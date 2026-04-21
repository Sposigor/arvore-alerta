import asyncio
import math
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from app import config


def _calcular_radar_sentinel1(
    lat: float,
    lon: float,
    token: str,
    dias_ref: int,
    data_fim: Optional[date] = None,
) -> Optional[dict]:
    """Síncrono — chamar via run_in_executor."""
    if not config.OPENEO_DISPONIVEL:
        return None
    try:
        import openeo
        import numpy as np

        fim_atu_dt = (
            datetime.combine(data_fim, datetime.min.time(), tzinfo=timezone.utc)
            if data_fim else datetime.now(timezone.utc)
        )
        bbox = {"west": lon - 0.02, "south": lat - 0.02, "east": lon + 0.02, "north": lat + 0.02}

        ini_atu = fim_atu_dt - timedelta(days=dias_ref)
        fim_atu = fim_atu_dt
        ini_ref = fim_atu_dt - timedelta(days=365 + dias_ref)
        fim_ref = fim_atu_dt - timedelta(days=365)

        conn = openeo.connect("https://openeo.dataspace.copernicus.eu")
        conn.authenticate_oidc_access_token(token)

        def vh_media(ini: datetime, fim: datetime) -> float:
            cube = conn.load_collection(
                "SENTINEL1_GRD",
                spatial_extent=bbox,
                temporal_extent=[ini.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")],
                bands=["VH"],
            )
            result = cube.mean_time().execute()
            val = float(np.nanmean(np.array(result.values, dtype=float)))
            if np.isnan(val):
                raise ValueError("Sem dados Sentinel-1 no período")
            return val

        vh_atu = vh_media(ini_atu, fim_atu)
        vh_ref = vh_media(ini_ref, fim_ref)
        delta_db = round(
            10 * math.log10(max(vh_ref, 1e-10)) - 10 * math.log10(max(vh_atu, 1e-10)), 2
        )
        return {"vh_ref": round(vh_ref, 6), "vh_atual": round(vh_atu, 6), "vh_delta_db": delta_db}
    except Exception:
        return None


async def calcular_radar_real(
    lat: float,
    lon: float,
    token: str,
    dias_ref: int,
    data_fim: Optional[date] = None,
) -> Optional[dict]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        config.executor, _calcular_radar_sentinel1, lat, lon, token, dias_ref, data_fim
    )
