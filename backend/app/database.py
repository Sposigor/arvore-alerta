import sqlite3

from app import config


def init_db():
    conn = sqlite3.connect(config.DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude    REAL    NOT NULL,
            longitude   REAL    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'pendente',
            origem      TEXT    NOT NULL DEFAULT 'satellite',
            confianca   REAL    DEFAULT 0.0,
            ndvi_atual  REAL,
            ndvi_ref    REAL,
            ndvi_delta  REAL,
            descricao   TEXT,
            criado_em   TEXT    DEFAULT CURRENT_TIMESTAMP,
            cidade      TEXT,
            bairro      TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reportes_usuario (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude      REAL    NOT NULL,
            longitude     REAL    NOT NULL,
            descricao     TEXT,
            confirmacoes  INTEGER DEFAULT 1,
            status        TEXT    DEFAULT 'ativo',
            criado_em     TEXT    DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TEXT    DEFAULT CURRENT_TIMESTAMP,
            cidade        TEXT,
            bairro        TEXT
        )
    """)

    for col_def in [
        "ALTER TABLE ocorrencias ADD COLUMN radar_vh_delta REAL",
        "ALTER TABLE ocorrencias ADD COLUMN alertas_dc TEXT",
        "ALTER TABLE ocorrencias ADD COLUMN modo_ref TEXT DEFAULT 'ano_anterior'",
        "ALTER TABLE ocorrencias ADD COLUMN periodo_atual TEXT",
        "ALTER TABLE ocorrencias ADD COLUMN periodo_ref TEXT",
    ]:
        try:
            c.execute(col_def)
        except sqlite3.OperationalError:
            pass

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
