FROM postgres:latest

RUN apt-get update && \
    apt-get install -y cron && \
    rm -rf /var/lib/apt/lists/*

COPY ./scripts/backup.sh /backup.sh
RUN chmod +x /backup.sh

CMD ["sh", "-c", \
"echo \"${BACKUP_INTERVAL_CRON} root . /etc/profile; \
export PG_HOST=${POSTGRES_HOST} \
PG_USER=${POSTGRES_USER} \
PG_PORT=${POSTGRES_PORT} \
PGPASSWORD=${POSTGRES_PASSWORD} \
PG_DATABASE=${DB_NAME} \ 
RETENTION=${BACKUP_RETENTION_COUNT}; \
/backup.sh >> /var/log/cron.log 2>&1\" > /etc/cron.d/backup-cron && \
     chmod 0644 /etc/cron.d/backup-cron && \
     cron -f"]