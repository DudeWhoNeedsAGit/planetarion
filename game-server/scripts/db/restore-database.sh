#!/bin/bash
# Database restore script with hash validation for Planetarion QNAP deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Extract hash from backup file
extract_backup_hash() {
    local backup_file="$1"
    grep "^-- GAME_STATE_HASH:" "$backup_file" | cut -d: -f2 | tr -d ' ' || echo "unavailable"
}

# Calculate current game state hash
calculate_current_hash() {
    docker exec planetarion-db psql -U planetarion_user -d planetarion -t -c "
SELECT MD5(STRING_AGG(
    CONCAT(
        'P', p.id, '|',
        p.metal_mine, '|', p.crystal_mine, '|', p.deuterium_synthesizer, '|',
        p.solar_plant, '|', p.fusion_reactor, '|',
        COALESCE(SUM(f.small_cargo), 0), '|', COALESCE(SUM(f.large_cargo), 0), '|',
        COALESCE(SUM(f.light_fighter), 0), '|', COALESCE(SUM(f.heavy_fighter), 0), '|',
        COALESCE(SUM(f.cruiser), 0), '|', COALESCE(SUM(f.battleship), 0), '|',
        COALESCE(SUM(f.colony_ship), 0)
    ), ''
    ORDER BY p.id
)) as game_state_hash
FROM planets p
LEFT JOIN fleets f ON f.user_id = p.user_id
WHERE p.user_id IS NOT NULL
GROUP BY p.id, p.user_id, p.metal_mine, p.crystal_mine, p.deuterium_synthesizer,
         p.solar_plant, p.fusion_reactor
ORDER BY p.id;" 2>/dev/null | tr -d ' '
}

# Generate JSON debug output for validation failure
generate_debug_json() {
    local backup_file="$1"
    local expected_hash="$2"
    local actual_hash="$3"

    # Extract configurations from current database
    local debug_data=$(docker exec planetarion-db psql -U planetarion_user -d planetarion -t -c "
SELECT json_build_object(
    'backup_file', '$backup_file',
    'expected_hash', '$expected_hash',
    'actual_hash', '$actual_hash',
    'configurations', json_agg(
        json_build_object(
            'planet_id', p.id,
            'coordinates', concat(p.x, ':', p.y, ':', p.z),
            'buildings', json_build_object(
                'metal_mine', p.metal_mine,
                'crystal_mine', p.crystal_mine,
                'deuterium_synthesizer', p.deuterium_synthesizer,
                'solar_plant', p.solar_plant,
                'fusion_reactor', p.fusion_reactor
            ),
            'ships', json_build_object(
                'small_cargo', COALESCE(SUM(f.small_cargo), 0),
                'large_cargo', COALESCE(SUM(f.large_cargo), 0),
                'light_fighter', COALESCE(SUM(f.light_fighter), 0),
                'heavy_fighter', COALESCE(SUM(f.heavy_fighter), 0),
                'cruiser', COALESCE(SUM(f.cruiser), 0),
                'battleship', COALESCE(SUM(f.battleship), 0),
                'colony_ship', COALESCE(SUM(f.colony_ship), 0)
            )
        )
    ),
    'summary', json_build_object(
        'total_planets', COUNT(DISTINCT p.id),
        'total_buildings', SUM(p.metal_mine + p.crystal_mine + p.deuterium_synthesizer + p.solar_plant + p.fusion_reactor),
        'total_ships', SUM(COALESCE(f.small_cargo, 0) + COALESCE(f.large_cargo, 0) + COALESCE(f.light_fighter, 0) +
                          COALESCE(f.heavy_fighter, 0) + COALESCE(f.cruiser, 0) + COALESCE(f.battleship, 0) + COALESCE(f.colony_ship, 0))
    )
)
FROM planets p
LEFT JOIN fleets f ON f.user_id = p.user_id
WHERE p.user_id IS NOT NULL
GROUP BY p.id, p.x, p.y, p.z, p.metal_mine, p.crystal_mine, p.deuterium_synthesizer, p.solar_plant, p.fusion_reactor;" 2>/dev/null)

    echo "$debug_data" | jq . 2>/dev/null || echo "$debug_data"
}

# Main restore function
restore_database() {
    local backup_file="$1"
    local log_file="/share/CACHEDEV1_DATA/planetarion/logs/restore.log"

    log_info "Starting database restore from: $(basename "$backup_file")"

    # Extract expected hash from backup
    local expected_hash=$(extract_backup_hash "$backup_file")
    log_info "Expected game state hash: $expected_hash"

    # Stop application containers (keep database running)
    log_info "Stopping application containers..."
    docker-compose -f docker-compose.qnap.yml stop backend frontend

    # Drop and recreate database
    log_info "Recreating database..."
    docker exec planetarion-db psql -U planetarion_user -d postgres -c "DROP DATABASE IF EXISTS planetarion;" 2>>"$log_file"
    docker exec planetarion-db psql -U planetarion_user -d postgres -c "CREATE DATABASE planetarion;" 2>>"$log_file"

    # Restore from backup
    log_info "Restoring database from backup..."
    docker exec -i planetarion-db psql -U planetarion_user planetarion < "$backup_file" 2>>"$log_file"

    # Calculate actual hash after restore
    local actual_hash=$(calculate_current_hash)
    log_info "Actual game state hash: $actual_hash"

    # Validate hashes
    if [ "$expected_hash" = "$actual_hash" ] && [ "$expected_hash" != "unavailable" ]; then
        log_success "✅ Hash validation successful!"
        return 0
    else
        log_error "❌ Hash validation failed!"
        log_error "Expected: $expected_hash"
        log_error "Actual: $actual_hash"

        # Generate debug JSON
        log_info "Generating debug information..."
        local debug_json=$(generate_debug_json "$backup_file" "$expected_hash" "$actual_hash")
        echo "$debug_json" > "/share/CACHEDEV1_DATA/planetarion/logs/restore_debug_$(date +%Y%m%d_%H%M%S).json"

        log_error "Debug information saved to restore_debug_*.json"
        return 1
    fi
}

# Main execution
main() {
    if [ $# -ne 1 ]; then
        log_error "Usage: $0 <backup_file.sql>"
        exit 1
    fi

    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi

    # Check if database container is running
    if ! docker ps --format "table {{.Names}}" | grep -q "^planetarion-db$"; then
        log_error "Database container 'planetarion-db' is not running"
        exit 1
    fi

    if restore_database "$backup_file"; then
        log_success "Database restore completed successfully!"
        exit 0
    else
        log_error "Database restore failed - validation error"
        exit 1
    fi
}

# Run main function
main "$@"
