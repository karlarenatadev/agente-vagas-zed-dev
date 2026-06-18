"""Router de candidaturas: CRUD persistido em applications.json."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from logging_config import get_logger
from session import (
    SessionPaths,
    get_session_lock,
    get_session_paths,
    read_text_async,
    write_text_atomic_async,
)


router = APIRouter()
logger = get_logger(__name__)


class ApplicationCreate(BaseModel):
    titulo: str
    empresa: str
    localizacao: str
    link: str
    salario: Optional[str] = None
    habilidades_correspondentes: Optional[str] = None
    habilidades_faltantes: Optional[str] = None
    contagem_correspondencia: Optional[str] = None
    status: str = "salva"
    notas: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notas: Optional[str] = None
    data_aplicacao: Optional[str] = None


async def _load(path: Path, session_id: str) -> list[dict[str, Any]]:
    try:
        content = await read_text_async(path)
        if not content.strip():
            return []

        payload = json.loads(content)
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        logger.error(
            "Formato invalido em applications.json",
            extra={
                "event": "applications_invalid_payload",
                "session_id": session_id,
                "path": str(path),
                "payload_type": type(payload).__name__,
            },
        )
        return []
    except json.JSONDecodeError as exc:
        logger.exception(
            "JSON invalido ao carregar candidaturas",
            extra={
                "event": "applications_json_decode_error",
                "session_id": session_id,
                "path": str(path),
                "error_type": type(exc).__name__,
            },
        )
        return []
    except OSError:
        logger.exception(
            "Falha ao carregar candidaturas",
            extra={
                "event": "applications_load_error",
                "session_id": session_id,
                "path": str(path),
            },
        )
        raise


async def _save(data: list[dict[str, Any]], path: Path, session_id: str) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    try:
        await write_text_atomic_async(path, payload)
    except OSError:
        logger.exception(
            "Falha ao salvar candidaturas",
            extra={
                "event": "applications_save_error",
                "session_id": session_id,
                "path": str(path),
                "item_count": len(data),
            },
        )
        raise


@router.get("/")
async def list_applications(
    paths: SessionPaths = Depends(get_session_paths),
) -> list[dict[str, Any]]:
    """Lista todas as candidaturas, ordenadas por data recente."""
    apps = await _load(paths.APPLICATIONS_FILE, paths.session_id)
    apps.sort(key=lambda item: str(item.get("data_salva", "")), reverse=True)
    return apps


@router.post("/")
async def create_application(
    body: ApplicationCreate,
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    """Salva uma nova candidatura."""
    async with get_session_lock(paths.session_id):
        apps = await _load(paths.APPLICATIONS_FILE, paths.session_id)
        new_app = {
            "id": str(uuid.uuid4()),
            "data_salva": datetime.now().isoformat(),
            **body.model_dump(),
        }
        apps.append(new_app)
        await _save(apps, paths.APPLICATIONS_FILE, paths.session_id)
    return new_app


@router.patch("/{app_id}")
async def update_application(
    app_id: str,
    body: ApplicationUpdate,
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    """Atualiza status, notas ou data de aplicacao."""
    async with get_session_lock(paths.session_id):
        apps = await _load(paths.APPLICATIONS_FILE, paths.session_id)
        for app in apps:
            if app.get("id") == app_id:
                if body.status is not None:
                    app["status"] = body.status
                    if body.status == "aplicada" and not app.get("data_aplicacao"):
                        app["data_aplicacao"] = datetime.now().isoformat()
                if body.notas is not None:
                    app["notas"] = body.notas
                if body.data_aplicacao is not None:
                    app["data_aplicacao"] = body.data_aplicacao
                await _save(apps, paths.APPLICATIONS_FILE, paths.session_id)
                return app
    raise HTTPException(status_code=404, detail="Candidatura nao encontrada")


@router.delete("/{app_id}")
async def delete_application(
    app_id: str,
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, bool]:
    """Remove uma candidatura."""
    async with get_session_lock(paths.session_id):
        apps = await _load(paths.APPLICATIONS_FILE, paths.session_id)
        filtered = [app for app in apps if app.get("id") != app_id]
        if len(filtered) == len(apps):
            raise HTTPException(status_code=404, detail="Candidatura nao encontrada")
        await _save(filtered, paths.APPLICATIONS_FILE, paths.session_id)
    return {"ok": True}


@router.get("/stats")
async def get_stats(
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    """Retorna contagens por status para o dashboard."""
    apps = await _load(paths.APPLICATIONS_FILE, paths.session_id)
    stats: dict[str, int] = {}
    for app in apps:
        status = str(app.get("status", "salva"))
        stats[status] = stats.get(status, 0) + 1
    return {"total": len(apps), "by_status": stats}
