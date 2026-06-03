"""
Router de candidaturas — CRUD para rastrear vagas aplicadas.
Persiste em data/applications.json.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config

router = APIRouter()

APPLICATIONS_FILE = config.DATA_DIR / "applications.json"


# ── Schemas ───────────────────────────────────────────────────────────────────

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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load() -> list[dict]:
    if not APPLICATIONS_FILE.exists():
        return []
    try:
        return json.loads(APPLICATIONS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(data: list[dict]) -> None:
    APPLICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    APPLICATIONS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/")
async def list_applications():
    """Lista todas as candidaturas, ordenadas por data (mais recente primeiro)."""
    apps = _load()
    apps.sort(key=lambda x: x.get("data_salva", ""), reverse=True)
    return apps


@router.post("/")
async def create_application(body: ApplicationCreate):
    """Salva uma nova candidatura."""
    apps = _load()
    new_app = {
        "id": str(uuid.uuid4()),
        "data_salva": datetime.now().isoformat(),
        **body.model_dump(),
    }
    apps.append(new_app)
    _save(apps)
    return new_app


@router.patch("/{app_id}")
async def update_application(app_id: str, body: ApplicationUpdate):
    """Atualiza status, notas ou data de aplicação."""
    apps = _load()
    for app in apps:
        if app["id"] == app_id:
            if body.status is not None:
                app["status"] = body.status
                if body.status == "aplicada" and not app.get("data_aplicacao"):
                    app["data_aplicacao"] = datetime.now().isoformat()
            if body.notas is not None:
                app["notas"] = body.notas
            if body.data_aplicacao is not None:
                app["data_aplicacao"] = body.data_aplicacao
            _save(apps)
            return app
    raise HTTPException(status_code=404, detail="Candidatura não encontrada")


@router.delete("/{app_id}")
async def delete_application(app_id: str):
    """Remove uma candidatura."""
    apps = _load()
    filtered = [a for a in apps if a["id"] != app_id]
    if len(filtered) == len(apps):
        raise HTTPException(status_code=404, detail="Candidatura não encontrada")
    _save(filtered)
    return {"ok": True}


@router.get("/stats")
async def get_stats():
    """Retorna contagens por status para o dashboard."""
    apps = _load()
    stats: dict[str, int] = {}
    for app in apps:
        s = app.get("status", "salva")
        stats[s] = stats.get(s, 0) + 1
    return {"total": len(apps), "by_status": stats}
