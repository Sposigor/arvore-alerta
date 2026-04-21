import asyncio
import math
import random
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app import config


def calcular_ndvi_simulado(lat: float, lon: float, produto_id: str) -> dict:
    """
    Stub de NDVI. Em produção, substitua pelo download real das bandas
    B04 (Red) e B08 (NIR) via API S3 do CDSE.
    NDVI = (NIR - Red) / (NIR + Red)
    """
    base = 0.55 + 0.20 * math.sin(lat * 10) * math.cos(lon * 10)
    ndvi_ref = round(max(0.1, min(0.9, base + random.uniform(-0.05, 0.05))), 3)
    ndvi_atual = round(max(0.0, ndvi_ref - random.uniform(0.05, 0.35)), 3)
    delta = round(ndvi_ref - ndvi_atual, 3)
    return {"ndvi_ref": ndvi_ref, "ndvi_atual": ndvi_atual, "ndvi_delta": delta}


def _calcular_ndvi_openeo(
    lat: float,
    lon: float,
    token: str,
    dias_ref: int,
    modo_ref: str = "ano_anterior",
    data_fim: Optional[date] = None,
) -> dict:
    """Síncrono — chamar via run_in_executor."""
    import openeo
    import numpy as np

    fim_atu_dt = (
        datetime.combine(data_fim, datetime.min.time(), tzinfo=timezone.utc)
        if data_fim else datetime.now(timezone.utc)
    )
    bbox = {"west": lon - 0.01, "south": lat - 0.01, "east": lon + 0.01, "north": lat + 0.01}

    ini_atu = fim_atu_dt - timedelta(days=dias_ref)
    fim_atu = fim_atu_dt
    if modo_ref == "recente":
        ini_ref = fim_atu_dt - timedelta(days=2 * dias_ref)
        fim_ref = fim_atu_dt - timedelta(days=dias_ref)
    else:
        ini_ref = fim_atu_dt - timedelta(days=365 + dias_ref)
        fim_ref = fim_atu_dt - timedelta(days=365)

    conn = openeo.connect("https://openeo.dataspace.copernicus.eu")
    conn.authenticate_oidc_access_token(token)

    ponto_geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {},
        }],
    }

    def ndvi_media(ini: datetime, fim: datetime) -> float:
        cube = conn.load_collection(
            "SENTINEL2_L2A",
            spatial_extent=bbox,
            temporal_extent=[ini.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")],
            bands=["B04", "B08"],
            max_cloud_cover=30,
        )
        nir = cube.band("B08")
        red = cube.band("B04")
        ndvi = (nir - red) / (nir + red)
        serie = ndvi.aggregate_spatial(geometries=ponto_geojson, reducer="mean").execute()
        vals = []
        for _, amostras in serie.items():
            for v in amostras:
                if v is not None and not (isinstance(v, float) and np.isnan(v)):
                    vals.append(float(v))
        if not vals:
            raise ValueError("Sem imagens válidas no período (cobertura de nuvens alta ou sem dados)")
        return float(np.mean(vals))

    v_atu = ndvi_media(ini_atu, fim_atu)
    v_ref = ndvi_media(ini_ref, fim_ref)
    delta = round(max(0.0, v_ref - v_atu), 3)

    return {
        "ndvi_ref": round(v_ref, 3),
        "ndvi_atual": round(v_atu, 3),
        "ndvi_delta": delta,
        "periodo_atual": f"{ini_atu.strftime('%d/%m/%Y')} – {fim_atu.strftime('%d/%m/%Y')}",
        "periodo_ref": f"{ini_ref.strftime('%d/%m/%Y')} – {fim_ref.strftime('%d/%m/%Y')}",
    }


async def calcular_ndvi_real(
    lat: float,
    lon: float,
    token: str,
    dias_ref: int,
    modo_ref: str = "ano_anterior",
    data_fim: Optional[date] = None,
) -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        config.executor, _calcular_ndvi_openeo, lat, lon, token, dias_ref, modo_ref, data_fim
    )


def interpretar_ndvi(ndvi_delta: float, ndvi_atual: float) -> dict:
    if ndvi_delta > 0.20:
        return {
            "queda_detectada": True,
            "confianca": round(min(0.99, 0.60 + ndvi_delta * 1.5), 2),
            "nivel": "alto",
            "descricao": (
                f"Queda brusca de NDVI detectada (Δ={ndvi_delta:.3f}). "
                f"NDVI atual: {ndvi_atual:.3f}. Alta probabilidade de perda de vegetação."
            ),
        }
    elif ndvi_delta > 0.10:
        return {
            "queda_detectada": True,
            "confianca": round(0.40 + ndvi_delta * 1.5, 2),
            "nivel": "medio",
            "descricao": (
                f"Anomalia de vegetação detectada (Δ={ndvi_delta:.3f}). "
                f"NDVI atual: {ndvi_atual:.3f}. Monitoramento recomendado."
            ),
        }
    else:
        return {
            "queda_detectada": False,
            "confianca": 0.0,
            "nivel": "normal",
            "descricao": (
                f"Vegetação estável (Δ={ndvi_delta:.3f}). "
                f"NDVI atual: {ndvi_atual:.3f}. Nenhuma anomalia detectada."
            ),
        }
