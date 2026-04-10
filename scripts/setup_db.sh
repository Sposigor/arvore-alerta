#!/bin/bash

DB_NAME="db_database"
DB_USER="postgres"

echo "Criando banco..."

sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
EOF

echo "Importando estrutura..."

psql -U $DB_USER -d $DB_NAME -f database_backup/schema.sql

echo "Banco pronto."