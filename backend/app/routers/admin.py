import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app import config
from app.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


def _autorizar(token: str):
    if not config.SEED_TOKEN:
        raise HTTPException(503, "SEED_TOKEN não configurado no servidor")
    if token != config.SEED_TOKEN:
        raise HTTPException(401, "token inválido")


@router.post("/seed-fake")
def seed_fake(
    token: str = Query(..., description="Token de autorização (env SEED_TOKEN)"),
    n: int = Query(80, ge=1, le=500, description="Quantidade de ocorrências a gerar"),
    dias: int = Query(180, ge=30, le=730, description="Espalhar nos últimos N dias"),
):
    """
    Gera ocorrências simuladas para apresentação.
    Marcadas com origem='seed_fake' — fáceis de remover depois com DELETE /admin/seed-fake.
    """
    _autorizar(token)

    locais = config.LOCAIS_MONITORAMENTO
    if not locais:
        raise HTTPException(500, "LOCAIS_MONITORAMENTO vazio")

    conn = get_db()
    c = conn.cursor()
    inseridos = 0
    agora = datetime.now(timezone.utc)

    for _ in range(n):
        lat0, lon0, cidade = random.choice(locais)
        # Pequeno jitter pra não colidir UNIQUE em (lat, lon, periodo_atual)
        lat = round(lat0 + random.uniform(-0.05, 0.05), 5)
        lon = round(lon0 + random.uniform(-0.05, 0.05), 5)

        delta = round(random.uniform(0.10, 0.42), 3)
        ndvi_atu = round(random.uniform(0.20, 0.55), 3)
        ndvi_ref = round(min(0.95, ndvi_atu + delta), 3)

        if delta > 0.20:
            nivel = "alto"
            conf_ndvi = round(min(0.99, 0.60 + delta * 1.5), 2)
        else:
            nivel = "medio"
            conf_ndvi = round(0.40 + delta * 1.5, 2)

        focos = random.choices([0, 0, 0, 1, 2, 5, 12], weights=[40, 20, 10, 10, 8, 7, 5])[0]
        deter = random.choices([0, 0, 1, 2], weights=[60, 20, 12, 8])[0]
        radar_db = round(random.uniform(-3.5, 3.5), 2) if random.random() < 0.7 else None

        bonus = 0.0
        fontes = []
        if focos > 0:
            bonus += 0.10
            fontes.append(f"FIRMS ({focos} focos)")
        if deter > 0:
            bonus += 0.15
            fontes.append(f"DETER/INPE ({deter} alertas)")
        if radar_db is not None and abs(radar_db) > 2:
            bonus += 0.05
            fontes.append(f"Radar S1 (Δ={radar_db:+.2f} dB)")
        confianca = round(min(0.99, conf_ndvi + bonus), 2)

        descricao = (
            f"Queda {'brusca ' if nivel == 'alto' else ''}de NDVI detectada (Δ={delta:.3f}). "
            f"NDVI atual: {ndvi_atu:.3f}."
        )
        if fontes:
            descricao += " Corroborado por: " + ", ".join(fontes) + "."

        dias_atras = random.randint(0, dias)
        fim = agora - timedelta(days=dias_atras)
        ini = fim - timedelta(days=30)
        periodo_atual = f"{ini.strftime('%d/%m/%Y')} – {fim.strftime('%d/%m/%Y')}"
        periodo_ref = (
            f"{(ini - timedelta(days=365)).strftime('%d/%m/%Y')} – "
            f"{(fim - timedelta(days=365)).strftime('%d/%m/%Y')}"
        )

        try:
            c.execute("""
                INSERT OR IGNORE INTO ocorrencias
                  (latitude, longitude, status, origem, confianca,
                   ndvi_atual, ndvi_ref, ndvi_delta, descricao, cidade,
                   radar_vh_delta, modo_ref, periodo_atual, periodo_ref,
                   focos_fogo, deter_alertas, criado_em)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                lat, lon, "confirmado", "seed_fake", confianca,
                ndvi_atu, ndvi_ref, delta, descricao, cidade,
                radar_db, "ano_anterior", periodo_atual, periodo_ref,
                focos, deter,
                fim.strftime("%Y-%m-%d %H:%M:%S"),
            ))
            if c.rowcount > 0:
                inseridos += 1
        except Exception:
            pass

    conn.commit()
    c.execute("SELECT COUNT(*) FROM ocorrencias WHERE origem='seed_fake'")
    total_fake = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ocorrencias")
    total = c.fetchone()[0]
    conn.close()

    return {
        "inseridos": inseridos,
        "tentados": n,
        "total_fake_no_banco": total_fake,
        "total_ocorrencias": total,
    }


@router.delete("/seed-fake")
def remover_seed_fake(token: str = Query(...)):
    """Remove todas as ocorrências com origem='seed_fake'."""
    _autorizar(token)
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM ocorrencias WHERE origem='seed_fake'")
    removidos = c.rowcount
    conn.commit()
    conn.close()
    return {"removidos": removidos}
