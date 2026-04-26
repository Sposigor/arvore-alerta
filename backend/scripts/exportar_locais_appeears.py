#!/usr/bin/env python3
"""
Gera CSV no formato esperado pelo AppEEARS (NASA Earthdata) para submissão
de Point Sample. Use o CSV em https://appeears.earthdatacloud.nasa.gov
> Extract > Point Sample > Upload CSV.

Produtos sugeridos para NDVI:
  - MOD13Q1.061  (MODIS Terra NDVI, 16-dias, 250m, 2000-presente)
  - MYD13Q1.061  (MODIS Aqua NDVI, 16-dias, 250m, 2002-presente)
  - HLSS30.020   (Sentinel-2 HLS NDVI, ~5 dias, 30m, 2015-presente)

Layers a marcar: _250m_16_days_NDVI (MODIS) ou NDVI calculado (HLS via B8A,B04).
"""
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import LOCAIS_MONITORAMENTO  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "locais_appeears.csv")

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ID", "Category", "Latitude", "Longitude"])
    for i, (lat, lon, cidade) in enumerate(LOCAIS_MONITORAMENTO, start=1):
        w.writerow([f"loc_{i:03d}", cidade, lat, lon])

print(f"Gerado: {OUT} ({len(LOCAIS_MONITORAMENTO)} pontos)")
