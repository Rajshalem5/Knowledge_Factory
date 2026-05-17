#!/bin/bash
# Knowledge Factory - Database Backup Script
# Backup SQLite DB to /mnt/hermes-shared/backups/knowledge-factory/
# Keeps last 30 backups, deletes older ones
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="/mnt/hermes-shared/backups/knowledge-factory"
RETENTION_DAYS=30
DB_PATH="$PROJECT_DIR/backend/knowledge_factory.db"
LOG_FILE="$PROJECT_DIR/logs/backup.log"

mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

timestamp=$(date +%Y%m%d_%H%M%S)

if [ -f "$DB_PATH" ]; then
    backup_file="$BACKUP_DIR/kf_$timestamp.db"
    sqlite3 "$DB_PATH" ".backup '$backup_file'"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: SQLite backup -> $backup_file" >> "$LOG_FILE"
    echo "Backup created: $backup_file"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: No SQLite DB found at $DB_PATH" >> "$LOG_FILE"
    echo "No SQLite database found at $DB_PATH"
    exit 0
fi

# Clean backups older than RETENTION_DAYS
find "$BACKUP_DIR" -name "kf_*.db" -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
count=$(find "$BACKUP_DIR" -name "kf_*.db" | wc -l)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] CLEANUP: $count backups retained (older than $RETENTION_DAYS days removed)" >> "$LOG_FILE"
echo "Done. $count backup(s) retained in $BACKUP_DIR"