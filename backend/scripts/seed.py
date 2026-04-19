#!/usr/bin/env python3
"""
Popula o banco com ocorrências de demonstração espalhadas pelo mundo.
Execute: python seed.py  (na pasta backend/)
"""
import sqlite3, random
from datetime import datetime, timedelta, timezone

DB_PATH = "arvore_alerta.db"

# (lat, lon, n_ocorrencias, cidade)
AREAS = [
    # São Paulo — alta densidade
    (-23.550, -46.633, 7, "São Paulo"),
    (-23.620, -46.520, 5, "São Paulo"),
    (-23.490, -46.840, 4, "São Paulo"),
    (-23.670, -46.700, 6, "São Paulo"),
    (-23.420, -46.580, 4, "São Paulo"),
    (-23.960, -46.340, 4, "Santos"),
    (-22.900, -47.060, 4, "Campinas"),
    (-23.180, -45.880, 3, "São José dos Campos"),
    (-23.500, -47.460, 3, "Sorocaba"),
    (-23.100, -46.550, 3, "Guarulhos"),
    (-23.680, -46.560, 3, "Santo André"),

    # Brasil — outras regiões
    (-22.900, -43.170, 5, "Rio de Janeiro"),
    (-3.100,  -60.020, 7, "Manaus"),           # Amazônia
    (-1.460,  -48.500, 5, "Belém"),
    (-12.970, -38.510, 3, "Salvador"),
    (-8.050,  -34.880, 3, "Recife"),
    (-3.720,  -38.540, 2, "Fortaleza"),
    (-15.780, -47.930, 2, "Brasília"),
    (-19.920, -43.940, 3, "Belo Horizonte"),
    (-30.030, -51.220, 3, "Porto Alegre"),
    (-25.430, -49.270, 3, "Curitiba"),
    (-21.170, -47.810, 2, "Ribeirão Preto"),
    (-22.330, -49.070, 2, "Bauru"),

    # América do Norte
    (37.770,  -122.420, 4, "San Francisco"),
    (25.770,   -80.190, 3, "Miami"),
    (41.880,   -87.630, 3, "Chicago"),
    (45.520,   -73.560, 2, "Montreal"),
    (19.430,   -99.130, 4, "Cidade do México"),
    (9.930,    -84.090, 4, "San José (Costa Rica)"),

    # América do Sul
    (-0.220,   -78.510, 5, "Quito"),            # Andes equatoriais
    (-12.050,  -77.040, 3, "Lima"),
    (-34.600,  -58.380, 2, "Buenos Aires"),
    (4.710,    -74.070, 4, "Bogotá"),

    # Europa
    (51.510,    -0.120, 3, "Londres"),
    (48.860,     2.350, 3, "Paris"),
    (52.520,    13.400, 2, "Berlim"),
    (40.410,    -3.700, 2, "Madrid"),
    (45.460,     9.190, 2, "Milão"),
    (59.330,    18.060, 2, "Estocolmo"),

    # Ásia
    (35.690,   139.690, 3, "Tóquio"),
    (1.350,    103.820, 4, "Singapura"),
    (-6.210,   106.850, 6, "Jacarta"),          # Indonesia
    (13.760,   100.500, 3, "Bangkok"),
    (22.280,   114.160, 2, "Hong Kong"),
    (28.610,    77.200, 3, "Nova Déli"),
    (14.600,   121.000, 4, "Manila"),

    # África
    (-1.290,    36.820, 4, "Nairóbi"),
    (6.370,      3.380, 3, "Lagos"),
    (-4.320,    15.320, 5, "Kinshasa"),         # Congo
    (3.860,     11.520, 4, "Yaoundé"),          # Camarões
    (-18.910,   47.540, 3, "Antananarivo"),     # Madagascar

    # Oceania
    (-33.870,  151.210, 3, "Sydney"),
    (-37.810,  144.960, 2, "Melbourne"),
    (-6.310,   143.950, 5, "Papua Nova Guiné"),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL, longitude REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            origem TEXT NOT NULL DEFAULT 'satellite',
            confianca REAL DEFAULT 0.0,
            ndvi_atual REAL, ndvi_ref REAL, ndvi_delta REAL,
            descricao TEXT, criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            cidade TEXT, bairro TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS reportes_usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL, longitude REAL NOT NULL,
            descricao TEXT, confirmacoes INTEGER DEFAULT 1,
            status TEXT DEFAULT 'ativo',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            cidade TEXT, bairro TEXT
        )
    """)

    now = datetime.now(timezone.utc)
    total = 0

    for lat, lon, n_oc, cidade in AREAS:
        for _ in range(n_oc):
            dlat = random.uniform(-0.08, 0.08)
            dlon = random.uniform(-0.08, 0.08)
            ndvi_ref   = round(random.uniform(0.50, 0.85), 3)
            ndvi_delta = round(random.uniform(0.12, 0.42), 3)
            ndvi_atual = round(max(0.0, ndvi_ref - ndvi_delta), 3)
            confianca  = round(min(0.99, 0.60 + ndvi_delta * 1.5), 2)
            nivel      = "alto" if ndvi_delta > 0.20 else "medio"
            criado     = (now - timedelta(days=random.randint(1, 360))).strftime("%Y-%m-%d %H:%M:%S")
            descricao  = (
                f"Queda brusca de NDVI detectada (Δ={ndvi_delta:.3f}). NDVI atual: {ndvi_atual:.3f}. Alta probabilidade de perda de vegetação."
                if nivel == "alto" else
                f"Anomalia de vegetação detectada (Δ={ndvi_delta:.3f}). NDVI atual: {ndvi_atual:.3f}. Monitoramento recomendado."
            )
            c.execute("""
                INSERT INTO ocorrencias
                  (latitude, longitude, status, origem, confianca,
                   ndvi_atual, ndvi_ref, ndvi_delta, descricao, cidade, criado_em)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (round(lat + dlat, 6), round(lon + dlon, 6),
                  "confirmado", "satellite", confianca,
                  ndvi_atual, ndvi_ref, ndvi_delta, descricao, cidade, criado))
            total += 1

    conn.commit()
    conn.close()
    print(f"Seed concluído: {total} ocorrências em {len(AREAS)} áreas do mundo")


if __name__ == "__main__":
    seed()
