#!/usr/bin/env python3
"""
Compara Δ-vs-Δ: para cada registro nosso (ArvoreAlerta), busca o evento
MODIS mais próximo na mesma cidade (±32 dias do meio do periodo_atual)
e compara ndvi_delta_aa vs ndvi_delta_modis (calculado em quedas_modis.csv).

Saída: backend/scripts/comparacao_delta_aa_vs_modis.csv
"""
import csv
import os
from datetime import datetime

OCO = "/tmp/ocorrencias_prod.csv"
NDVI_HIST = "/tmp/ndvi_hist_prod.csv"
QUEDAS_MODIS = os.path.join(os.path.dirname(__file__), "quedas_modis.csv")
OUT = os.path.join(os.path.dirname(__file__), "comparacao_delta_aa_vs_modis.csv")
JANELA = 32


def parse_periodo(p: str):
    if not p:
        return None
    try:
        ini_s, fim_s = [x.strip() for x in p.replace("–", "-").split("-", 1)]
        ini = datetime.strptime(ini_s, "%d/%m/%Y")
        fim = datetime.strptime(fim_s, "%d/%m/%Y")
        return ini + (fim - ini) / 2
    except Exception:
        return None


def carregar_modis_eventos():
    eventos = []
    with open(QUEDAS_MODIS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            eventos.append({
                "lat": float(r["latitude"]), "lon": float(r["longitude"]),
                "data": datetime.strptime(r["data_atual"], "%Y-%m-%d"),
                "delta": float(r["ndvi_delta"]),
                "queda": int(r["queda_detectada"]),
                "nivel": r["nivel"],
                "ndvi_atual": float(r["ndvi_atual"]),
            })
    return eventos


def carregar_nossos():
    nossos = []
    with open(OCO, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["fonte"] = "ocorrencias"
            r["queda_detectada"] = "1"  # ocorrencias = sempre queda
            nossos.append(r)
    with open(NDVI_HIST, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["fonte"] = "ndvi_historico"
            nossos.append(r)
    return nossos


def achar_modis(eventos, lat, lon, alvo):
    cands = [
        e for e in eventos
        if abs(e["lat"] - lat) <= 0.5 and abs(e["lon"] - lon) <= 0.5
        and abs((e["data"] - alvo).days) <= JANELA
    ]
    if not cands:
        return None
    return min(cands, key=lambda e: abs((e["data"] - alvo).days))


def main():
    eventos = carregar_modis_eventos()
    nossos = carregar_nossos()
    print(f"MODIS eventos: {len(eventos)}  |  ArvoreAlerta: {len(nossos)}")

    saidas = []
    sem_match = 0
    for r in nossos:
        meio = parse_periodo(r.get("periodo_atual", ""))
        if not meio:
            sem_match += 1
            continue
        try:
            lat, lon = float(r["latitude"]), float(r["longitude"])
        except (ValueError, TypeError):
            continue
        m = achar_modis(eventos, lat, lon, meio)
        if not m:
            sem_match += 1
            continue

        delta_aa = float(r["ndvi_delta"])
        queda_aa = int((r.get("queda_detectada") or "0") in ("1", "true", "True"))
        saidas.append({
            "fonte": r["fonte"],
            "cidade": r.get("cidade", ""),
            "periodo_atual": r["periodo_atual"],
            "data_meio": meio.strftime("%Y-%m-%d"),
            "modis_data": m["data"].strftime("%Y-%m-%d"),
            "modis_dt_dias": (m["data"] - meio).days,
            "delta_aa": round(delta_aa, 4),
            "delta_modis": round(m["delta"], 4),
            "diff_delta": round(delta_aa - m["delta"], 4),
            "queda_aa": queda_aa,
            "queda_modis": m["queda"],
            "nivel_modis": m["nivel"],
            "concorda_queda": int(queda_aa == m["queda"]),
        })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(saidas[0].keys()))
        w.writeheader()
        w.writerows(saidas)

    n = len(saidas)
    diffs = [s["diff_delta"] for s in saidas]
    media = sum(diffs) / n
    abs_media = sum(abs(d) for d in diffs) / n
    concord_delta = sum(1 for s in saidas if abs(s["diff_delta"]) <= 0.10)
    concord_queda = sum(1 for s in saidas if s["concorda_queda"])

    tp = sum(1 for s in saidas if s["queda_aa"] == 1 and s["queda_modis"] == 1)
    tn = sum(1 for s in saidas if s["queda_aa"] == 0 and s["queda_modis"] == 0)
    fp = sum(1 for s in saidas if s["queda_aa"] == 1 and s["queda_modis"] == 0)
    fn = sum(1 for s in saidas if s["queda_aa"] == 0 and s["queda_modis"] == 1)

    print(f"\nMatches: {n}  |  Sem match: {sem_match}")
    print(f"\nΔ ArvoreAlerta − Δ MODIS:")
    print(f"  média:                {media:+.4f}")
    print(f"  |média|:              {abs_media:.4f}")
    print(f"  Concordância |Δ|≤0.10: {concord_delta}/{n} ({concord_delta/n*100:.1f}%)")
    print(f"\nClassificação queda (sim/não):")
    print(f"  Concordância:         {concord_queda}/{n} ({concord_queda/n*100:.1f}%)")
    print(f"  TP={tp}  TN={tn}  FP={fp}  FN={fn}")
    if tp + fp > 0:
        print(f"  Precisão (AA→MODIS):  {tp/(tp+fp)*100:.1f}%")
    if tp + fn > 0:
        print(f"  Recall (MODIS→AA):    {tp/(tp+fn)*100:.1f}%")
    print(f"\nCSV: {OUT}")


if __name__ == "__main__":
    main()
