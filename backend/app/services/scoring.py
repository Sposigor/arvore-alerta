"""
Score multi-sinal — funde evidências independentes para reforçar a confiança
quando múltiplas fontes concordam sobre uma anomalia de vegetação.

Sinais considerados (pesos escolhidos a partir da confiabilidade relativa
da fonte para detecção de perda de cobertura vegetal):

    FIRMS (fogo, VIIRS)    +0.10   evidência correlacional (queimada → queda NDVI)
    DETER (INPE, polígono) +0.15   evidência oficial, ground-truth brasileiro
    Radar Sentinel-1 (VH)  +0.05   evidência estrutural (independente de nuvens)

Confiança final é truncada em 0.99 para preservar margem de incerteza.
"""
from typing import Optional

BONUS_FIRMS = 0.10
BONUS_DETER = 0.15
BONUS_RADAR = 0.05
LIMIAR_RADAR_DB = 2.0


def fortalecer_confianca(
    base: float,
    focos_fogo: Optional[int],
    deter_alertas: Optional[int],
    radar_vh_delta_db: Optional[float],
) -> tuple[float, list[str]]:
    """
    Aplica bônus à confiança base e retorna (nova_confianca, fontes_corroborantes).
    """
    conf = base
    fontes: list[str] = []

    if focos_fogo and focos_fogo > 0:
        conf += BONUS_FIRMS
        fontes.append(f"FIRMS ({focos_fogo} foco{'s' if focos_fogo > 1 else ''})")

    if deter_alertas and deter_alertas > 0:
        conf += BONUS_DETER
        fontes.append(f"DETER/INPE ({deter_alertas} alerta{'s' if deter_alertas > 1 else ''})")

    if radar_vh_delta_db is not None and abs(radar_vh_delta_db) > LIMIAR_RADAR_DB:
        conf += BONUS_RADAR
        fontes.append(f"Radar S1 (Δ={radar_vh_delta_db:+.1f} dB)")

    return round(min(0.99, conf), 2), fontes
