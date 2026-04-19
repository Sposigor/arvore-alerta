import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.database import init_db
from app.routers import ocorrencias, satelite, sistema, usuario
from app.scheduler import _scheduler, executar_seed_automatico

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("arvore_alerta")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_path_env = os.getenv("DB_PATH")
    if db_path_env:
        config.DB_PATH = db_path_env
    init_db()

    if config.CDSE_USER and config.CDSE_PASS and config.OPENEO_DISPONIVEL:
        _scheduler.add_job(
            executar_seed_automatico, "interval", hours=1,
            id="seed_automatico", replace_existing=True,
        )
        _scheduler.start()
        log.info(
            f"[CRON] Monitoramento ativo — {config.LOTE_POR_HORA} locais/hora, "
            f"{len(config.LOCAIS_MONITORAMENTO)} locais no total"
        )
    else:
        log.info("[CRON] Monitoramento desativado (sem credenciais Copernicus)")

    yield

    if _scheduler.running:
        _scheduler.shutdown(wait=False)


app = FastAPI(title="ArvoreAlerta API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(satelite.router)
app.include_router(usuario.router)
app.include_router(ocorrencias.router)
app.include_router(sistema.router)
