"""
Recoloca IA — Backend Principal
FastAPI + WebSocket para comunicação em tempo real com o frontend.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, profile, data_files, applications, resume


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos na startup e limpa no shutdown."""
    # Garante que o diretório data/ existe
    data_dir = os.getenv("DATA_DIR", "../data")
    os.makedirs(data_dir, exist_ok=True)
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


@app.get("/health")
async def health():
    return {"status": "online", "agent": "Maestro"}
