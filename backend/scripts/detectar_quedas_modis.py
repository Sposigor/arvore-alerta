#!/usr/bin/env python3
"""
Aplica o algoritmo de detecção de queda do ArvoreAlerta sobre toda a série
MODIS MOD13Q1 (2019-2026, 48 locais) e gera CSV de eventos.

Para cada amostra MODIS (loc_id, data, ndvi_atual):
  - Busca a amostra MODIS mais próxima de 365 dias antes (janela ±32 dias)
  - Δ = ndvi_ref - ndvi_atual
  - Classifica via interpretar_ndvi (mesmos thresholds do backend)

Saída: backend/scripts/quedas_modis.csv
"""
import csv
import os
import sqlite3
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.services.ndvi import interpretar_ndvi  # noqa: E402

DB = os.path.join(os.path.dirname(__file__), "..", "modis_local.db")
OUT = os.path.join(os.path.dirname(__file__), "quedas_modis.csv")

JANELA_REF_DIAS = 32  # ±32 dias em torno de t-365 (2 composites MODIS = 32d)


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("""
        SELECT loc_id, cidade, latitude, longitude, data, ndvi
        FROM modis_ndvi
        ORDER BY loc_id, data
    """)
    rows = [dict(r) for r in c.fetchall()]

    por_loc = {}
    for r in rows:
        por_loc.setdefault(r["loc_id"], []).append({
            **r,
            "data_dt": datetime.strptime(r["data"], "%Y-%m-%d").date(),
        })

    eventos = []
    sem_ref = 0
    for loc_id, serie in por_loc.items():
        datas_set = [s["data_dt"] for s in serie]
        for atu in serie:
            alvo = atu["data_dt"] - timedelta(days=365)
            ini = alvo - timedelta(days=JANELA_REF_DIAS)
            fim = alvo + timedelta(days=JANELA_REF_DIAS)

            candidatos = [s for s in serie if ini <= s["data_dt"] <= fim]
            if not candidatos:
                sem_ref += 1
                continue
            ref = min(candidatos, key=lambda s: abs((s["data_dt"] - alvo).days))
            ndvi_ref = ref["ndvi"]
            ndvi_atu = atu["ndvi"]
            delta = round(max(0.0, ndvi_ref - ndvi_atu), 3)
            interp = interpretar_ndvi(delta, ndvi_atu)
            eventos.append({
                "loc_id": loc_id,
                "cidade": atu["cidade"],
                "latitude": atu["latitude"],
                "longitude": atu["longitude"],
                "data_atual": atu["data"],
                "data_ref": ref["data"],
                "ndvi_atual": round(ndvi_atu, 4),
                "ndvi_ref": round(ndvi_ref, 4),
                "ndvi_delta": delta,
                "queda_detectada": int(interp["queda_detectada"]),
                "nivel": interp["nivel"],
                "confianca": interp["confianca"],
            })

    conn.close()

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(eventos[0].keys()))
        w.writeheader()
        w.writerows(eventos)

    quedas = [e for e in eventos if e["queda_detectada"]]
    alto = sum(1 for e in quedas if e["nivel"] == "alto")
    medio = sum(1 for e in quedas if e["nivel"] == "medio")
    cidades_com_queda = len({e["cidade"] for e in quedas})

    print(f"CSV: {OUT}")
    print(f"Total eventos analisados:  {len(eventos)}")
    print(f"Sem referência (t-365):    {sem_ref}")
    print(f"Quedas detectadas:         {len(quedas)} ({len(quedas)/max(len(eventos),1)*100:.1f}%)")
    print(f"  ALTO  (Δ>0.20):          {alto}")
    print(f"  MEDIO (Δ>0.10):          {medio}")
    print(f"Cidades com ≥1 queda:      {cidades_com_queda} de 48")

    by_cid = {}
    for e in quedas:
        by_cid.setdefault(e["cidade"], 0)
        by_cid[e["cidade"]] += 1
    top = sorted(by_cid.items(), key=lambda x: -x[1])[:10]
    print("\nTop 10 cidades por nº de quedas:")
    for cid, n in top:
        print(f"  {cid:<25} {n}")


if __name__ == "__main__":
    main()
