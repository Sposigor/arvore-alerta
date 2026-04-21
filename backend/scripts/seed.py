#!/usr/bin/env python3
"""
Seed simulado — mesma estrutura do seed_real.py, mas gera dados sintéticos
localmente (sem CDSE/FIRMS/DETER). Usa os 50 locais curados em app/config.py
e amostragem trimestral. Útil para demo, dev e testes de UI.

Execute (na pasta backend/):
    python scripts/seed.py

Configurações via env:
    ANOS          anos de histórico (default 2)
    DIAS_REF      janela em dias de cada snapshot (default 30)
    MAX_LOCAIS    limita nº de locais (debug)
"""
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import LOCAIS_MONITORAMENTO  # noqa: E402
from app.database import get_db, init_db  # noqa: E402
from app.services.ndvi import calcular_ndvi_simulado, interpretar_ndvi  # noqa: E402
from app.services.scoring import fortalecer_confianca  # noqa: E402

ANOS = int(os.getenv("ANOS", "2"))
DIAS_REF = int(os.getenv("DIAS_REF", "30"))
MAX_LOCAIS = int(os.getenv("MAX_LOCAIS", "0"))


def datas_trimestrais(anos: int) -> list[datetime]:
    hoje = datetime.now(timezone.utc)
    return [hoje - timedelta(days=90 * i) for i in range(anos * 4)]


def periodos(data_fim: datetime, dias_ref: int) -> tuple[str, str]:
    ini_atu = data_fim - timedelta(days=dias_ref)
    fim_ref = data_fim - timedelta(days=365)
    ini_ref = fim_ref - timedelta(days=dias_ref)
    return (
        f"{ini_atu.strftime('%d/%m/%Y')} – {data_fim.strftime('%d/%m/%Y')}",
        f"{ini_ref.strftime('%d/%m/%Y')} – {fim_ref.strftime('%d/%m/%Y')}",
    )


def simular_fontes() -> tuple[int, int, float | None, int]:
    focos = random.randint(1, 8) if random.random() < 0.30 else 0
    deter = random.randint(1, 3) if random.random() < 0.20 else 0
    radar = round(random.uniform(-5.0, -2.1), 1) if random.random() < 0.35 else None
    alertas_inmet = random.randint(1, 2) if random.random() < 0.15 else 0
    return focos, deter, radar, alertas_inmet


def seed():
    locais = LOCAIS_MONITORAMENTO
    if MAX_LOCAIS > 0:
        locais = locais[:MAX_LOCAIS]

    datas = datas_trimestrais(ANOS)
    total = len(locais) * len(datas)
    print(f"{len(locais)} locais × {len(datas)} trimestres = {total} snapshots simulados")
    print(f"Janela: {DIAS_REF}d | Modo ref: ano_anterior\n")

    init_db()
    conn = get_db()
    c = conn.cursor()
    inseridas = ignoradas = sem_queda = 0

    for lat, lon, cidade in locais:
        for data_fim in datas:
            dlat = random.uniform(-0.02, 0.02)
            dlon = random.uniform(-0.02, 0.02)
            lat_amostra = round(lat + dlat, 6)
            lon_amostra = round(lon + dlon, 6)

            ndvi_data = calcular_ndvi_simulado(lat_amostra, lon_amostra, "simulado")
            resultado = interpretar_ndvi(ndvi_data["ndvi_delta"], ndvi_data["ndvi_atual"])
            if not resultado["queda_detectada"]:
                sem_queda += 1
                continue

            focos, deter, radar_delta, alertas_inmet = simular_fontes()
            confianca_final, fontes = fortalecer_confianca(
                resultado["confianca"], focos, deter, radar_delta,
            )
            if fontes:
                resultado["descricao"] += " Corroborado por: " + ", ".join(fontes) + "."

            periodo_atual, periodo_ref = periodos(data_fim, DIAS_REF)
            criado = data_fim.strftime("%Y-%m-%d %H:%M:%S")

            c.execute("""
                INSERT OR IGNORE INTO ocorrencias
                  (latitude, longitude, status, origem, confianca,
                   ndvi_atual, ndvi_ref, ndvi_delta, descricao, cidade, bairro,
                   radar_vh_delta, alertas_dc, modo_ref, periodo_atual, periodo_ref,
                   focos_fogo, deter_alertas, criado_em)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                lat_amostra, lon_amostra, "confirmado", "satellite",
                confianca_final,
                ndvi_data["ndvi_atual"], ndvi_data["ndvi_ref"], ndvi_data["ndvi_delta"],
                resultado["descricao"], cidade, None,
                radar_delta, alertas_inmet, "ano_anterior", periodo_atual, periodo_ref,
                focos, deter, criado,
            ))
            if c.rowcount > 0:
                inseridas += 1
            else:
                ignoradas += 1

    conn.commit()
    conn.close()
    print(f"Concluído: {inseridas} inseridas | {ignoradas} ignoradas (duplicatas) | {sem_queda} sem queda")


if __name__ == "__main__":
    seed()
