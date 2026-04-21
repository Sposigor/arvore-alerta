"""
NASA FIRMS — focos de queimada (VIIRS/MODIS).

Endpoint de área: https://firms.modaps.eosdis.nasa.gov/api/area/csv/{MAP_KEY}/{SOURCE}/{AREA_COORDS}/{DAY_RANGE}/{DATE}

Limites:
- DAY_RANGE máximo: 10 dias por query
- DATE é a data final (YYYY-MM-DD)
- Para SOURCE usamos VIIRS_SNPP_NRT (near-real-time) em dados recentes
  e VIIRS_SNPP_SP (scientific processing) em histórico (>60 dias)
"""
from datetime import date, timedelta
from typing import Optional

import httpx

from app import config


async def contar_focos_fogo(
    lat: float,
    lon: float,
    data_fim: Optional[date] = None,
    janela_dias: int = 30,
    raio_graus: float = 0.05,
) -> Optional[int]:
    """
    Conta focos de fogo em bbox ao redor de (lat, lon) na janela de `janela_dias`
    terminando em `data_fim` (ou hoje). Retorna None se não configurado ou falhar.
    """
    if not config.FIRMS_MAP_KEY:
        return None

    fim = data_fim or date.today()
    source = "VIIRS_SNPP_NRT" if (date.today() - fim).days <= 60 else "VIIRS_SNPP_SP"
    west = lon - raio_graus
    south = lat - raio_graus
    east = lon + raio_graus
    north = lat + raio_graus
    area = f"{west},{south},{east},{north}"

    total = 0
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            restante = janela_dias
            cursor = fim
            while restante > 0:
                passo = min(10, restante)
                url = (
                    f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
                    f"{config.FIRMS_MAP_KEY}/{source}/{area}/{passo}/"
                    f"{cursor.strftime('%Y-%m-%d')}"
                )
                r = await client.get(url)
                r.raise_for_status()
                linhas = r.text.strip().splitlines()
                if len(linhas) > 1:
                    total += len(linhas) - 1
                cursor = cursor - timedelta(days=passo)
                restante -= passo
        return total
    except Exception:
        return None
