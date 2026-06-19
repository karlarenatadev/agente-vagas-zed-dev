"""
Recoloca IA — Backend Principal
FastAPI + WebSocket para comunicação em tempo real com o frontend.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
from logging_config import configure_logging, get_logger
from routers import (
    applications,
    chat,
    data_files,
    job_description,
    pdi,
    profile,
    reconciliation,
    resume,
    resume_match,
    resume_tailoring,
)


configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa recursos na startup e limpa no shutdown."""
    # Garante que o diretório data/ existe (mesmo caminho usado para todo I/O)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Backend startup concluido",
        extra={
            "event": "backend_startup",
            "data_dir": str(config.DATA_DIR),
        },
    )
    yield
    logger.info("Backend shutdown iniciado", extra={"event": "backend_shutdown"})


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
app.include_router(
    reconciliation.router,
    prefix="/api/reconciliation",
    tags=["reconciliation"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part != "body"]
        errors.append(
            {
                "field": ".".join(location) or "request",
                "message": str(error.get("msg", "Valor invalido")),
                "type": str(error.get("type", "validation_error")),
            }
        )

    logger.warning(
        "Falha de validacao na requisicao",
        extra={
            "event": "request_validation_error",
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Dados invalidos na requisicao.",
            "errors": errors,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Erro interno nao tratado",
        extra={
            "event": "unhandled_exception",
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
        },
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno no processamento. Tente novamente."},
    )


@app.get("/health")
async def health():
    return {"status": "online", "agent": "Maestro"}
