#!/bin/bash

postgres_db="$DB_NAME"
postgres_user="$POSTGRES_USER"
analytic_role="analytic"
analyst_users="$ANALYST_NAMES"  # Пример: analyst1,analyst2
password_suffix="$PASSWORD_SUFFIX"

export PGPASSWORD="${POSTGRES_PASSWORD}"

if [[ -z "$postgres_db" || -z "$postgres_user" || -z "$analyst_users" || -z "$password_suffix" ]]; then
  echo "Ошибка: Не все переменные окружения установлены."
  echo "Необходимые переменные: DB_NAME, POSTGRES_USER, ANALYST_NAMES, PASSWORD_SUFFIX"
  exit 1
fi

echo "[LOG] Используется:"
echo "PostgreSQL пользователь: $postgres_user"
echo "База данных: $postgres_db"
echo "Аналитическая роль: $analytic_role"
echo "Аналитики: $analyst_users"

echo "[LOG] Проверка наличия роли $analytic_role"
role_exists=$(psql -U "$postgres_user" -d "$postgres_db" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$analytic_role'")
if [[ -z "$role_exists" ]]; then
  echo "[LOG] Создание роли $analytic_role"
  psql -U "$postgres_user" -d "$postgres_db" -c "CREATE ROLE \"$analytic_role\" NOINHERIT NOLOGIN;" || { echo "Ошибка создания роли $analytic_role"; exit 1; }
else
  echo "[LOG] Роль $analytic_role уже существует"
fi

echo "[LOG] Назначение привилегий для роли $analytic_role"
psql -U "$postgres_user" -d "$postgres_db" <<-EOSQL
    GRANT USAGE ON SCHEMA public TO "$analytic_role";
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO "$analytic_role";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "$analytic_role";
EOSQL
if [[ $? -ne 0 ]]; then
  echo "[ERROR] Не удалось назначить привилегии для роли $analytic_role"
  exit 1
fi

IFS=',' read -ra analyst_array <<< "$analyst_users"

echo "[LOG] Создание пользователей: ${analyst_array[*]}"
for analyst in "${analyst_array[@]}"; do
  user_exists=$(psql -U "$postgres_user" -d "$postgres_db" -tAc "SELECT 1 FROM pg_roles WHERE rolname='$analyst'")
  if [[ ! -z "$user_exists" ]]; then
    echo "[LOG] Пользователь $analyst уже существует. Пропуск."
    continue
  fi

  password="${analyst}_${password_suffix}"
  echo "[LOG] Создание пользователя: $analyst"
  psql -U "$postgres_user" -d "$postgres_db" -c \
    "CREATE USER \"$analyst\" WITH PASSWORD '$password' IN ROLE \"$analytic_role\";" \
  || { echo "[ERROR] Не удалось создать пользователя $analyst"; exit 1; }
done

echo "[LOG] Все пользователи успешно созданы"