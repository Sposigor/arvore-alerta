#!/usr/bin/env python3
"""
Seed histórico — amostragem trimestral dos últimos 2 anos para os 50 locais
curados em app/config.py (capitais, hotspots de desmatamento, Mata Atlântica).

Execute:
    python seed_real.py                                     # usa localhost:8000
    API=https://<host>.up.railway.app python seed_real.py   # aponta pra produção

Configurações via env:
    API              URL do backend (default http://localhost:8000)
    ANOS             anos de histórico (default 2)
    DIAS_REF         janela de dias por snapshot (default 30)
    MAX_LOCAIS       limita nº de locais (debug)
    PAUSA_S          segundos entre chamadas (default 20 — evita rate-limit CDSE)

Cada snapshot chama POST /satelite/analisar?data_fim=YYYY-MM-DD.
Cada chamada leva 60-180 s. Total estimado: 50 × 8 = 400 chamadas (~12-20 h).
"""
import os
import sys
import time
from datetime import date, timedelta

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import LOCAIS_MONITORAMENTO  # noqa: E402

API = os.getenv("API", "http://localhost:8000").rstrip("/")
ANOS = int(os.getenv("ANOS", "2"))
DIAS_REF = int(os.getenv("DIAS_REF", "30"))
MAX_LOCAIS = int(os.getenv("MAX_LOCAIS", "0"))
PAUSA_S = float(os.getenv("PAUSA_S", "20"))


def datas_trimestrais(anos: int) -> list[date]:
    """Retorna datas finais de janela, espaçadas 90 dias, cobrindo N anos."""
    hoje = date.today()
    passos = anos * 4
    return [hoje - timedelta(days=90 * i) for i in range(passos)]


def seed():
    locais = LOCAIS_MONITORAMENTO
    if MAX_LOCAIS > 0:
        locais = locais[:MAX_LOCAIS]

    datas = datas_trimestrais(ANOS)
    total = len(locais) * len(datas)
    print(f"{len(locais)} locais × {len(datas)} trimestres = {total} análises")
    print(f"Pausa entre chamadas: {PAUSA_S}s | Janela: {DIAS_REF}d")
    print(f"Estimativa: {total * 90 / 3600:.1f}h (média 90s por call)\n")

    ok = err = detectadas = 0
    i = 0

    for lat, lon, cidade in locais:
        for data_fim in datas:
            i += 1
            prefixo = f"[{i:04d}/{total}] {cidade[:25]:<25} {data_fim.isoformat()}"
            try:
                r = httpx.post(
                    f"{API}/satelite/analisar",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "cidade": cidade,
                        "dias_ref": DIAS_REF,
                        "data_fim": data_fim.isoformat(),
                    },
                    timeout=300,
                )
                r.raise_for_status()
                d = r.json()
                if d.get("queda_detectada"):
                    detectadas += 1
                    print(
                        f"{prefixo} | QUEDA {d['nivel'].upper():<5} "
                        f"Δ={d['ndvi_delta']:.3f} conf={d['confianca']:.0%} "
                        f"fogo={d.get('focos_fogo')} deter={d.get('deter_alertas')}"
                    )
                else:
                    print(f"{prefixo} | normal Δ={d['ndvi_delta']:.3f}")
                ok += 1
            except Exception as e:
                print(f"{prefixo} | ERRO {type(e).__name__}: {e}")
                err += 1

            if i < total:
                time.sleep(PAUSA_S)

    print(f"\nConcluído: {ok} ok | {err} erro | {detectadas} quedas detectadas")


if __name__ == "__main__":
    print(f"Backend: {API}")
    try:
        httpx.get(f"{API}/stats", timeout=10).raise_for_status()
    except Exception as e:
        print(f"Erro: backend não respondeu em {API}: {e}")
        sys.exit(1)

    seed()
