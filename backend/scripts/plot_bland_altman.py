#!/usr/bin/env python3
"""
Bland-Altman: análise de concordância entre Δ NDVI ArvoreAlerta (Sentinel-2)
e Δ NDVI MODIS MOD13Q1 nos mesmos pontos/datas.

Eixo X: média dos dois métodos     ((Δ_AA + Δ_MODIS) / 2)
Eixo Y: diferença entre métodos    (Δ_AA - Δ_MODIS)
Linhas: viés (média) + limites de concordância (±1.96·DP)

Saída: backend/scripts/bland_altman_delta.png
"""
import csv
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CSV = os.path.join(os.path.dirname(__file__), "comparacao_delta_aa_vs_modis.csv")
OUT = os.path.join(os.path.dirname(__file__), "bland_altman_delta.png")


def main():
    aa, modis = [], []
    with open(CSV, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            aa.append(float(r["delta_aa"]))
            modis.append(float(r["delta_modis"]))

    aa = np.array(aa)
    modis = np.array(modis)
    media = (aa + modis) / 2
    diff = aa - modis

    vies = float(np.mean(diff))
    dp = float(np.std(diff, ddof=1))
    sup = vies + 1.96 * dp
    inf = vies - 1.96 * dp

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(media, diff, alpha=0.65, s=55, color="#1f77b4", edgecolor="white", linewidth=0.8)

    ax.axhline(vies, color="#d62728", linewidth=1.8, label=f"Viés = {vies:+.4f}")
    ax.axhline(sup, color="#7f7f7f", linewidth=1.2, linestyle="--",
               label=f"+1.96·DP = {sup:+.4f}")
    ax.axhline(inf, color="#7f7f7f", linewidth=1.2, linestyle="--",
               label=f"−1.96·DP = {inf:+.4f}")
    ax.axhline(0, color="black", linewidth=0.5, alpha=0.3)

    ax.set_xlabel("Média dos métodos: (Δ ArvoreAlerta + Δ MODIS) / 2", fontsize=11)
    ax.set_ylabel("Diferença: Δ ArvoreAlerta − Δ MODIS", fontsize=11)
    ax.set_title(
        f"Bland-Altman — Concordância Δ NDVI (n={len(aa)})\n"
        f"ArvoreAlerta (Sentinel-2 / openEO) vs MODIS MOD13Q1.061",
        fontsize=12,
    )
    ax.grid(True, alpha=0.25)
    ax.legend(loc="upper right", framealpha=0.95, fontsize=9)

    dentro = int(np.sum((diff >= inf) & (diff <= sup)))
    ax.text(
        0.02, 0.02,
        f"Pontos dentro dos limites: {dentro}/{len(aa)} ({dentro/len(aa)*100:.1f}%)\n"
        f"DP da diferença: {dp:.4f}",
        transform=ax.transAxes, fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="gray"),
    )

    plt.tight_layout()
    plt.savefig(OUT, dpi=150, bbox_inches="tight")
    print(f"PNG: {OUT}")
    print(f"\nEstatísticas Bland-Altman (n={len(aa)}):")
    print(f"  Viés (média da diferença):   {vies:+.4f}")
    print(f"  DP da diferença:             {dp:.4f}")
    print(f"  Limite superior (+1.96·DP):  {sup:+.4f}")
    print(f"  Limite inferior (−1.96·DP):  {inf:+.4f}")
    print(f"  Dentro dos limites:          {dentro}/{len(aa)} ({dentro/len(aa)*100:.1f}%)")


if __name__ == "__main__":
    main()
