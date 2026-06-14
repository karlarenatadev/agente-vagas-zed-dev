"""
Recoloca IA — Backend Principal
FastAPI + WebSocket para comunicação em tempo real com o frontend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import (
    applications,
    chat,
    data_files,
    job_description,
    pdi,
    profile,
    resume,
    resume_match,
    resume_tailoring,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos na startup e limpa no shutdown."""
    # Garante que o diretório data/ existe (mesmo caminho usado para todo I/O)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Recoloca IA",
    description="Sistema multi-agente de desenvolvimento de carreira",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/ws", tags=["websocket"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(data_files.router, prefix="/api/data", tags=["data"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(resume.router, prefix="/api/resume", tags=["resume"])
app.include_router(
    job_description.router,
    prefix="/api/job-description",
    tags=["job-description"],
)
app.include_router(
    resume_match.router,
    prefix="/api/resume-match",
    tags=["resume-match"],
)
app.include_router(
    resume_tailoring.router,
    prefix="/api/resume-tailoring",
    tags=["resume-tailoring"],
)
app.include_router(pdi.router, prefix="/api/pdi", tags=["pdi"])


@app.get("/health")
async def health():
    return {"status": "online", "agent": "Maestro"}
