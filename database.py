import psycopg2
from psycopg2.extras import RealDictCursor, execute_values  # Corrigido para incluir execute_values
import io
import time

class postgresDatabase():
    def __init__(self, user='postgres', password='postgres', host='localhost', dbname='db_database', port='5432'):
        self.lastError = None
        self.connectionString = f"user={user} password={password} host={host} dbname={dbname} port={port}"

    def readRaw(self, sql, params=None, realdict=False):
        try:
            start_time = time.time()

            conn = psycopg2.connect(self.connectionString)

            if realdict:
                cur = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cur = conn.cursor()

            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)

            if realdict:
                data = cur.fetchall()
            else:
                data = [list(row) for row in cur.fetchall()]

            cur.close()
            conn.close()

            end_time = time.time()
            print(f"Tempo para executar a consulta no Postgres: {end_time - start_time:.2f} segundos")

            return data

        except Exception as e:
            self.lastError = e
            print("Valor de e: ", e)
            return []

    def writeRaw(self, sql, params=None):
        try:
            start_time = time.time()  # Temporizador de início
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()
            if params:
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            conn.commit()
            cur.close()
            conn.close()
            end_time = time.time()  # Temporizador de fim
            print(f"Tempo para executar a consulta no Postgres: {end_time - start_time:.2f} segundos")
            return True
        except Exception as e:
            print('Erro:', e)
            self.lastError = e
            return False

    def bulkInsert(self, table, columns, data, custom_query=None):
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            if custom_query:
                # Se a consulta personalizada foi fornecida, usa essa consulta.
                execute_values(cur, custom_query, data)
                print("passei aqui no if")
            else:
                print("passei aqui no else")
                # Constrói uma consulta padrão com proteção contra conflitos.
                placeholders = ", ".join(["%s"] * len(columns))  # Cria uma string de placeholders.
                sql = f"""
                    INSERT INTO {table} ({', '.join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT (codigo, nome_cliente) DO UPDATE SET
                    {', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col not in ['codigo', 'nome_cliente']])};
                """
                execute_values(cur, sql, data)

            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print('Erro ao realizar bulk insert:', e)
            self.lastError = e
            return False


    def copyFrom(self, table, columns, data):
        try:
            conn = psycopg2.connect(self.connectionString)
            cur = conn.cursor()

            buffer = io.StringIO()
            for row in data:
                buffer.write('\t'.join(map(str, row)) + '\n')
            buffer.seek(0)

            cur.copy_from(buffer, table, sep='\t', columns=columns)
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print('Erro ao usar COPY FROM:', e)
            self.lastError = e
            return False


