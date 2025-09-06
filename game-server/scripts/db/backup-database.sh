#!/bin/bash
# Automated PostgreSQL backup for Planetarion QNAP deployment with hash validation

BACKUP_DIR="/share/CACHEDEV1_DATA/planetarion/backups"
LOG_DIR="/share/CACHEDEV1_DATA/planetarion/logs"
LOG_FILE="$LOG_DIR/backup.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TEMP_BACKUP_FILE="$BACKUP_DIR/temp_backup_$TIMESTAMP.sql"

# Ensure directories exist
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Log backup start
echo "$(date): Starting database backup with hash validation" >> "$LOG_FILE"

# Check if database container is running
if ! docker ps --format "table {{.Names}}" | grep -q "^planetarion-db$"; then
    echo "$(date): ERROR - Database container 'planetarion-db' is not running" >> "$LOG_FILE"
    exit 1
fi

# Calculate game state hash before backup
echo "$(date): Calculating game state hash..." >> "$LOG_FILE"
GAME_STATE_HASH=$(docker exec planetarion-db psql -U planetarion_user -d planetarion -t -c "
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
ORDER BY p.id;" 2>/dev/null | tr -d ' ')

if [ -z "$GAME_STATE_HASH" ] || [ "$GAME_STATE_HASH" = "null" ]; then
    echo "$(date): WARNING - Could not calculate game state hash, proceeding without validation" >> "$LOG_FILE"
    GAME_STATE_HASH="unavailable"
fi

echo "$(date): Game state hash calculated: $GAME_STATE_HASH" >> "$LOG_FILE"

# Create backup from Docker container
if docker exec planetarion-db pg_dump -U planetarion_user planetarion > "$TEMP_BACKUP_FILE" 2>> "$LOG_FILE"; then
    echo "$(date): Backup dump successful: $TEMP_BACKUP_FILE" >> "$LOG_FILE"

    # Add hash comment to backup file
    echo "-- GAME_STATE_HASH: $GAME_STATE_HASH" >> "$TEMP_BACKUP_FILE"
    echo "-- BACKUP_TIMESTAMP: $TIMESTAMP" >> "$TEMP_BACKUP_FILE"

    # Create final backup filename with hash
    BACKUP_FILE="$BACKUP_DIR/planetarion_backup_${TIMESTAMP}_${GAME_STATE_HASH}.sql"
    mv "$TEMP_BACKUP_FILE" "$BACKUP_FILE"

    echo "$(date): Backup successful: $BACKUP_FILE" >> "$LOG_FILE"

    # Rotate backups (keep last 3)
    cd "$BACKUP_DIR"
    ls -t planetarion_backup_*.sql | tail -n +4 | while read old_backup; do
        rm -f "$old_backup"
        echo "$(date): Removed old backup: $old_backup" >> "$LOG_FILE"
    done

    # Verify backup file exists and has content
    if [ -s "$BACKUP_FILE" ]; then
        BACKUP_SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null || echo "unknown")
        echo "$(date): Backup verification successful - Size: $BACKUP_SIZE bytes" >> "$LOG_FILE"
        echo "$(date): Game state hash stored: $GAME_STATE_HASH" >> "$LOG_FILE"
    else
        echo "$(date): ERROR - Backup file is empty" >> "$LOG_FILE"
        exit 1
    fi
else
    echo "$(date): ERROR - Backup failed" >> "$LOG_FILE"
    rm -f "$TEMP_BACKUP_FILE"
    exit 1
fi

echo "$(date): Backup process completed successfully" >> "$LOG_FILE"
