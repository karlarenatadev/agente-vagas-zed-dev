"""Endpoints da reconciliação entre perfil, currículo e vaga.

Lê os três artefatos analisados (perfil do quiz, currículo e vaga), mais o
relatório de aderência currículo×vaga quando disponível, e gera um diagnóstico
de consistência que respeita o "foco da candidatura" escolhido pelo usuário.
Espelha a estrutura de ``routers/resume_match.py``.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from session import SessionPaths, get_session_lock, get_session_paths, write_text_atomic_async
from routers.common import read_required
from agents.reconciliation import (
    Reconciler,
    normalize_focus,
    reconciliation_from_markdown,
    reconciliation_to_markdown,
    validate_profile,
)
from agents.resume_matcher import (
    validate_job_analysis,
    validate_resume_analysis,
)

router = APIRouter()
reconciler = Reconciler()


class ReconciliationRequest(BaseModel):
    use_latest_profile: bool = True
    use_latest_resume_analysis: bool = True
    use_latest_job_analysis: bool = True
    use_latest_match_report: bool = True
    # Foco opcional: sobrepõe a linha "Foco da candidatura:" do perfil.
    # Se None, lê do perfil; se ainda assim faltar, assume "vaga".
    focus: str | None = None

    @field_validator("focus")
    @classmethod
    def validate_focus(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        focus = normalize_focus(value)
        if focus is None:
            raise ValueError("Foco deve ser perfil, curriculo ou vaga.")
        return focus


class Conflict(BaseModel):
    field: str
    profile_value: str
    other_value: str
    severity: str


class ReconciliationResponse(BaseModel):
    focus: str
    consistency_score: int
    consistency_level: str
    profile_resume_conflicts: list[Conflict]
    profile_job_conflicts: list[Conflict]
    resume_job_summary: str
    match_score: int
    aligned_fields: list[str]
    focus_recommendations: list[str]
    next_steps: list[str]


def _read_match_if_present(paths: SessionPaths) -> str | None:
    """Lê o relatório de aderência se existir; retorna None caso contrário."""
    try:
        return paths.RESUME_MATCH_REPORT_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


@router.get("/latest", response_model=ReconciliationResponse)
async def get_latest_reconciliation(
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    try:
        content = paths.RECONCILIATION_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma reconciliação foi gerada ainda.",
        )

    report = reconciliation_from_markdown(content)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma reconciliação válida foi encontrada.",
        )

    return report


@router.post("/analyze", response_model=ReconciliationResponse)
async def analyze_reconciliation(
    body: ReconciliationRequest | None = None,
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    request = body or ReconciliationRequest()
    if (
        not request.use_latest_profile
        or not request.use_latest_resume_analysis
        or not request.use_latest_job_analysis
    ):
        raise HTTPException(
            status_code=400,
            detail="Esta versão reconcilia apenas os artefatos mais recentes salvos em data/.",
        )

    # Perfil (user-profile.md) — formato diferente dos demais.
    profile_content = read_required(
        paths.PROFILE_FILE,
        "Conclua o quiz de perfil primeiro.",
        "O perfil está vazio. Refaça o diagnóstico.",
    )
    if not validate_profile(profile_content):
        raise HTTPException(
            status_code=400,
            detail="O perfil não está concluído ou está incompleto. Refaça o diagnóstico.",
        )

    resume_content = read_required(
        paths.RESUME_ANALYSIS_FILE,
        "Envie e analise um currículo primeiro.",
        "A análise do currículo está vazia ou inválida. Envie o currículo novamente.",
    )
    if not validate_resume_analysis(resume_content):
        raise HTTPException(
            status_code=400,
            detail="A análise do currículo está vazia ou inválida. Envie o currículo novamente.",
        )

    job_content = read_required(
        paths.JOB_DESCRIPTION_ANALYSIS_FILE,
        "Analise uma descrição de vaga primeiro.",
        "A análise da vaga está vazia ou inválida. Analise a vaga novamente.",
    )
    if not validate_job_analysis(job_content):
        raise HTTPException(
            status_code=400,
            detail="A análise da vaga está vazia ou inválida. Analise a vaga novamente.",
        )

    # Relatório de aderência é opcional: se não existir, o reconciler recalcula
    # internamente via ResumeMatcher. Mas se existir, reusamos para consistência.
    match_content = _read_match_if_present(paths) if request.use_latest_match_report else None

    result = reconciler.reconcile(
        profile_content,
        resume_content,
        job_content,
        match_content=match_content,
        focus=request.focus,
    )

    async with get_session_lock(paths.session_id):
        await write_text_atomic_async(
            paths.RECONCILIATION_FILE,
            reconciliation_to_markdown(result),
        )

    return result
