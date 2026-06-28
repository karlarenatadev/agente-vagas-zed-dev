"""Router de candidaturas: CRUD persistido em applications.json."""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AnyHttpUrl, BaseModel, Field, TypeAdapter, ValidationError, field_validator

from logging_config import get_logger
from session import (
    SessionPaths,
    get_session_lock,
    get_session_paths,
    write_text_atomic_async,
)


router = APIRouter()
logger = get_logger(__name__)

_HTTP_URL_ADAPTER = TypeAdapter(AnyHttpUrl)

TITLE_MAX_LENGTH = 200
COMPANY_MAX_LENGTH = 200
LOCATION_MAX_LENGTH = 200
LINK_MAX_LENGTH = 2048
SALARY_MAX_LENGTH = 120
SKILLS_MAX_LENGTH = 2000
MATCH_COUNT_MAX_LENGTH = 120
NOTES_MAX_LENGTH = 5000
APPLICATION_DATE_MAX_LENGTH = 64


class ApplicationStatus(str, Enum):
    SALVA = "salva"
    APLICADA = "aplicada"
    EM_PROCESSO = "em_processo"
    ENTREVISTA = "entrevista"
    OFERTA = "oferta"
    RECUSADA = "recusada"
    DESISTIU = "desistiu"


class ApplicationCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    empresa: str = Field(min_length=1, max_length=COMPANY_MAX_LENGTH)
    localizacao: str = Field(min_length=1, max_length=LOCATION_MAX_LENGTH)
    link: str = Field(default="", max_length=LINK_MAX_LENGTH)
    salario: Optional[str] = Field(default=None, max_length=SALARY_MAX_LENGTH)
    habilidades_correspondentes: Optional[str] = Field(
        default=None,
        max_length=SKILLS_MAX_LENGTH,
    )
    habilidades_faltantes: Optional[str] = Field(
        default=None,
        max_length=SKILLS_MAX_LENGTH,
    )
    contagem_correspondencia: Optional[str] = Field(
        default=None,
        max_length=MATCH_COUNT_MAX_LENGTH,
    )
    status: ApplicationStatus = ApplicationStatus.SALVA
    notas: Optional[str] = Field(default=None, max_length=NOTES_MAX_LENGTH)

    @field_validator("titulo", "empresa", "localizacao", mode="before")
    @classmethod
    def strip_required_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator("link")
    @classmethod
    def validate_link(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            return ""
        try:
            _HTTP_URL_ADAPTER.validate_python(cleaned)
        except ValidationError as exc:
            raise ValueError("Link deve usar http ou https, ou ficar vazio.") from exc
        return cleaned


class ApplicationUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notas: Optional[str] = Field(default=None, max_length=NOTES_MAX_LENGTH)
    data_aplicacao: Optional[str] = Field(
        default=None,
        max_length=APPLICATION_DATE_MAX_LENGTH,
    )


async def _read_existing_text(path: Path) -> str | None:
    try:
        return await asyncio.to_thread(path.read_text, encoding="utf-8")
    except FileNotFoundError:
        return None


async def _backup_corrupted_file(path: Path, content: str, session_id: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    backup_path = path.with_name(f"{path.stem}.corrupt-{timestamp}{path.suffix}")
    try:
        await write_text_atomic_async(backup_path, content)
    except OSError:
        logger.exception(
            "Falha ao criar backup de applications.json corrompido",
            extra={
                "event": "applications_corrupt_backup_error",
                "session_id": session_id,
                "path": str(path),
                "backup_path": str(backup_path),
            },
        )
        raise
    return backup_path


async def _raise_corrupted_file(path: Path, session_id: str, content: str, reason: str) -> None:
    backup_path = await _backup_corrupted_file(path, content, session_id)
    logger.error(
        "applications.json corrompido; escrita bloqueada",
        extra={
            "event": "applications_corrupted_file",
            "session_id": session_id,
            "path": str(path),
            "backup_path": str(backup_path),
            "reason": reason,
        },
    )
    raise HTTPException(
        status_code=409,
        detail=(
            "Arquivo de candidaturas corrompido. "
            "A operacao foi bloqueada para evitar perda de dados."
        ),
    )


async def _load(path: Path, session_id: str) -> list[dict[str, Any]]:
    try:
        content = await _read_existing_text(path)
        if content is None:
            return []
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
        await _raise_corrupted_file(path, session_id, content, "invalid_payload")
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
        await _raise_corrupted_file(path, session_id, content or "", "json_decode_error")
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
            **body.model_dump(mode="json"),
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
                    status_value = body.status.value
                    app["status"] = status_value
                    if status_value == "aplicada" and not app.get("data_aplicacao"):
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
