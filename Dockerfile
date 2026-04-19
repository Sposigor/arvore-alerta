FROM python:3.11-slim

WORKDIR /app

# Instala dependências (separado para aproveitar cache do Docker)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    pip install --no-cache-dir fastapi "uvicorn[standard]" python-multipart \
        pydantic httpx python-dotenv "apscheduler>=3.10,<4.0"

# Copia o código do backend
COPY backend/ .

ENV PORT=8000
EXPOSE $PORT

CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port $PORT"]
