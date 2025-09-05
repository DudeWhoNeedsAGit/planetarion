# Planetarion Database Backup System

This document describes the automated PostgreSQL database backup system for Planetarion QNAP deployments.

## Overview

The backup system provides automated, scheduled backups of the production PostgreSQL database running in Docker containers on QNAP NAS. It maintains rotation of backup files and includes comprehensive error handling and logging.

## Features

- ✅ Automated backups every 8 hours (02:00, 10:00, 18:00)
- ✅ PostgreSQL `pg_dump` from within database container
- ✅ Automatic rotation (keeps last 3 backups)
- ✅ Comprehensive error handling and logging
- ✅ Container health checks before backup
- ✅ Backup verification and integrity checks
- ✅ Cron job scheduling on QNAP
- ✅ Integrated with deployment process

## File Structure

```
/share/CACHEDEV1_DATA/planetarion/
├── backups/                    # Backup files directory
│   ├── planetarion_backup_20231201_020000.sql
│   ├── planetarion_backup_20231201_100000.sql
│   └── planetarion_backup_20231201_180000.sql
├── logs/                       # Backup logs directory
│   └── backup.log             # Backup operation logs
├── backup-database.sh         # Main backup script
└── setup-backup-cron.sh       # Cron job setup script
```

## Backup Script Details

### `backup-database.sh`

**Location:** `/share/CACHEDEV1_DATA/planetarion/backup-database.sh`

**Functionality:**
- Checks if database container (`planetarion-db`) is running
- Creates timestamped backup files
- Performs backup rotation (keeps last 3 files)
- Logs all operations with timestamps
- Verifies backup file integrity

**Backup File Naming:** `planetarion_backup_YYYYMMDD_HHMMSS.sql`

### `setup-backup-cron.sh`

**Location:** `/share/CACHEDEV1_DATA/planetarion/setup-backup-cron.sh`

**Functionality:**
- Validates QNAP environment
- Sets up cron job for automated backups
- Verifies cron job installation
- Tests backup script functionality

## Cron Job Configuration

The system installs a cron job that runs the backup script every 8 hours:

```bash
0 2,10,18 * * * /share/CACHEDEV1_DATA/planetarion/backup-database.sh
```

**Schedule:**
- 02:00 (2:00 AM)
- 10:00 (10:00 AM)
- 18:00 (6:00 PM)

## Deployment Integration

The backup system is automatically integrated into the QNAP deployment process with **automatic restore functionality**:

### 🚀 **Smart Deployment with Restore**

The deployment script now includes intelligent restore logic:

1. **A-B Deployment Detection**: Checks for existing running containers
2. **Automatic Restore**: If backups exist, attempts restore from latest backup
3. **Fallback Chain**: If latest fails, tries previous backups automatically
4. **Safety First**: Aborts deployment if all restores fail (protects existing system)
5. **Backup Setup**: Installs automated backup system after successful deployment

### Deployment Steps

```bash
# Run the deployment script (includes automatic restore + backup setup)
./deploy-to-qnap.sh
```

### Restore-on-Deployment Flow

```
1. Check for existing containers (A-B scenario)
2. If existing deployment found:
   ├── Search for backup files in /share/CACHEDEV1_DATA/planetarion/backups/
   ├── Try latest backup first
   ├── If fails → try previous backup
   ├── If fails → try oldest backup
   ├── If all fail → ABORT DEPLOYMENT (safe!)
3. If restore succeeds → proceed with new deployment
4. Setup automated backup system
5. Switch to new containers
```

### Safety Features

- ✅ **A-B Protection**: Never disrupts running services
- ✅ **Automatic Fallback**: Tries multiple backups automatically
- ✅ **Hash Validation**: Ensures restore integrity
- ✅ **JSON Debug Output**: Detailed failure diagnostics
- ✅ **Graceful Abortion**: Stops deployment if restore fails

### Restore Validation

Each restore attempt includes:
- **Hash Verification**: Compares expected vs actual game state
- **JSON Diagnostics**: Detailed configuration output on failures
- **Comprehensive Logging**: Full restore operation logs

## Manual Operations

### Running Backup Manually

```bash
# SSH to QNAP
ssh user@qnap-ip

# Navigate to project directory
cd /share/CACHEDEV1_DATA/planetarion

# Run backup manually
./backup-database.sh
```

### Checking Backup Status

```bash
# View backup logs
tail -f /share/CACHEDEV1_DATA/planetarion/logs/backup.log

# List backup files
ls -la /share/CACHEDEV1_DATA/planetarion/backups/

# Check cron job status
crontab -l | grep backup
```

### Restoring from Backup

```bash
# Copy backup file to a safe location
cp /share/CACHEDEV1_DATA/planetarion/backups/planetarion_backup_20231201_020000.sql /tmp/

# Restore database (adjust container name and credentials as needed)
docker exec -i planetarion-db psql -U planetarion_user planetarion < /tmp/planetarion_backup_20231201_020000.sql
```

## Monitoring and Troubleshooting

### Log Files

**Backup Log:** `/share/CACHEDEV1_DATA/planetarion/logs/backup.log`

Contains:
- Backup start/end timestamps
- Success/failure status
- File sizes and verification results
- Error messages and troubleshooting information

### Common Issues

#### 1. Database Container Not Running

**Error:** `ERROR - Database container 'planetarion-db' is not running`

**Solution:**
```bash
# Check container status
docker ps | grep planetarion-db

# Start services if needed
cd /share/CACHEDEV1_DATA/planetarion
docker-compose -f docker-compose.qnap.yml up -d
```

#### 2. Permission Issues

**Error:** `Permission denied` when creating backup files

**Solution:**
```bash
# Ensure proper permissions on backup directory
chmod 755 /share/CACHEDEV1_DATA/planetarion/backups
chmod 755 /share/CACHEDEV1_DATA/planetarion/logs
```

#### 3. Cron Job Not Running

**Check cron service:**
```bash
# Check if cron is running
ps aux | grep cron

# Check cron logs
grep CRON /var/log/syslog
```

**Verify cron job:**
```bash
# List cron jobs
crontab -l

# Test cron job manually
sudo -u your-user /share/CACHEDEV1_DATA/planetarion/backup-database.sh
```

### Backup Verification

The system automatically verifies backups by:
1. Checking file existence after creation
2. Ensuring file has non-zero size
3. Logging file size information

**Manual verification:**
```bash
# Check backup file size
ls -lh /share/CACHEDEV1_DATA/planetarion/backups/

# Verify backup file integrity
head -n 5 /share/CACHEDEV1_DATA/planetarion/backups/planetarion_backup_*.sql
```

## Configuration

### Backup Retention

Currently configured to keep the **last 3 backups**. To modify:

```bash
# Edit backup-database.sh
# Change the tail -n +4 to adjust retention
# Example: tail -n +8 to keep last 7 backups
```

### Backup Schedule

To modify the backup schedule, update the cron job:

```bash
# Edit crontab
crontab -e

# Change the schedule (current: 0 2,10,18 * * *)
# Example: every 6 hours - 0 */6 * * *
```

## Security Considerations

- Backup files contain sensitive database information
- Store backups in secure QNAP shared folders
- Consider encrypting backup files for additional security
- Regularly audit backup logs for unauthorized access

## Performance Impact

- Backups run during low-usage hours by default
- `pg_dump` creates a consistent snapshot
- Minimal impact on running database operations
- Backup duration depends on database size

## Maintenance

### Regular Tasks

- Monitor backup logs weekly
- Verify backup file integrity monthly
- Test restore procedure quarterly
- Review disk space usage for backup storage

### Log Rotation

Backup logs can grow over time. Consider log rotation:

```bash
# Example: Rotate logs monthly
# Add to cron: 0 0 1 * * logrotate /etc/logrotate.d/backup-logs
```

## Support

For issues with the backup system:

1. Check backup logs: `/share/CACHEDEV1_DATA/planetarion/logs/backup.log`
2. Verify cron job: `crontab -l`
3. Test manual backup execution
4. Check QNAP system logs for cron-related issues

## Version History

- **v1.0** - Initial automated backup system implementation
- Integrated with QNAP deployment process
- 8-hour backup intervals with 3-file rotation
- Comprehensive error handling and logging
