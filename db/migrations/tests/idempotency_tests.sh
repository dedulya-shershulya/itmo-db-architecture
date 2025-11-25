#!/bin/bash
set -e

DB_HOST="$TEST_DB_HOST"
DB_PORT="$TEST_DB_PORT"
DB_NAME="$TEST_DB_NAME"
DB_USER="$TEST_DB_USER"
DB_PASSWORD="$TEST_DB_PASSWORD"

MIGRATIONS_DIR="/migrations"
UP_DIR="$MIGRATIONS_DIR/up"
DOWN_DIR="$MIGRATIONS_DIR/down"

export PGPASSWORD="$DB_PASSWORD"

SNAPSHOT_DIR=$(mktemp -d)
trap 'rm -rf "$SNAPSHOT_DIR"' EXIT

required_vars=("DB_HOST" "DB_PORT" "DB_USER" "PGPASSWORD" "DB_NAME")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "🚨 ERROR: Required variable $var is not set"
        exit 1
    fi
done

apply_migration() {
    local file="$1"
    echo "  ⚡ Applying: $(basename "$file")"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -f "$file" > /dev/null
}

take_schema_snapshot() {
    local snapshot_file="$1"
    echo "  📸 Creating schema snapshot: $snapshot_file"
    
    pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        --schema-only > "$snapshot_file"
}

compare_schemas() {
    local snapshot1="$1"
    local snapshot2="$2"
    
    sed -e 's/^--.*//' -e '/^$/d' "$snapshot1" | sort > "${snapshot1}.normalized"
    sed -e 's/^--.*//' -e '/^$/d' "$snapshot2" | sort > "${snapshot2}.normalized"
    
    if ! diff -u "${snapshot1}.normalized" "${snapshot2}.normalized"; then
        echo "  🔍 Schema mismatch detected!"
        return 1
    fi

    return 0
}

echo "🔄 Recreating database $DB_NAME..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<-EOSQL
    DROP DATABASE IF EXISTS "$DB_NAME";
    CREATE DATABASE "$DB_NAME";
EOSQL

migrations=($(ls "$UP_DIR" | sort -V))
migration_num=0
total_migrations="${#migrations[@]}"

echo "🔎 Found $total_migrations migrations to test"
echo "🚀 Starting idempotency tests..." 
echo "========================================"

applied_migrations=()
for ((i=0; i<total_migrations; i++)); do
    migration="${migrations[$i]}"
    migration_num=$((i+1))
    
    echo ""
    echo "🧪 TESTING MIGRATION #$migration_num/$total_migrations: $migration"
    echo "----------------------------------------"
    
    up_file="${UP_DIR}/${migration}"
    down_migration="${migration/_up.sql/_down.sql}"
    down_file="${DOWN_DIR}/${down_migration}"
    
    if [ ! -f "$down_file" ]; then
        echo "🚨 ERROR: Down file not found: $down_file"
        exit 1
    fi

    echo "  [1/5] Applying migration..."
    apply_migration "$up_file"
    applied_migrations+=("$migration")
    
    echo "  [2/5] Creating first snapshot..."
    take_schema_snapshot "${SNAPSHOT_DIR}/snapshot1.sql"
    
    echo "  [3/5] Rolling back migration..."
    apply_migration "$down_file"
    
    echo "  [4/5] Re-applying migration..."
    apply_migration "$up_file"
    
    echo "  [5/5] Creating second snapshot..."
    take_schema_snapshot "${SNAPSHOT_DIR}/snapshot2.sql"
    
    echo "🔍 Comparing schemas..."
    if compare_schemas "${SNAPSHOT_DIR}/snapshot1.sql" "${SNAPSHOT_DIR}/snapshot2.sql"; then
        echo "✅ SUCCESS: Migration is idempotent"
    else
        echo "❌ FAILURE: Migration is NOT idempotent"
        exit 1
    fi
    
    echo "----------------------------------------"
    echo "Progress: $migration_num/$total_migrations migrations tested"
done

echo ""
echo "========================================"
echo "🎉 All migrations passed idempotency test!"
echo "========================================"
exit 0