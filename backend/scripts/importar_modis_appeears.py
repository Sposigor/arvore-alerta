#!/usr/bin/env python3
"""
Lê o CSV de resultado do AppEEARS (MOD13Q1.061), filtra qualidade,
e grava numa tabela SQLite local `modis_ndvi`.

Uso:
    python importar_modis_appeears.py /caminho/para/results.csv [db.sqlite]

Filtro padrão: pixel_reliability ∈ {0, 1} (Good + Marginal).
NDVI já vem em escala 0..1 (AppEEARS aplica scale factor automaticamente).
"""
import csv
import os
import sqlite3
import sys

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "/tmp/appeears/tcc-univesp-250426-MOD13Q1-061-results.csv"
DB_PATH = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(__file__), "..", "modis_local.db")
DB_PATH = os.path.abspath(DB_PATH)

NDVI_COL = "MOD13Q1_061__250m_16_days_NDVI"
REL_COL = "MOD13Q1_061__250m_16_days_pixel_reliability"
DOY_COL = "MOD13Q1_061__250m_16_days_composite_day_of_the_year"


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS modis_ndvi (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            loc_id      TEXT    NOT NULL,
            cidade      TEXT,
            latitude    REAL    NOT NULL,
            longitude   REAL    NOT NULL,
            data        TEXT    NOT NULL,
            ndvi        REAL    NOT NULL,
            reliability INTEGER,
            doy         INTEGER,
            UNIQUE (loc_id, data)
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_modis_loc_data ON modis_ndvi (loc_id, data)")

    total = ok = filtrados = 0
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            try:
                rel = int(float(row[REL_COL]))
            except (ValueError, KeyError):
                rel = -1
            if rel not in (0, 1):
                filtrados += 1
                continue
            try:
                ndvi = float(row[NDVI_COL])
            except ValueError:
                continue
            if ndvi < -0.2 or ndvi > 1.0:
                continue
            try:
                doy = int(float(row[DOY_COL]))
            except (ValueError, KeyError):
                doy = None
            c.execute("""
                INSERT OR IGNORE INTO modis_ndvi
                  (loc_id, cidade, latitude, longitude, data, ndvi, reliability, doy)
                VALUES (?,?,?,?,?,?,?,?)
            """, (
                row["ID"], row["Category"].strip(),
                float(row["Latitude"]), float(row["Longitude"]),
                row["Date"], ndvi, rel, doy,
            ))
            ok += 1

    conn.commit()
    c.execute("SELECT COUNT(*), COUNT(DISTINCT loc_id), MIN(data), MAX(data) FROM modis_ndvi")
    n, n_loc, dmin, dmax = c.fetchone()
    c.execute("SELECT cidade, COUNT(*) FROM modis_ndvi GROUP BY cidade ORDER BY 2 DESC LIMIT 5")
    top = c.fetchall()
    conn.close()

    print(f"DB: {DB_PATH}")
    print(f"Total CSV: {total}  |  Importados: {ok}  |  Filtrados (reliability>1): {filtrados}")
    print(f"Em DB: {n} pontos × {n_loc} locais  |  Período: {dmin} → {dmax}")
    print("Top 5 cidades:")
    for cid, cnt in top:
        print(f"  {cid:<25} {cnt}")


if __name__ == "__main__":
    main()
