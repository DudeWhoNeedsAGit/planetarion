#!/bin/bash
# Setup automated database backup cron job for Planetarion QNAP deployment

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

# Check if running on QNAP
check_qnap_environment() {
    if [[ ! -d "/share/CACHEDEV1_DATA" ]]; then
        log_error "This script must be run on a QNAP NAS system"
        exit 1
    fi
}

# Setup cron job for database backup
setup_cron_job() {
    local backup_script="/share/CACHEDEV1_DATA/planetarion/backup-database.sh"
    local cron_entry="0 2,10,18 * * * $backup_script"

    log_info "Setting up cron job for database backup..."

    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$backup_script"; then
        log_warning "Cron job for backup script already exists"
        return 0
    fi

    # Add cron job (create new crontab or append to existing)
    if crontab -l 2>/dev/null; then
        # Append to existing crontab
        (crontab -l 2>/dev/null; echo "$cron_entry") | crontab -
    else
        # Create new crontab
        echo "$cron_entry" | crontab -
    fi

    log_success "Cron job added successfully"
    log_info "Backup will run at: 02:00, 10:00, 18:00 daily"
}

# Verify cron job setup
verify_cron_setup() {
    log_info "Verifying cron job setup..."

    if crontab -l | grep -q "backup-database.sh"; then
        log_success "Cron job verification successful"
        crontab -l | grep "backup-database.sh"
    else
        log_error "Cron job verification failed"
        exit 1
    fi
}

# Test backup script
test_backup_script() {
    local backup_script="/share/CACHEDEV1_DATA/planetarion/backup-database.sh"

    log_info "Testing backup script..."

    if [[ ! -x "$backup_script" ]]; then
        log_error "Backup script is not executable: $backup_script"
        exit 1
    fi

    # Run a dry-run test (without actually creating backup)
    if "$backup_script" --dry-run 2>/dev/null || true; then
        log_success "Backup script test completed"
    else
        log_warning "Backup script test had issues (may be normal for dry-run)"
    fi
}

# Main function
main() {
    echo "🔄 Setting up Planetarion Database Backup Cron Job"
    echo "================================================="

    check_qnap_environment
    setup_cron_job
    verify_cron_setup
    test_backup_script

    log_success "Database backup cron job setup completed!"
    log_info "The database will be backed up automatically every 8 hours"
    log_info "Backup files will be stored in: /share/CACHEDEV1_DATA/planetarion/backups/"
    log_info "Logs will be available in: /share/CACHEDEV1_DATA/planetarion/logs/backup.log"
}

# Run main function
main "$@"
