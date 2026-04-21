import csv
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.database import get_db

router = APIRouter(prefix="/ocorrencias", tags=["ocorrências"])

_COLS = """id, latitude, longitude, status, origem, confianca,
           ndvi_atual, ndvi_ref, ndvi_delta, descricao, criado_em, cidade, bairro,
           radar_vh_delta, alertas_dc, modo_ref, periodo_atual, periodo_ref,
           focos_fogo, deter_alertas"""


@router.get("")
def listar_ocorrencias(limite: int = 100, dias: Optional[int] = None):
    conn = get_db()
    c = conn.cursor()
    if dias:
        desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute(
            f"SELECT {_COLS} FROM ocorrencias WHERE criado_em >= ? ORDER BY criado_em DESC LIMIT ?",
            (desde, limite),
        )
    else:
        c.execute(f"SELECT {_COLS} FROM ocorrencias ORDER BY criado_em DESC LIMIT ?", (limite,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/exportar")
def exportar_ocorrencias(
    formato: str = Query("geojson", description="'geojson' ou 'csv'"),
    dias: Optional[int] = Query(None),
):
    conn = get_db()
    c = conn.cursor()
    if dias:
        desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("SELECT * FROM ocorrencias WHERE criado_em >= ? ORDER BY criado_em DESC", (desde,))
    else:
        c.execute("SELECT * FROM ocorrencias ORDER BY criado_em DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    if formato == "csv":
        output = io.StringIO()
        if rows:
            writer = csv.DictWriter(output, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ocorrencias.csv"},
        )

    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
            "properties": {k: v for k, v in r.items() if k not in ("latitude", "longitude")},
        }
        for r in rows
    ]
    content = json.dumps(
        {"type": "FeatureCollection", "features": features},
        ensure_ascii=False,
        indent=2,
    )
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="application/geo+json",
        headers={"Content-Disposition": "attachment; filename=ocorrencias.geojson"},
    )


@router.delete("/{ocorrencia_id}")
def deletar_ocorrencia(ocorrencia_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (ocorrencia_id,))
    conn.commit()
    conn.close()
    return {"mensagem": "Ocorrência removida"}
