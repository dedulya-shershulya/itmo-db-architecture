#!/bin/bash

BACKUP_DIR="/backups"
BACKUP_FILE="backup-$(date +%Y-%m-%d-%H-%M-%S).sql.gz"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚡️ Starting backup process..."
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Host: $PG_HOST, Database: $PG_DATABASE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup file: $BACKUP_DIR/$BACKUP_FILE"

pg_dump -h "$PG_HOST" -p "$PG_PORT" -U "$PG_USER" -d "$PG_DATABASE" | gzip > "$BACKUP_DIR/$BACKUP_FILE"
unset PGPASSWORD

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup created successfully!"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup failed!" >&2
    exit 1
fi

OLD_BACKUPS=$(ls -t "$BACKUP_DIR"/backup-*.sql.gz | tail -n +$(($RETENTION + 1)))

if [ -n "$OLD_BACKUPS" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🗑 Deleting old backups:"
    echo "$OLD_BACKUPS"
    rm -f $OLD_BACKUPS
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🏁 Backup process completed"