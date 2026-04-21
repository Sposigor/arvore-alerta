import os
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()

CDSE_USER = os.getenv("CDSE_USER", "")
CDSE_PASS = os.getenv("CDSE_PASS", "")
CDSE_TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
CDSE_SEARCH_URL = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"

DB_PATH = os.getenv("DB_PATH", "arvore_alerta.db")

FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY", "")

LOTE_POR_HORA = 8

try:
    import openeo  # noqa: F401
    import numpy  # noqa: F401
    OPENEO_DISPONIVEL = True
except ImportError:
    OPENEO_DISPONIVEL = False

executor = ThreadPoolExecutor(max_workers=2)

# Fonte: PRODES/DETER (INPE) — principais focos de desmatamento e maiores cidades brasileiras
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
    ( -7.530, -55.030, "Altamira — PA"),
    ( -7.093, -55.110, "Novo Progresso — PA"),
    ( -6.638, -51.955, "São Félix do Xingu — PA"),
    ( -3.380, -53.050, "Rurópolis — PA"),
    ( -5.450, -55.430, "Trairão — PA"),
    ( -4.810, -53.770, "Placas — PA"),
    ( -6.200, -55.530, "Itaituba — PA"),
    ( -9.977, -58.200, "Colniza — MT"),
    (-10.370, -58.020, "Alta Floresta — MT"),
    (-11.550, -55.450, "Sorriso — MT"),
    (-13.010, -55.250, "Lucas do Rio Verde — MT"),
    (-11.860, -55.760, "Sinop — MT"),
    (-14.660, -59.320, "Juína — MT"),
    (-10.878, -61.945, "Ji-Paraná — RO"),
    (-11.730, -61.360, "Cacoal — RO"),
    ( -9.165, -62.856, "Machadinho d'Oeste — RO"),
    (-11.437, -61.832, "Presidente Médici — RO"),
    ( -6.050, -67.950, "Lábrea — AM"),
    ( -7.280, -64.890, "Humaitá — AM"),
    ( -5.826, -61.274, "Novo Aripuanã — AM"),
    ( -4.870, -60.030, "Borba — AM"),
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
