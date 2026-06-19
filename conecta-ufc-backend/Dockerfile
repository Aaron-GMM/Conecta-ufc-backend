FROM python:3.12-slim
RUN apt-get update && apt-get install -y build-essential libpq-dev curl && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt
COPY . .

# Executa alembic upgrade e check durante o build num banco temporário
# Usamos ARG para evitar expor variáveis no comando RUN (boa prática de segurança)
ARG DATABASE_URL=sqlite:///./build_check.db
RUN alembic upgrade head && \
    alembic check && \
    rm ./build_check.db

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
