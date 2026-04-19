import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import config
from app.database import get_db
from app.services.alertas import buscar_alertas_inmet
from app.services.copernicus import get_cdse_token
from app.services.ndvi import calcular_ndvi_real, calcular_ndvi_simulado, interpretar_ndvi
from app.services.radar import calcular_radar_real

log = logging.getLogger("arvore_alerta")

_scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")
_seed_cursor = 0


async def executar_seed_automatico():
    global _seed_cursor
    if not config.CDSE_USER or not config.CDSE_PASS or not config.OPENEO_DISPONIVEL:
        return

    try:
        token = await get_cdse_token()
    except Exception as e:
        log.warning(f"[CRON] Falha na autenticação Copernicus: {e}")
        return

    total = len(config.LOCAIS_MONITORAMENTO)
    lote = [config.LOCAIS_MONITORAMENTO[(_seed_cursor + i) % total] for i in range(config.LOTE_POR_HORA)]
    _seed_cursor = (_seed_cursor + config.LOTE_POR_HORA) % total

    log.info(f"[CRON] Processando lote: {[c for _, _, c in lote]}")

    for lat, lon, cidade in lote:
        try:
            resultados = await asyncio.gather(
                calcular_ndvi_real(lat, lon, token, 30),
                calcular_radar_real(lat, lon, token, 30),
                return_exceptions=True,
            )
            ndvi_data = resultados[0] if not isinstance(resultados[0], Exception) \
                else calcular_ndvi_simulado(lat, lon, "cron")
            radar_data = resultados[1] if not isinstance(resultados[1], Exception) else None

            alertas = await buscar_alertas_inmet(lat, lon)
            resultado = interpretar_ndvi(ndvi_data["ndvi_delta"], ndvi_data["ndvi_atual"])

            if resultado["queda_detectada"]:
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    INSERT INTO ocorrencias
                      (latitude, longitude, status, origem, confianca,
                       ndvi_atual, ndvi_ref, ndvi_delta, descricao, cidade,
                       radar_vh_delta, alertas_dc, modo_ref, periodo_atual, periodo_ref)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    lat, lon, "confirmado", "satellite",
                    resultado["confianca"],
                    ndvi_data["ndvi_atual"], ndvi_data["ndvi_ref"], ndvi_data["ndvi_delta"],
                    resultado["descricao"], cidade,
                    radar_data["vh_delta_db"] if radar_data else None,
                    alertas, "ano_anterior",
                    ndvi_data.get("periodo_atual"), ndvi_data.get("periodo_ref"),
                ))
                conn.commit()
                conn.close()
                log.info(f"[CRON] ✓ {cidade}: {resultado['nivel']} Δ={ndvi_data['ndvi_delta']:.3f}")
            else:
                log.info(f"[CRON] – {cidade}: normal Δ={ndvi_data['ndvi_delta']:.3f}")

        except Exception as e:
            log.warning(f"[CRON] Erro em {cidade}: {type(e).__name__}: {e}")

        await asyncio.sleep(5)
