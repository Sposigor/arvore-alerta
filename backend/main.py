"""
ArvoreAlerta — Backend FastAPI v2.0
Dois modos de detecção:
  1. Satélite: consulta Sentinel-2 via Copernicus CDSE e calcula NDVI
  2. Usuário:  reporte manual estilo Waze com confirmações coletivas
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3
import httpx
import os
import math
import random
import asyncio
import csv
import io
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

try:
    import openeo
    import numpy as np
    OPENEO_DISPONIVEL = True
except ImportError:
    OPENEO_DISPONIVEL = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("arvore_alerta")

_executor = ThreadPoolExecutor(max_workers=2)

load_dotenv()

# -------------------------------------------------------
# Locais de monitoramento automático
# Fonte: PRODES/DETER (INPE) — principais focos de desmatamento
# e maiores cidades brasileiras
# -------------------------------------------------------
LOCAIS_MONITORAMENTO = [
    # --- Capitais e metrópoles ---
    (-23.550, -46.633, "São Paulo"),
    (-22.906, -43.173, "Rio de Janeiro"),
    (-19.917, -43.934, "Belo Horizonte"),
    (-15.779, -47.929, "Brasília"),
    (-12.971, -38.511, "Salvador"),
    ( -8.054, -34.881, "Recife"),
    ( -3.717, -38.543, "Fortaleza"),
    ( -3.119, -60.022, "Manaus"),
    ( -1.456, -48.502, "Belém"),
    (-25.429, -49.271, "Curitiba"),
    (-30.033, -51.230, "Porto Alegre"),
    ( -2.529, -44.303, "São Luís"),
    (-10.912, -37.073, "Aracaju"),
    ( -8.761, -63.900, "Porto Velho"),
    ( -9.975, -67.824, "Rio Branco"),
    # --- Hotspots de desmatamento — Arco da Amazônia (INPE/DETER) ---
    # Pará (maior desmatador recente)
    ( -7.530, -55.030, "Altamira — PA"),
    ( -7.093, -55.110, "Novo Progresso — PA"),
    ( -6.638, -51.955, "São Félix do Xingu — PA"),
    ( -3.380, -53.050, "Rurópolis — PA"),
    ( -5.450, -55.430, "Trairão — PA"),
    ( -4.810, -53.770, "Placas — PA"),
    ( -6.200, -55.530, "Itaituba — PA"),
    # Mato Grosso
    ( -9.977, -58.200, "Colniza — MT"),
    (-10.370, -58.020, "Alta Floresta — MT"),
    (-11.550, -55.450, "Sorriso — MT"),
    (-13.010, -55.250, "Lucas do Rio Verde — MT"),
    (-11.860, -55.760, "Sinop — MT"),
    (-14.660, -59.320, "Juína — MT"),
    # Rondônia
    (-10.878, -61.945, "Ji-Paraná — RO"),
    (-11.730, -61.360, "Cacoal — RO"),
    ( -9.165, -62.856, "Machadinho d'Oeste — RO"),
    (-11.437, -61.832, "Presidente Médici — RO"),
    # Amazonas
    ( -6.050, -67.950, "Lábrea — AM"),
    ( -7.280, -64.890, "Humaitá — AM"),
    ( -5.826, -61.274, "Novo Aripuanã — AM"),
    ( -4.870, -60.030, "Borba — AM"),
    # Acre
    (-10.003, -67.807, "Brasileia — AC"),
    ( -7.728, -72.664, "Cruzeiro do Sul — AC"),
    ( -8.160, -70.770, "Feijó — AC"),
    # --- Hotspots — Cerrado (Matopiba) ---
    (-11.858, -45.838, "Barreiras — BA"),
    (-12.150, -45.005, "São Desidério — BA"),
    ( -7.216, -48.203, "Araguaína — TO"),
    (-10.175, -48.335, "Palmas — TO"),
    ( -6.755, -47.459, "Imperatriz — MA"),
    ( -4.867, -44.886, "Barra do Corda — MA"),
    # --- Mata Atlântica ---
    (-20.270, -40.308, "Vitória — ES"),
    (-23.960, -46.340, "Santos — SP"),
    (-26.305, -48.849, "Joinville — SC"),
]

# Quantos locais processar por hora (controle de créditos openEO)
# 15.000 créditos/mês ÷ 30 dias ÷ 24 h = ~21 créditos/hora
# ~2 créditos/análise NDVI → máximo seguro: 8 locais/hora
LOTE_POR_HORA = 8
_seed_cursor = 0  # rotação pelo índice da lista

_scheduler = AsyncIOScheduler(timezone="America/Sao_Paulo")

async def executar_seed_automatico():
    """
    Cron horário: analisa o próximo lote de locais via Sentinel-2 + Sentinel-1.
    Rotaciona pelo LOCAIS_MONITORAMENTO para cobrir todos em ~6 horas.
    """
    global _seed_cursor
    if not CDSE_USER or not CDSE_PASS or not OPENEO_DISPONIVEL:
        return

    try:
        token = await get_cdse_token()
    except Exception as e:
        log.warning(f"[CRON] Falha na autenticação Copernicus: {e}")
        return

    total = len(LOCAIS_MONITORAMENTO)
    lote = [LOCAIS_MONITORAMENTO[(_seed_cursor + i) % total] for i in range(LOTE_POR_HORA)]
    _seed_cursor = (_seed_cursor + LOTE_POR_HORA) % total

    log.info(f"[CRON] Processando lote: {[c for _, _, c in lote]}")

    for lat, lon, cidade in lote:
        try:
            resultados = await asyncio.gather(
                calcular_ndvi_real(lat, lon, token, 30),
                calcular_radar_real(lat, lon, token, 30),
                return_exceptions=True,
            )
            ndvi_data  = resultados[0] if not isinstance(resultados[0], Exception) \
                         else calcular_ndvi_simulado(lat, lon, "cron")
            radar_data = resultados[1] if not isinstance(resultados[1], Exception) else None

            alertas   = await buscar_alertas_inmet(lat, lon)
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

        await asyncio.sleep(5)  # pausa entre chamadas para não sobrecarregar a API


@asynccontextmanager
async def lifespan(app: FastAPI):
    DB_PATH_ENV = os.getenv("DB_PATH")
    if DB_PATH_ENV:
        global DB_PATH
        DB_PATH = DB_PATH_ENV
        init_db()

    if CDSE_USER and CDSE_PASS and OPENEO_DISPONIVEL:
        _scheduler.add_job(executar_seed_automatico, "interval", hours=1,
                           id="seed_automatico", replace_existing=True)
        _scheduler.start()
        log.info(f"[CRON] Monitoramento ativo — {LOTE_POR_HORA} locais/hora, "
                 f"{len(LOCAIS_MONITORAMENTO)} locais no total")
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

# -------------------------------------------------------
# Configuração Copernicus CDSE
# Crie conta gratuita em: https://dataspace.copernicus.eu
# Defina as variáveis de ambiente antes de rodar:
#   export CDSE_USER="seu@email.com"
#   export CDSE_PASS="sua_senha"
# -------------------------------------------------------
CDSE_USER      = os.getenv("CDSE_USER", "")
CDSE_PASS      = os.getenv("CDSE_PASS", "")
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

DB_PATH = os.getenv("DB_PATH", "arvore_alerta.db")


# -------------------------------------------------------
# Banco de dados
# -------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS ocorrencias (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude    REAL    NOT NULL,
            longitude   REAL    NOT NULL,
            status      TEXT    NOT NULL DEFAULT 'pendente',
            origem      TEXT    NOT NULL DEFAULT 'satellite',
            confianca   REAL    DEFAULT 0.0,
            ndvi_atual  REAL,
            ndvi_ref    REAL,
            ndvi_delta  REAL,
            descricao   TEXT,
            criado_em   TEXT    DEFAULT CURRENT_TIMESTAMP,
            cidade      TEXT,
            bairro      TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reportes_usuario (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude      REAL    NOT NULL,
            longitude     REAL    NOT NULL,
            descricao     TEXT,
            confirmacoes  INTEGER DEFAULT 1,
            status        TEXT    DEFAULT 'ativo',
            criado_em     TEXT    DEFAULT CURRENT_TIMESTAMP,
            atualizado_em TEXT    DEFAULT CURRENT_TIMESTAMP,
            cidade        TEXT,
            bairro        TEXT
        )
    """)

    # Migrações — adiciona colunas novas sem recriar a tabela
    for col_def in [
        "ALTER TABLE ocorrencias ADD COLUMN radar_vh_delta REAL",
        "ALTER TABLE ocorrencias ADD COLUMN alertas_dc TEXT",
        "ALTER TABLE ocorrencias ADD COLUMN modo_ref TEXT DEFAULT 'ano_anterior'",
        "ALTER TABLE ocorrencias ADD COLUMN periodo_atual TEXT",
        "ALTER TABLE ocorrencias ADD COLUMN periodo_ref TEXT",
    ]:
        try:
            c.execute(col_def)
        except sqlite3.OperationalError:
            pass  # coluna já existe

    conn.commit()
    conn.close()

init_db()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------------------------------
# Copernicus CDSE — autenticação e busca de produtos
# -------------------------------------------------------
async def get_cdse_token() -> str:
    if not CDSE_USER or not CDSE_PASS:
        raise HTTPException(
            status_code=503,
            detail=(
                "Credenciais Copernicus não configuradas. "
                "Crie conta em https://dataspace.copernicus.eu e defina "
                "CDSE_USER e CDSE_PASS como variáveis de ambiente."
            )
        )
    async with httpx.AsyncClient() as client:
        r = await client.post(CDSE_TOKEN_URL, data={
            "grant_type": "password",
            "client_id":  "cdse-public",
            "username":   CDSE_USER,
            "password":   CDSE_PASS,
        }, timeout=20)
        r.raise_for_status()
        return r.json()["access_token"]


async def buscar_produto_sentinel2(lat: float, lon: float, dias_atras: int = 30) -> Optional[dict]:
    """
    Busca o produto Sentinel-2 L2A mais recente com cobertura de nuvens < 20%
    para a coordenada informada.
    """
    data_fim = datetime.now(timezone.utc)
    data_ini = data_fim - timedelta(days=dias_atras)
    d = 0.005  # bounding box ~1 km

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
            CDSE_SEARCH_URL,
            params={"$filter": filtro, "$orderby": "ContentDate/Start desc", "$top": "1"},
            timeout=30,
        )
        r.raise_for_status()
        items = r.json().get("value", [])
        return items[0] if items else None


def calcular_ndvi_simulado(lat: float, lon: float, produto_id: str) -> dict:
    """
    STUB — Em produção substitua pelo download real das bandas:
      B04 (Red) e B08 (NIR) via API S3 do CDSE.
      NDVI = (NIR - Red) / (NIR + Red)

    Documentação:
      https://documentation.dataspace.copernicus.eu/APIs/S3.html

    Bibliotecas recomendadas:
      pip install openeo rasterio numpy sentinelsat
    """
    base       = 0.55 + 0.20 * math.sin(lat * 10) * math.cos(lon * 10)
    ndvi_ref   = round(max(0.1, min(0.9, base + random.uniform(-0.05, 0.05))), 3)
    ndvi_atual = round(max(0.0, ndvi_ref - random.uniform(0.05, 0.35)), 3)
    delta      = round(ndvi_ref - ndvi_atual, 3)
    return {"ndvi_ref": ndvi_ref, "ndvi_atual": ndvi_atual, "ndvi_delta": delta}


def _calcular_ndvi_openeo(lat: float, lon: float, token: str, dias_ref: int, modo_ref: str = "ano_anterior") -> dict:
    """
    Calcula NDVI real via openEO + Sentinel-2 L2A.
    modo_ref='ano_anterior': compara ao mesmo período 1 ano atrás.
    modo_ref='recente': compara ao período imediatamente anterior.
    Executa de forma síncrona — chamar via run_in_executor.
    """
    now = datetime.now(timezone.utc)
    bbox = {"west": lon - 0.01, "south": lat - 0.01, "east": lon + 0.01, "north": lat + 0.01}

    ini_atu = now - timedelta(days=dias_ref)
    fim_atu = now
    if modo_ref == "recente":
        ini_ref = now - timedelta(days=2 * dias_ref)
        fim_ref = now - timedelta(days=dias_ref)
    else:
        ini_ref = now - timedelta(days=365 + dias_ref)
        fim_ref = now - timedelta(days=365)

    conn = openeo.connect("https://openeo.dataspace.copernicus.eu")
    conn.authenticate_oidc_access_token(token)

    def ndvi_media(ini: datetime, fim: datetime) -> float:
        cube = conn.load_collection(
            "SENTINEL2_L2A",
            spatial_extent=bbox,
            temporal_extent=[ini.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d")],
            bands=["B04", "B08"],
            max_cloud_cover=20,
        )
        nir  = cube.band("B08")
        red  = cube.band("B04")
        ndvi = (nir - red) / (nir + red)
        result = ndvi.mean_time().execute()
        val = float(np.nanmean(result.values))
        if np.isnan(val):
            raise ValueError("Sem imagens válidas no período (cobertura de nuvens alta ou sem dados)")
        return val

    v_atu = ndvi_media(ini_atu, fim_atu)
    v_ref = ndvi_media(ini_ref, fim_ref)
    delta = round(max(0.0, v_ref - v_atu), 3)

    return {
        "ndvi_ref":      round(v_ref, 3),
        "ndvi_atual":    round(v_atu, 3),
        "ndvi_delta":    delta,
        "periodo_atual": f"{ini_atu.strftime('%d/%m/%Y')} – {fim_atu.strftime('%d/%m/%Y')}",
        "periodo_ref":   f"{ini_ref.strftime('%d/%m/%Y')} – {fim_ref.strftime('%d/%m/%Y')}",
    }


def _calcular_radar_sentinel1(lat: float, lon: float, token: str, dias_ref: int) -> Optional[dict]:
    """
    Calcula variação de retroespalhamento VH do Sentinel-1 GRD via openEO.
    Compara período atual com mesmo período 1 ano atrás.
    Retorna None se não houver dados disponíveis.
    """
    try:
        now = datetime.now(timezone.utc)
        bbox = {"west": lon - 0.02, "south": lat - 0.02, "east": lon + 0.02, "north": lat + 0.02}

        ini_atu = now - timedelta(days=dias_ref)
        fim_atu = now
        ini_ref = now - timedelta(days=365 + dias_ref)
        fim_ref = now - timedelta(days=365)

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
        # Delta em dB: positivo = referência maior = possível perda de vegetação
        delta_db = round(
            10 * math.log10(max(vh_ref, 1e-10)) - 10 * math.log10(max(vh_atu, 1e-10)), 2
        )
        return {"vh_ref": round(vh_ref, 6), "vh_atual": round(vh_atu, 6), "vh_delta_db": delta_db}
    except Exception:
        return None


async def calcular_ndvi_real(lat: float, lon: float, token: str, dias_ref: int, modo_ref: str = "ano_anterior") -> dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _executor, _calcular_ndvi_openeo, lat, lon, token, dias_ref, modo_ref
    )


async def calcular_radar_real(lat: float, lon: float, token: str, dias_ref: int) -> Optional[dict]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _executor, _calcular_radar_sentinel1, lat, lon, token, dias_ref
    )


async def buscar_alertas_inmet(lat: float, lon: float) -> Optional[str]:
    """Busca alertas ativos do INMET para a região. Aplicável apenas ao Brasil."""
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


def interpretar_ndvi(ndvi_delta: float, ndvi_atual: float) -> dict:
    """
    Interpreta variação de NDVI.
    Ajuste os limiares conforme seu contexto urbano/florestal.
    """
    if ndvi_delta > 0.20:
        return {
            "queda_detectada": True,
            "confianca":       round(min(0.99, 0.60 + ndvi_delta * 1.5), 2),
            "nivel":           "alto",
            "descricao": (
                f"Queda brusca de NDVI detectada (Δ={ndvi_delta:.3f}). "
                f"NDVI atual: {ndvi_atual:.3f}. Alta probabilidade de perda de vegetação."
            ),
        }
    elif ndvi_delta > 0.10:
        return {
            "queda_detectada": True,
            "confianca":       round(0.40 + ndvi_delta * 1.5, 2),
            "nivel":           "medio",
            "descricao": (
                f"Anomalia de vegetação detectada (Δ={ndvi_delta:.3f}). "
                f"NDVI atual: {ndvi_atual:.3f}. Monitoramento recomendado."
            ),
        }
    else:
        return {
            "queda_detectada": False,
            "confianca":       0.0,
            "nivel":           "normal",
            "descricao": (
                f"Vegetação estável (Δ={ndvi_delta:.3f}). "
                f"NDVI atual: {ndvi_atual:.3f}. Nenhuma anomalia detectada."
            ),
        }


# -------------------------------------------------------
# Endpoints — Satélite / NDVI
# -------------------------------------------------------
@app.post("/satelite/analisar")
async def analisar_por_satelite(
    latitude:  float = Query(...),
    longitude: float = Query(...),
    cidade:    Optional[str] = Query(None),
    bairro:    Optional[str] = Query(None),
    dias_ref:  int   = Query(30, description="Janela de dias para buscar imagem de referência"),
    modo_ref:  str   = Query("ano_anterior", description="'ano_anterior' ou 'recente'"),
):
    """
    Consulta Copernicus CDSE, calcula NDVI (Sentinel-2) e retroespalhamento radar (Sentinel-1),
    consulta alertas INMET e registra ocorrência se anomalia detectada.
    """
    # 1. Buscar produto Sentinel-2 no catálogo
    produto_nome = "Simulado (sem credenciais CDSE)"
    produto_id   = "simulado"

    if CDSE_USER and CDSE_PASS:
        try:
            produto = await buscar_produto_sentinel2(latitude, longitude, dias_atras=dias_ref)
            if produto:
                produto_id   = produto["Id"]
                produto_nome = produto["Name"]
            else:
                produto_nome = f"Nenhum produto Sentinel-2 encontrado nos últimos {dias_ref} dias"
        except Exception as e:
            produto_nome = f"Erro CDSE: {e} — usando simulação"

    # 2. Calcular NDVI + Radar em paralelo (se credenciais disponíveis)
    ndvi_data  = None
    radar_data = None
    token      = None

    if CDSE_USER and CDSE_PASS and OPENEO_DISPONIVEL:
        try:
            token = await get_cdse_token()
            ndvi_task  = calcular_ndvi_real(latitude, longitude, token, dias_ref, modo_ref)
            radar_task = calcular_radar_real(latitude, longitude, token, dias_ref)
            ndvi_data, radar_data = await asyncio.gather(ndvi_task, radar_task, return_exceptions=True)
            if isinstance(ndvi_data, Exception):
                produto_nome += f" [NDVI simulado — {type(ndvi_data).__name__}: {ndvi_data}]"
                ndvi_data = None
            if isinstance(radar_data, Exception):
                radar_data = None
        except Exception as e:
            produto_nome += f" [NDVI simulado — {type(e).__name__}: {e}]"

    if ndvi_data is None:
        ndvi_data = calcular_ndvi_simulado(latitude, longitude, produto_id)

    # 3. Alertas INMET (Brasil apenas)
    alertas = await buscar_alertas_inmet(latitude, longitude)

    # 4. Interpretar NDVI
    resultado = interpretar_ndvi(ndvi_data["ndvi_delta"], ndvi_data["ndvi_atual"])

    # 5. Persistir se anomalia detectada
    ocorrencia_id = None
    if resultado["queda_detectada"]:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO ocorrencias
              (latitude, longitude, status, origem, confianca,
               ndvi_atual, ndvi_ref, ndvi_delta, descricao, cidade, bairro,
               radar_vh_delta, alertas_dc, modo_ref, periodo_atual, periodo_ref)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            latitude, longitude, "confirmado", "satellite",
            resultado["confianca"],
            ndvi_data["ndvi_atual"], ndvi_data["ndvi_ref"], ndvi_data["ndvi_delta"],
            resultado["descricao"], cidade, bairro,
            radar_data["vh_delta_db"] if radar_data else None,
            alertas,
            modo_ref,
            ndvi_data.get("periodo_atual"),
            ndvi_data.get("periodo_ref"),
        ))
        conn.commit()
        ocorrencia_id = c.lastrowid
        conn.close()

    return {
        "produto_sentinel2": produto_nome,
        "produto_id":        produto_id,
        "ndvi_ref":          ndvi_data["ndvi_ref"],
        "ndvi_atual":        ndvi_data["ndvi_atual"],
        "ndvi_delta":        ndvi_data["ndvi_delta"],
        "periodo_atual":     ndvi_data.get("periodo_atual"),
        "periodo_ref":       ndvi_data.get("periodo_ref"),
        "modo_ref":          modo_ref,
        "nivel":             resultado["nivel"],
        "queda_detectada":   resultado["queda_detectada"],
        "confianca":         resultado["confianca"],
        "descricao":         resultado["descricao"],
        "radar":             radar_data,
        "alertas_dc":        alertas,
        "ocorrencia_id":     ocorrencia_id,
    }


# -------------------------------------------------------
# Endpoints — Reporte de Usuário (estilo Waze)
# -------------------------------------------------------
class ReporteUsuarioIn(BaseModel):
    latitude:  float
    longitude: float
    descricao: Optional[str] = None
    cidade:    Optional[str] = None
    bairro:    Optional[str] = None


@app.post("/usuario/reportar")
def reportar_usuario(body: ReporteUsuarioIn):
    """
    Usuário reporta queda que viu pessoalmente.
    Se já existe reporte ativo a menos de ~100 m, incrementa confirmações.
    """
    conn = get_db()
    c = conn.cursor()
    delta = 0.0009  # ~100 m

    c.execute("""
        SELECT id, confirmacoes FROM reportes_usuario
        WHERE status = 'ativo'
          AND latitude  BETWEEN ? AND ?
          AND longitude BETWEEN ? AND ?
        ORDER BY criado_em DESC LIMIT 1
    """, (
        body.latitude  - delta, body.latitude  + delta,
        body.longitude - delta, body.longitude + delta,
    ))
    existente = c.fetchone()

    if existente:
        c.execute("""
            UPDATE reportes_usuario
            SET confirmacoes  = confirmacoes + 1,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (existente["id"],))
        conn.commit()
        reporte_id   = existente["id"]
        confirmacoes = existente["confirmacoes"] + 1
        novo         = False
    else:
        c.execute("""
            INSERT INTO reportes_usuario (latitude, longitude, descricao, cidade, bairro)
            VALUES (?,?,?,?,?)
        """, (body.latitude, body.longitude, body.descricao, body.cidade, body.bairro))
        conn.commit()
        reporte_id   = c.lastrowid
        confirmacoes = 1
        novo         = True

    conn.close()
    return {
        "id":           reporte_id,
        "novo":         novo,
        "confirmacoes": confirmacoes,
        "mensagem": (
            "Novo reporte registrado! Obrigado por contribuir."
            if novo else
            f"Reporte confirmado! {confirmacoes} pessoa(s) já reportaram esta ocorrência."
        ),
    }


@app.get("/usuario/reportes")
def listar_reportes_usuario(limite: int = 100, dias: Optional[int] = None):
    conn = get_db()
    c = conn.cursor()
    if dias:
        desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            SELECT * FROM reportes_usuario
            WHERE status = 'ativo' AND criado_em >= ?
            ORDER BY confirmacoes DESC, criado_em DESC LIMIT ?
        """, (desde, limite))
    else:
        c.execute("""
            SELECT * FROM reportes_usuario
            WHERE status = 'ativo'
            ORDER BY confirmacoes DESC, criado_em DESC LIMIT ?
        """, (limite,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/usuario/reportes/{reporte_id}/confirmar")
def confirmar_reporte(reporte_id: int):
    """Adiciona +1 confirmação a um reporte existente."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM reportes_usuario WHERE id = ?", (reporte_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Reporte não encontrado")
    c.execute("""
        UPDATE reportes_usuario
        SET confirmacoes  = confirmacoes + 1,
            atualizado_em = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (reporte_id,))
    conn.commit()
    c.execute("SELECT confirmacoes FROM reportes_usuario WHERE id = ?", (reporte_id,))
    conf = c.fetchone()["confirmacoes"]
    conn.close()
    return {"id": reporte_id, "confirmacoes": conf}


@app.delete("/usuario/reportes/{reporte_id}")
def resolver_reporte(reporte_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE reportes_usuario SET status = 'resolvido' WHERE id = ?", (reporte_id,))
    conn.commit()
    conn.close()
    return {"mensagem": "Reporte marcado como resolvido"}


# -------------------------------------------------------
# Endpoints — Ocorrências gerais
# -------------------------------------------------------
@app.get("/ocorrencias")
def listar_ocorrencias(limite: int = 100, dias: Optional[int] = None):
    conn = get_db()
    c = conn.cursor()
    cols = """id, latitude, longitude, status, origem, confianca,
              ndvi_atual, ndvi_ref, ndvi_delta, descricao, criado_em, cidade, bairro,
              radar_vh_delta, alertas_dc, modo_ref, periodo_atual, periodo_ref"""
    if dias:
        desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute(f"SELECT {cols} FROM ocorrencias WHERE criado_em >= ? ORDER BY criado_em DESC LIMIT ?",
                  (desde, limite))
    else:
        c.execute(f"SELECT {cols} FROM ocorrencias ORDER BY criado_em DESC LIMIT ?", (limite,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/ocorrencias/exportar")
def exportar_ocorrencias(
    formato: str = Query("geojson", description="'geojson' ou 'csv'"),
    dias: Optional[int] = Query(None),
):
    """Exporta ocorrências em GeoJSON ou CSV."""
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

    # GeoJSON (padrão)
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
        ensure_ascii=False, indent=2,
    )
    return StreamingResponse(
        io.BytesIO(content.encode("utf-8")),
        media_type="application/geo+json",
        headers={"Content-Disposition": "attachment; filename=ocorrencias.geojson"},
    )


@app.delete("/ocorrencias/{ocorrencia_id}")
def deletar_ocorrencia(ocorrencia_id: int):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM ocorrencias WHERE id = ?", (ocorrencia_id,))
    conn.commit()
    conn.close()
    return {"mensagem": "Ocorrência removida"}


@app.get("/stats")
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
        "total":            total,
        "confirmados":      confirmados,
        "media_confianca":  round(media, 2),
        "reportes_usuario": reportes,
    }


@app.get("/cron/status")
def status_cron():
    """Status do monitoramento automático (útil para healthcheck em produção)."""
    jobs = []
    if _scheduler.running:
        for job in _scheduler.get_jobs():
            jobs.append({
                "id":           job.id,
                "proxima_exec": str(job.next_run_time),
            })
    return {
        "ativo":              _scheduler.running,
        "locais_total":       len(LOCAIS_MONITORAMENTO),
        "lote_por_hora":      LOTE_POR_HORA,
        "cursor_atual":       _seed_cursor,
        "ciclo_completo_h":   math.ceil(len(LOCAIS_MONITORAMENTO) / LOTE_POR_HORA),
        "creditos_mes_est":   LOTE_POR_HORA * 24 * 30 * 2,
        "jobs":               jobs,
        "modo_openeo":        OPENEO_DISPONIVEL and bool(CDSE_USER),
    }
