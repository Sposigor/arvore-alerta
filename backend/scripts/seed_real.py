#!/usr/bin/env python3
"""
Popula o banco com NDVI REAL via Copernicus CDSE + openEO.
Pré-requisito: backend rodando em http://localhost:8000

Execute:  python seed_real.py
Cada cidade leva ~60-120 s (2 chamadas openEO por ponto).
Cidades sem imagens disponíveis são puladas automaticamente.
"""
import httpx, time, sys

API = "http://localhost:8000"

# (lat, lon, cidade)  — subconjunto representativo do mundo
CIDADES = [
    # São Paulo — alta densidade
    (-23.550, -46.633, "São Paulo"),
    (-23.620, -46.520, "São Paulo — Zona Leste"),
    (-23.490, -46.840, "São Paulo — Zona Oeste"),
    (-23.670, -46.700, "São Paulo — Zona Sul"),
    (-23.960, -46.340, "Santos"),
    (-22.900, -47.060, "Campinas"),
    (-23.180, -45.880, "São José dos Campos"),
    (-23.500, -47.460, "Sorocaba"),
    (-23.100, -46.550, "Guarulhos"),
    # Brasil
    (-22.900, -43.170, "Rio de Janeiro"),
    (-3.100,  -60.020, "Manaus"),
    (-1.460,  -48.500, "Belém"),
    (-12.970, -38.510, "Salvador"),
    (-8.050,  -34.880, "Recife"),
    (-15.780, -47.930, "Brasília"),
    (-19.920, -43.940, "Belo Horizonte"),
    (-25.430, -49.270, "Curitiba"),
    # América do Norte
    (37.770,  -122.420, "San Francisco"),
    (25.770,   -80.190, "Miami"),
    (19.430,   -99.130, "Cidade do México"),
    # Europa
    (51.510,    -0.120, "Londres"),
    (48.860,     2.350, "Paris"),
    (52.520,    13.400, "Berlim"),
    # Ásia
    (35.690,   139.690, "Tóquio"),
    (1.350,    103.820, "Singapura"),
    (-6.210,   106.850, "Jacarta"),
    # África
    (-1.290,    36.820, "Nairóbi"),
    (-4.320,    15.320, "Kinshasa"),
    # Oceania
    (-33.870,  151.210, "Sydney"),
]

def seed():
    total_ok  = 0
    total_err = 0

    for i, (lat, lon, cidade) in enumerate(CIDADES, 1):
        print(f"[{i:02d}/{len(CIDADES)}] {cidade} ({lat:.3f}, {lon:.3f}) ... ", end="", flush=True)
        try:
            r = httpx.post(
                f"{API}/satelite/analisar",
                params={"latitude": lat, "longitude": lon, "cidade": cidade, "dias_ref": 30},
                timeout=180,
            )
            r.raise_for_status()
            d = r.json()
            if d.get("queda_detectada"):
                print(f"queda {d['nivel'].upper()} Δ={d['ndvi_delta']:.3f} conf={d['confianca']:.0%}")
            else:
                print(f"normal Δ={d['ndvi_delta']:.3f}")
            total_ok += 1
        except Exception as e:
            print(f"ERRO — {e}")
            total_err += 1

        # pausa entre chamadas para não sobrecarregar a API
        if i < len(CIDADES):
            time.sleep(3)

    print(f"\nConcluído: {total_ok} inseridas, {total_err} com erro")

if __name__ == "__main__":
    print(f"Conectando ao backend em {API}...")
    try:
        httpx.get(f"{API}/stats", timeout=5).raise_for_status()
    except Exception:
        print("Erro: backend não está rodando. Inicie com: uvicorn main:app --reload --port 8000")
        sys.exit(1)

    print(f"Backend OK. Iniciando seed real com {len(CIDADES)} cidades...\n")
    seed()
