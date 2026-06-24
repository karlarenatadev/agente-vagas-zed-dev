# Backend (FastAPI) — imagem de produção.
#
# IMPORTANTE: o contexto de build precisa ser a RAIZ do repositório, não a
# pasta backend/. O config.py resolve personas/, skills/ e data/ em
# PROJECT_ROOT (dois níveis acima de backend/config.py), então a imagem precisa
# conter essas pastas irmãs. O docker-compose.yml já usa `context: .`.
#
#   docker build -f backend/Dockerfile -t import-vagas-backend .
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app/backend

# curl é usado apenas pelo HEALTHCHECK. Camada isolada e cache de apt limpo.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Dependências primeiro, para aproveitar o cache de camadas do Docker.
# As versões de requirements.txt têm wheels para cp312 (sem compilação).
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r requirements.txt

# Código da aplicação + recursos compartilhados (personas e skills).
# backend/.env e caches são excluídos pelo .dockerignore.
COPY backend/ /app/backend/
COPY personas/ /app/personas/
COPY skills/ /app/skills/

# Usuário sem privilégios. /app/data e /app/logs criados e com dono correto
# para que o volume nomeado herde a permissão de escrita do appuser.
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/data /app/logs \
    && chown -R appuser:appuser /app
USER appuser

# Caminhos absolutos no container (o compose também os define; aqui garante
# que a imagem funcione mesmo sem o compose).
ENV DATA_DIR=/app/data \
    PERSONAS_DIR=/app/personas \
    SKILLS_DIR=/app/skills \
    LOG_DIR=/app/logs \
    LOG_FILE=/app/logs/backend.log

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

# Produção: sem --reload, ouvindo em todas as interfaces do container.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
