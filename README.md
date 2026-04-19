# ArvoreAlerta v2.0

Sistema de detecção e mapeamento de quedas de árvores utilizando imagens de satélite Sentinel-2 (Copernicus CDSE) e processamento de índice de vegetação NDVI.

**Stack:** FastAPI · SQLite · Leaflet.js · openEO · Copernicus CDSE (Sentinel-2 L2A)

---

## Sobre o Projeto

ArvoreAlerta é um sistema web que detecta automaticamente possíveis quedas de árvores a partir da análise de imagens de satélite. O sistema compara o índice de vegetação NDVI de um ponto geográfico em dois períodos distintos — se houver queda brusca, uma ocorrência é registrada com nível de confiança.

O projeto foi desenvolvido como Trabalho de Conclusão de Curso (TCC) e demonstra a viabilidade de usar dados públicos e gratuitos do programa Copernicus (ESA/União Europeia) para monitoramento ambiental urbano.

---

## Estrutura do Projeto

```
projeto_tcc/
├── backend/
│   ├── main.py              # API FastAPI — lógica principal
│   ├── requirements.txt     # Dependências Python
│   ├── .env.example         # Template de credenciais (versionar)
│   ├── .env                 # Credenciais reais (não versionar — criar a partir do .env.example)
│   ├── arvore_alerta.db     # Banco SQLite (criado automaticamente, não versionar)
│   └── scripts/
│       ├── seed.py          # Popula banco com dados simulados (demo)
│       └── seed_real.py     # Popula banco com NDVI real via Copernicus
├── frontend/
│   └── index.html           # Interface web (mapa + análise NDVI)
├── .gitignore
└── README.md
```

---

## Pré-requisitos

- **Python 3.9+**
- **Conta Copernicus CDSE** — gratuita, sem cartão de crédito
  - Cadastro: https://dataspace.copernicus.eu
  - Dá acesso a imagens Sentinel-2 dos últimos 2 anos e 15.000 créditos openEO/mês

---

## Tutorial de Instalação

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd projeto_tcc
```

### 2. Criar ambiente virtual Python

```bash
cd backend
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciais Copernicus

```bash
cd backend
cp .env.example .env
# Edite .env com seu editor preferido e preencha suas credenciais
```

> Sem o `.env`, o sistema roda em **modo simulado** — todos os valores de NDVI são gerados aleatoriamente. Útil para testar a interface sem conta Copernicus.

### 5. Iniciar o backend

```bash
# Na pasta backend/
uvicorn main:app --reload --port 8000
```

API disponível em: http://localhost:8000  
Documentação interativa (Swagger): http://localhost:8000/docs

### 6. Iniciar o frontend

Em outro terminal:

```bash
cd frontend
python -m http.server 3000
```

Acesse: http://localhost:3000

### 7. Popular o banco de dados

**Dados simulados** (rápido, sem conta Copernicus):
```bash
cd backend
python scripts/seed.py
```

**Dados reais via Copernicus** (requer `.env` configurado e backend rodando):
```bash
cd backend
python scripts/seed_real.py
# Processa ~29 cidades. Cada ponto leva 60–120 s.
```

---

## Como Usar

1. **Selecionar período** — o seletor no topo do painel filtra as ocorrências exibidas no mapa (15 dias até 1 ano)
2. **Analisar um ponto** — clique em qualquer lugar do mapa para preencher as coordenadas, ajuste a janela de referência NDVI e clique em **Consultar Sentinel-2**
3. **Ver detalhes** — clique em qualquer marcador ou card da lista para abrir o painel de detalhes com as barras de NDVI
4. **Filtrar por severidade** — botões **Todos / Alto / Médio** acima da lista atualizam o mapa e a listagem simultaneamente
5. **Expandir mapa** — o botão `‹` na borda do painel recolhe a sidebar

---

## Como o NDVI funciona

O NDVI (Normalized Difference Vegetation Index) mede a densidade e saúde da vegetação a partir de imagens de satélite.

```
NDVI = (NIR - Red) / (NIR + Red)

  NIR = Banda B08 do Sentinel-2 (infravermelho próximo, 842 nm)
  Red = Banda B04 do Sentinel-2 (vermelho visível, 665 nm)
```

**Interpretação dos valores:**

| NDVI | Significado |
|------|-------------|
| > 0.5 | Vegetação densa e saudável |
| 0.2 – 0.5 | Vegetação moderada |
| 0.0 – 0.2 | Solo exposto ou vegetação esparsa |
| < 0.0 | Água, nuvens ou superfícies artificiais |

**Detecção de queda:**

O sistema compara o NDVI do período atual com o mesmo período do ano anterior. Uma queda brusca indica perda de cobertura vegetal.

| Δ NDVI | Nível | Confiança |
|--------|-------|-----------|
| > 0.20 | Alto | 60–99% |
| 0.10 – 0.20 | Médio | 40–60% |
| ≤ 0.10 | Normal | — |

---

## API REST

### Por que uma API?

A API é a camada central do sistema. Ela orquestra três responsabilidades distintas:

1. **Integração com o Copernicus CDSE** — autentica via OAuth2, consulta o catálogo OData para encontrar cenas Sentinel-2 recentes com cobertura de nuvens < 20%, e processa as bandas via openEO
2. **Cálculo e persistência** — interpreta o NDVI calculado, classifica o nível de alerta e persiste ocorrências no banco SQLite
3. **Servir dados ao frontend** — expõe endpoints REST consumidos pelo mapa Leaflet em tempo real

Separar a API do frontend permite que qualquer outra interface (app mobile, painel municipal, script de automação) consuma os mesmos dados sem duplicar a lógica de negócio.

### Endpoints

#### Análise por Satélite

| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/satelite/analisar` | Consulta Sentinel-2, calcula NDVI e registra se anomalia |

**Parâmetros (query string):**

| Parâmetro | Tipo | Obrigatório | Descrição |
|-----------|------|-------------|-----------|
| `latitude` | float | Sim | Latitude do ponto |
| `longitude` | float | Sim | Longitude do ponto |
| `cidade` | string | Não | Nome da cidade/bairro |
| `dias_ref` | int | Não (padrão: 30) | Janela de referência NDVI em dias |

**Exemplo de resposta:**
```json
{
  "produto_sentinel2": "S2B_MSIL2A_20260418...",
  "ndvi_ref": 0.631,
  "ndvi_atual": 0.312,
  "ndvi_delta": 0.319,
  "nivel": "alto",
  "queda_detectada": true,
  "confianca": 0.88,
  "descricao": "Queda brusca de NDVI detectada (Δ=0.319). NDVI atual: 0.312.",
  "ocorrencia_id": 42
}
```

#### Ocorrências

| Método | Rota | Parâmetros | Descrição |
|--------|------|------------|-----------|
| `GET` | `/ocorrencias` | `?dias=30&limite=100` | Lista ocorrências filtradas por período |
| `DELETE` | `/ocorrencias/{id}` | — | Remove uma ocorrência |

#### Estatísticas

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/stats` | Total de ocorrências, confirmados e confiança média |

**Exemplo `/stats`:**
```json
{
  "total": 53,
  "confirmados": 53,
  "media_confianca": 0.79,
  "reportes_usuario": 0
}
```

---

## Modos de Operação

| Modo | Configuração | NDVI | Uso |
|------|-------------|------|-----|
| **Simulado** | Sem `.env` | Gerado aleatoriamente | Testes locais, demo de interface |
| **Real** | Com `.env` + openEO | Calculado do Sentinel-2 | Produção, TCC com dados reais |

O sistema detecta automaticamente qual modo usar. Se as credenciais estiverem configuradas e o pacote `openeo` instalado, usa dados reais com fallback automático para simulação em caso de erro (ex: nuvens, sem imagens no período).

---

## Custos da API Copernicus

| Recurso | Limite gratuito |
|---------|----------------|
| Busca no catálogo (OData/STAC) | Ilimitado |
| Download de bandas via S3 | 12 TB/mês |
| Processamento openEO | 15.000 créditos/mês |

**Para este projeto:** o consumo típico é de ~2 créditos openEO por análise. O free tier cobre milhares de consultas mensais.

---

## Solução de Problemas

**Backend não conecta ao Copernicus:**
```
Verifique se CDSE_USER e CDSE_PASS estão corretos no .env
Teste a autenticação: python -c "from dotenv import load_dotenv; load_dotenv(); import os, httpx; r = httpx.post('https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token', data={'grant_type':'password','client_id':'cdse-public','username':os.getenv('CDSE_USER'),'password':os.getenv('CDSE_PASS')}); print(r.status_code)"
```

**NDVI retorna simulado mesmo com credenciais:**
```
Verifique se openeo e numpy estão instalados: pip install openeo numpy
A resposta da API inclui o motivo no campo "produto_sentinel2"
```

**Frontend não conecta ao backend:**
```
Confirme que o backend está rodando em http://localhost:8000
Verifique erros no console do navegador (F12)
```

**Nenhuma imagem Sentinel-2 encontrada:**
```
A região pode ter cobertura de nuvens > 20% no período
Aumente a janela de referência NDVI para 60 ou 90 dias
Regiões de alta nebulosidade (ex: Amazônia na estação chuvosa) podem não ter dados
```

---

## Roadmap

- [x] Cálculo de NDVI com dados reais via openEO
- [x] Heatmap de densidade de ocorrências
- [x] Filtro por período e severidade
- [x] Clustering de marcadores no mapa
- [x] Painel de detalhes por ocorrência
- [x] Exportação GeoJSON / CSV
- [x] Comparação ano a ano (mesmo período safra anterior)
- [x] Integração com API de alertas da Defesa Civil (INMET)
- [x] Análise com Radar Sentinel-1 (ignora cobertura de nuvens)
- [ ] Notificações push por área de interesse
- [ ] App mobile (PWA)
