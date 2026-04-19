from typing import Optional

import httpx


async def buscar_alertas_inmet(lat: float, lon: float) -> Optional[str]:
    """Busca alertas ativos do INMET. Aplicável apenas ao Brasil."""
    if not (-35 <= lat <= 5 and -74 <= lon <= -28):
        return None
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get("https://apiprevmet3.inmet.gov.br/avisos/ativos")
            if r.status_code != 200:
                return None
            data = r.json()
            avisos = data if isinstance(data, list) else data.get("avisos", [])
            relevantes = []
            for aviso in avisos[:30]:
                titulo = (
                    aviso.get("ds_titulo") or aviso.get("titulo") or
                    aviso.get("descricao") or ""
                )
                nivel = aviso.get("ds_severidade") or aviso.get("nivel") or ""
                if titulo:
                    relevantes.append(f"[{nivel}] {titulo[:80]}" if nivel else titulo[:80])
            return "; ".join(relevantes[:3]) if relevantes else None
    except Exception:
        return None
