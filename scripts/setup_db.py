import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
import subprocess

DB_NAME = "db_database"
DB_USER = "postgres"
DB_PASSWORD = "postgres" 
DB_HOST = "localhost"
DB_PORT = "5432"

# Caminho do arquivo de backup
SCHEMA_PATH = "../database_backup/dump-db.sql"

# Caminho completo do executável do Postgres no Windows (versão 16)
PSQL_PATH = r"C:\Program Files\PostgreSQL\16\bin\psql.exe"

try:
    print("Criando banco...")

    # 1. Conecta no Postgres geral só para criar o banco
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        database="postgres"
    )

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Verifica se já existe
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"Banco '{DB_NAME}' criado.")
    else:
        print(f"Banco '{DB_NAME}' já existe.")

    # Fecha essa conexão inicial
    cursor.close()
    conn.close()

    print("Importando estrutura e dados...")

    # 2. Usa o psql nativo para importar o arquivo de forma bruta
    os.environ["PGPASSWORD"] = DB_PASSWORD
    
    # Se por acaso o caminho exato não for esse, o script tenta só "psql" como plano B
    if not os.path.exists(PSQL_PATH):
        PSQL_PATH = "psql"

    # Monta o comando de terminal colocando aspas em volta dos caminhos para evitar problemas com espaços
    comando = f'"{PSQL_PATH}" -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -d {DB_NAME} -f "{SCHEMA_PATH}"'
    
    # Executa o comando
    subprocess.run(comando, shell=True, check=True)
    print("\n✅ Banco pronto e populado com sucesso!")

except subprocess.CalledProcessError:
    print("\n❌ Falha ao importar o arquivo SQL. Verifique se o caminho do PostgreSQL está correto.")
except Exception as e:
    print("\n❌ Erro geral:", e)