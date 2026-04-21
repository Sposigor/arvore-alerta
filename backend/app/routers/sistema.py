import math

from fastapi import APIRouter

from app import config
from app.database import get_db
from app.scheduler import _scheduler, _seed_cursor

router = APIRouter(tags=["sistema"])


@router.get("/stats")
def estatisticas():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as v FROM ocorrencias")
    total = c.fetchone()["v"]
    c.execute("SELECT COUNT(*) as v FROM ocorrencias WHERE status = 'confirmado'")
    confirmados = c.fetchone()["v"]
    c.execute("SELECT AVG(confianca) as v FROM ocorrencias")
    media = c.fetchone()["v"] or 0
    c.execute("SELECT COUNT(*) as v FROM reportes_usuario WHERE status = 'ativo'")
    reportes = c.fetchone()["v"]
    conn.close()
    return {
        "total": total,
        "confirmados": confirmados,
        "media_confianca": round(media, 2),
        "reportes_usuario": reportes,
    }


@router.get("/cron/status")
def status_cron():
    jobs = []
    if _scheduler.running:
        for job in _scheduler.get_jobs():
            jobs.append({"id": job.id, "proxima_exec": str(job.next_run_time)})
    return {
        "ativo": _scheduler.running,
        "cron_ativo_env": config.CRON_ATIVO,
        "locais_total": len(config.LOCAIS_MONITORAMENTO),
        "lote_por_hora": config.LOTE_POR_HORA,
        "cursor_atual": _seed_cursor,
        "ciclo_completo_h": math.ceil(len(config.LOCAIS_MONITORAMENTO) / config.LOTE_POR_HORA),
        "creditos_mes_est": config.LOTE_POR_HORA * 24 * 30 * 2,
        "jobs": jobs,
        "modo_openeo": config.OPENEO_DISPONIVEL and bool(config.CDSE_USER),
    }
