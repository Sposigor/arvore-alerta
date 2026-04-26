#!/usr/bin/env python3
"""
Cruzamento temporal entre ArvoreAlerta (Sentinel-2 via openEO) e MODIS MOD13Q1.

Para cada registro nosso (ocorrencias + ndvi_historico), busca a amostra MODIS
mais próxima na mesma cidade (loc match por lat/lon ≤ 0.5°) dentro de ±32 dias
do meio do periodo_atual. Compara NDVI atual e Δ.

Saída: backend/scripts/comparacao_arvorealerta_vs_modis.csv
"""
import csv
import os
import sqlite3
import sys
from datetime import datetime, timedelta

OCO = "/tmp/ocorrencias_prod.csv"
NDVI_HIST = "/tmp/ndvi_hist_prod.csv"
MODIS_DB = os.path.join(os.path.dirname(__file__), "..", "modis_local.db")
OUT = os.path.join(os.path.dirname(__file__), "comparacao_arvorealerta_vs_modis.csv")
JANELA = 32  # dias


def parse_periodo(p: str):
    """'25/03/2026 – 24/04/2026' → (datetime_ini, datetime_fim, datetime_meio)."""
    if not p:
        return None
    try:
        ini_s, fim_s = [x.strip() for x in p.replace("–", "-").split("-", 1)]
        ini = datetime.strptime(ini_s, "%d/%m/%Y")
        fim = datetime.strptime(fim_s, "%d/%m/%Y")
        meio = ini + (fim - ini) / 2
        return ini, fim, meio
    except Exception:
        return None


def carregar_modis():
    conn = sqlite3.connect(MODIS_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT cidade, latitude, longitude, data, ndvi FROM modis_ndvi ORDER BY data")
    rows = []
    for r in c.fetchall():
        rows.append({
            "cidade": r["cidade"], "lat": r["latitude"], "lon": r["longitude"],
            "data": datetime.strptime(r["data"], "%Y-%m-%d"), "ndvi": r["ndvi"],
        })
    conn.close()
    return rows


def achar_modis_proximo(modis_rows, lat, lon, alvo, janela_dias=JANELA):
    """Casamento por lat/lon ≤ 0.5° e |dt - alvo| ≤ janela_dias."""
    cands = [
        m for m in modis_rows
        if abs(m["lat"] - lat) <= 0.5 and abs(m["lon"] - lon) <= 0.5
        and abs((m["data"] - alvo).days) <= janela_dias
    ]
    if not cands:
        return None
    return min(cands, key=lambda m: abs((m["data"] - alvo).days))


def carregar_csvs():
    nossos = []
    with open(OCO, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nossos.append({"fonte": "ocorrencias", **r})
    with open(NDVI_HIST, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nossos.append({"fonte": "ndvi_historico", **r})
    return nossos


def main():
    modis = carregar_modis()
    nossos = carregar_csvs()
    print(f"MODIS: {len(modis)} amostras  |  ArvoreAlerta: {len(nossos)} registros")

    saidas = []
    sem_match = 0
    for r in nossos:
        per = parse_periodo(r.get("periodo_atual", ""))
        if not per:
            sem_match += 1
            continue
        _, _, meio = per
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
        except (ValueError, TypeError):
            continue
        m = achar_modis_proximo(modis, lat, lon, meio)
        if not m:
            sem_match += 1
            continue

        ndvi_atu_aa = float(r["ndvi_atual"])
        delta_aa = float(r["ndvi_delta"])
        diff_ndvi = round(ndvi_atu_aa - m["ndvi"], 4)
        saidas.append({
            "fonte": r["fonte"],
            "cidade": r.get("cidade", ""),
            "latitude": lat, "longitude": lon,
            "periodo_atual": r["periodo_atual"],
            "data_meio": meio.strftime("%Y-%m-%d"),
            "modis_data": m["data"].strftime("%Y-%m-%d"),
            "modis_dt_dias": (m["data"] - meio).days,
            "ndvi_atual_aa": round(ndvi_atu_aa, 4),
            "ndvi_atual_modis": round(m["ndvi"], 4),
            "diff_ndvi_aa_minus_modis": diff_ndvi,
            "ndvi_delta_aa": delta_aa,
            "queda_aa": int((r.get("queda_detectada") or "0") in ("1", "true", "True"))
                        if r["fonte"] == "ndvi_historico" else 1,
            "nivel_aa": r.get("nivel") or r.get("descricao", "")[:50],
        })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(saidas[0].keys()))
        w.writeheader()
        w.writerows(saidas)

    diffs = [s["diff_ndvi_aa_minus_modis"] for s in saidas]
    media = sum(diffs) / len(diffs) if diffs else 0
    abs_media = sum(abs(d) for d in diffs) / len(diffs) if diffs else 0
    concord = sum(1 for s in saidas if abs(s["diff_ndvi_aa_minus_modis"]) <= 0.10)

    print(f"\nMatches: {len(saidas)}  |  Sem match: {sem_match}")
    print(f"NDVI ArvoreAlerta - MODIS:  média={media:+.4f}  |  |média|={abs_media:.4f}")
    print(f"Concordância (|Δ|≤0.10):    {concord}/{len(saidas)} ({concord/max(len(saidas),1)*100:.1f}%)")
    print(f"\nCSV: {OUT}")


if __name__ == "__main__":
    main()
