from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import HTTPException

from app import config


async def get_cdse_token() -> str:
    if not config.CDSE_USER or not config.CDSE_PASS:
        raise HTTPException(
            status_code=503,
            detail=(
                "Credenciais Copernicus não configuradas. "
                "Crie conta em https://dataspace.copernicus.eu e defina "
                "CDSE_USER e CDSE_PASS como variáveis de ambiente."
            ),
        )
    async with httpx.AsyncClient() as client:
        r = await client.post(
            config.CDSE_TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": "cdse-public",
                "username": config.CDSE_USER,
                "password": config.CDSE_PASS,
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()["access_token"]


async def buscar_produto_sentinel2(lat: float, lon: float, dias_atras: int = 30) -> Optional[dict]:
    data_fim = datetime.now(timezone.utc)
    data_ini = data_fim - timedelta(days=dias_atras)
    d = 0.005

    filtro = (
        f"Collection/Name eq 'SENTINEL-2' "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(("
        f"{lon-d} {lat-d},{lon+d} {lat-d},{lon+d} {lat+d},{lon-d} {lat+d},{lon-d} {lat-d}))')"
        f" and ContentDate/Start gt {data_ini.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"
        f" and ContentDate/Start lt {data_fim.strftime('%Y-%m-%dT%H:%M:%S.000Z')}"
        f" and Attributes/OData.CSC.DoubleAttribute/any("
        f"att:att/Name eq 'cloudCover' and att/OData.CSC.DoubleAttribute/Value lt 20.00)"
        f" and contains(Name,'L2A')"
    )

    async with httpx.AsyncClient() as client:
        r = await client.get(
            config.CDSE_SEARCH_URL,
            params={"$filter": filtro, "$orderby": "ContentDate/Start desc", "$top": "1"},
            timeout=30,
        )
        r.raise_for_status()
        items = r.json().get("value", [])
        return items[0] if items else None
