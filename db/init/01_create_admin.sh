#!/bin/bash

postgres_db="$POSTGRES_DB"
postgres_user="$POSTGRES_USER"
db="$DB_NAME"
creator_user="$DB_ADMIN_USER"
creator_password="$DB_ADMIN_PASSWORD"
db_host="$PGHOST"
db_port="$PGPORT"

export PGPASSWORD="$POSTGRES_PASSWORD"

MAX_RETRIES=30
for i in $(seq 1 $MAX_RETRIES); do
  pg_isready -h "$db_host" -p "$db_port" -U "$postgres_user" && break || sleep 2
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "PostgreSQL не доступен после $MAX_RETRIES попыток. Выход."
    exit 1
  fi
done

echo "[LOG]: Ожидание доступности мастера..."
for i in $(seq 1 $MAX_RETRIES); do
  if psql -h "$db_host" -p "$db_port" -U "$postgres_user" -tAc "SELECT pg_is_in_recovery()" | grep -q f; then
    echo "Мастер доступен"
    break
  fi
  sleep 2
  if [ "$i" -eq "$MAX_RETRIES" ]; then
    echo "Мастер PostgreSQL не доступен после $MAX_RETRIES попыток. Выход."
    exit 1
  fi
done

echo "Используется:"
echo "PostgreSQL хост: $db_host"
echo "PostgreSQL порт: $db_port"
echo "PostgreSQL пользователь: $postgres_user"
echo "База данных: $db"
echo "Админ пользователь: $creator_user"

echo "[LOG]: Проверка наличия пользователя $creator_user"
if ! psql -h "$db_host" -p "$db_port" -U "$postgres_user" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$creator_user'" | grep -q 1; then
  echo "[LOG]: Создание пользователя $creator_user"
  psql -h "$db_host" -p "$db_port" -U "$postgres_user" -c "CREATE USER \"$creator_user\" WITH CREATEDB PASSWORD '$creator_password';" || { echo "Ошибка создания пользователя"; exit 1; }
else
  echo "[LOG]: Пользователь $creator_user уже существует"
fi

echo "[LOG]: Проверка наличия БД $db"
if ! psql -h "$db_host" -p "$db_port" -U "$postgres_user" -tAc "SELECT 1 FROM pg_database WHERE datname='$db'" | grep -q 1; then
  echo "[LOG]: Создание БД $db"
  psql -h "$db_host" -p "$db_port" -U "$postgres_user" -c "CREATE DATABASE \"$db\" WITH OWNER \"$creator_user\";" || { echo "Ошибка создания БД"; exit 1; }
else
  echo "[LOG]: БД $db уже существует"
fi

echo "[LOG]: Назначение привилегий в БД $db"
psql -h "$db_host" -p "$db_port" -U "$postgres_user" -d "$db" <<-EOSQL
    GRANT ALL ON SCHEMA public TO "$creator_user";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "$creator_user";
EOSQL