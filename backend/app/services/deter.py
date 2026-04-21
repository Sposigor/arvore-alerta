"""
INPE TerraBrasilis — DETER (alertas de desmatamento quase tempo real).

Consulta via WFS GetFeature no GeoServer público do TerraBrasilis.
Biomas cobertos: Amazônia (deter-amz) e Cerrado (deter-cerrado).

Docs: https://terrabrasilis.dpi.inpe.br/geoserver/web/
"""
from datetime import date, timedelta
from typing import Optional

import httpx

WFS_URL = "https://terrabrasilis.dpi.inpe.br/geoserver/ows"
LAYERS = ["deter-amz:deter_amz", "deter-cerrado:deter_cerrado"]


async def contar_alertas_deter(
    lat: float,
    lon: float,
    data_fim: Optional[date] = None,
    janela_dias: int = 90,
    raio_graus: float = 0.05,
) -> Optional[int]:
    """
    Conta polígonos DETER em bbox ao redor de (lat, lon) na janela de `janela_dias`
    terminando em `data_fim`. Consulta Amazônia e Cerrado, soma os dois.
    Retorna None se todas as camadas falharem.
    """
    fim = data_fim or date.today()
    ini = fim - timedelta(days=janela_dias)
    west, south = lon - raio_graus, lat - raio_graus
    east, north = lon + raio_graus, lat + raio_graus

    cql = (
        f"BBOX(geom,{west},{south},{east},{north}) "
        f"AND view_date BETWEEN '{ini.strftime('%Y-%m-%d')}' "
        f"AND '{fim.strftime('%Y-%m-%d')}'"
    )

    total = 0
    sucesso = False
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            for layer in LAYERS:
                params = {
                    "service": "WFS",
                    "version": "2.0.0",
                    "request": "GetFeature",
                    "typeNames": layer,
                    "outputFormat": "application/json",
                    "CQL_FILTER": cql,
                    "count": "1000",
                }
                try:
                    r = await client.get(WFS_URL, params=params)
                    r.raise_for_status()
                    data = r.json()
                    total += len(data.get("features", []))
                    sucesso = True
                except Exception:
                    continue
        return total if sucesso else None
    except Exception:
        return None
