import asyncio
from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app import config
from app.database import get_db
from app.services.alertas import buscar_alertas_inmet
from app.services.copernicus import buscar_produto_sentinel2, get_cdse_token
from app.services.deter import contar_alertas_deter
from app.services.firms import contar_focos_fogo
from app.services.ndvi import calcular_ndvi_real, calcular_ndvi_simulado, interpretar_ndvi
from app.services.radar import calcular_radar_real
from app.services.scoring import fortalecer_confianca

router = APIRouter(prefix="/satelite", tags=["satélite"])


@router.post("/analisar")
async def analisar_por_satelite(
    latitude: float = Query(...),
    longitude: float = Query(...),
    cidade: Optional[str] = Query(None),
    bairro: Optional[str] = Query(None),
    dias_ref: int = Query(30, description="Janela de dias para buscar imagem de referência"),
    modo_ref: str = Query("ano_anterior", description="'ano_anterior' ou 'recente'"),
    data_fim: Optional[date] = Query(None, description="Data final da janela (YYYY-MM-DD). Default: hoje"),
):
    produto_nome = "Simulado (sem credenciais CDSE)"
    produto_id = "simulado"

    if config.CDSE_USER and config.CDSE_PASS:
        try:
            produto = await buscar_produto_sentinel2(latitude, longitude, dias_atras=dias_ref)
            if produto:
                produto_id = produto["Id"]
                produto_nome = produto["Name"]
            else:
                produto_nome = f"Nenhum produto Sentinel-2 encontrado nos últimos {dias_ref} dias"
        except Exception as e:
            produto_nome = f"Erro CDSE: {e} — usando simulação"

    ndvi_data = None
    radar_data = None

    if config.CDSE_USER and config.CDSE_PASS and config.OPENEO_DISPONIVEL:
        try:
            token = await get_cdse_token()
            ndvi_data, radar_data = await asyncio.gather(
                calcular_ndvi_real(latitude, longitude, token, dias_ref, modo_ref, data_fim),
                calcular_radar_real(latitude, longitude, token, dias_ref, data_fim),
                return_exceptions=True,
            )
            if isinstance(ndvi_data, Exception):
                produto_nome += f" [NDVI simulado — {type(ndvi_data).__name__}: {ndvi_data}]"
                ndvi_data = None
            if isinstance(radar_data, Exception):
                radar_data = None
        except Exception as e:
            produto_nome += f" [NDVI simulado — {type(e).__name__}: {e}]"

    if ndvi_data is None:
        ndvi_data = calcular_ndvi_simulado(latitude, longitude, produto_id)

    alertas_inmet, focos_fogo, deter_alertas = await asyncio.gather(
        buscar_alertas_inmet(latitude, longitude),
        contar_focos_fogo(latitude, longitude, data_fim),
        contar_alertas_deter(latitude, longitude, data_fim),
    )
    resultado = interpretar_ndvi(ndvi_data["ndvi_delta"], ndvi_data["ndvi_atual"])
    radar_delta = radar_data["vh_delta_db"] if radar_data else None
    confianca_final, fontes_corroborantes = fortalecer_confianca(
        resultado["confianca"], focos_fogo, deter_alertas, radar_delta,
    )
    if fontes_corroborantes:
        resultado["descricao"] += " Corroborado por: " + ", ".join(fontes_corroborantes) + "."

    ocorrencia_id = None
    if resultado["queda_detectada"]:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT OR IGNORE INTO ocorrencias
              (latitude, longitude, status, origem, confianca,
               ndvi_atual, ndvi_ref, ndvi_delta, descricao, cidade, bairro,
               radar_vh_delta, alertas_dc, modo_ref, periodo_atual, periodo_ref,
               focos_fogo, deter_alertas)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            latitude, longitude, "confirmado", "satellite",
            confianca_final,
            ndvi_data["ndvi_atual"], ndvi_data["ndvi_ref"], ndvi_data["ndvi_delta"],
            resultado["descricao"], cidade, bairro,
            radar_delta,
            alertas_inmet, modo_ref,
            ndvi_data.get("periodo_atual"), ndvi_data.get("periodo_ref"),
            focos_fogo, deter_alertas,
        ))
        conn.commit()
        ocorrencia_id = c.lastrowid if c.rowcount > 0 else None
        conn.close()

    return {
        "produto_sentinel2": produto_nome,
        "produto_id": produto_id,
        "ndvi_ref": ndvi_data["ndvi_ref"],
        "ndvi_atual": ndvi_data["ndvi_atual"],
        "ndvi_delta": ndvi_data["ndvi_delta"],
        "periodo_atual": ndvi_data.get("periodo_atual"),
        "periodo_ref": ndvi_data.get("periodo_ref"),
        "modo_ref": modo_ref,
        "data_fim": data_fim.isoformat() if data_fim else None,
        "nivel": resultado["nivel"],
        "queda_detectada": resultado["queda_detectada"],
        "confianca": confianca_final,
        "confianca_ndvi": resultado["confianca"],
        "fontes_corroborantes": fontes_corroborantes,
        "descricao": resultado["descricao"],
        "radar": radar_data,
        "alertas_dc": alertas_inmet,
        "focos_fogo": focos_fogo,
        "deter_alertas": deter_alertas,
        "ocorrencia_id": ocorrencia_id,
    }
