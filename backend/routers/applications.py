"""
Router de candidaturas — CRUD para rastrear vagas aplicadas.
Persiste em data/applications.json.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from session import SessionPaths, get_session_paths

router = APIRouter()

# Serializa o ciclo ler-modificar-gravar. FastAPI roda num único event loop,
# então este asyncio.Lock impede que duas requisições concorrentes (ex.: dois
# PATCH simultâneos) leiam a mesma lista, alterem cópias diferentes e uma
# sobrescreva a outra. Cobre também futuras mudanças que introduzam await
# entre o load e o save.
_write_lock = asyncio.Lock()


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

def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(data: list[dict], path: Path) -> None:
    # Escrita atômica: grava num arquivo temporário no mesmo diretório e troca
    # pelo definitivo com os.replace (operação atômica no SO). Assim, se o
    # processo cair no meio da escrita, o applications.json nunca fica truncado
    # ou corrompido — ou tem o conteúdo antigo, ou o novo, nunca um pedaço.
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    tmp_path = path.with_suffix(".json.tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    os.replace(tmp_path, path)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/")
async def list_applications(paths: SessionPaths = Depends(get_session_paths)):
    """Lista todas as candidaturas, ordenadas por data (mais recente primeiro)."""
    apps = _load(paths.APPLICATIONS_FILE)
    apps.sort(key=lambda x: x.get("data_salva", ""), reverse=True)
    return apps


@router.post("/")
async def create_application(
    body: ApplicationCreate,
    paths: SessionPaths = Depends(get_session_paths),
):
    """Salva uma nova candidatura."""
    async with _write_lock:
        apps = _load(paths.APPLICATIONS_FILE)
        new_app = {
            "id": str(uuid.uuid4()),
            "data_salva": datetime.now().isoformat(),
            **body.model_dump(),
        }
        apps.append(new_app)
        _save(apps, paths.APPLICATIONS_FILE)
    return new_app


@router.patch("/{app_id}")
async def update_application(
    app_id: str,
    body: ApplicationUpdate,
    paths: SessionPaths = Depends(get_session_paths),
):
    """Atualiza status, notas ou data de aplicação."""
    async with _write_lock:
        apps = _load(paths.APPLICATIONS_FILE)
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
                _save(apps, paths.APPLICATIONS_FILE)
                return app
    raise HTTPException(status_code=404, detail="Candidatura não encontrada")


@router.delete("/{app_id}")
async def delete_application(
    app_id: str,
    paths: SessionPaths = Depends(get_session_paths),
):
    """Remove uma candidatura."""
    async with _write_lock:
        apps = _load(paths.APPLICATIONS_FILE)
        filtered = [a for a in apps if a["id"] != app_id]
        if len(filtered) == len(apps):
            raise HTTPException(status_code=404, detail="Candidatura não encontrada")
        _save(filtered, paths.APPLICATIONS_FILE)
    return {"ok": True}


@router.get("/stats")
async def get_stats(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna contagens por status para o dashboard."""
    apps = _load(paths.APPLICATIONS_FILE)
    stats: dict[str, int] = {}
    for app in apps:
        s = app.get("status", "salva")
        stats[s] = stats.get(s, 0) + 1
    return {"total": len(apps), "by_status": stats}
