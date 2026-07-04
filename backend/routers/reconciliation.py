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

from artifacts import (
    ArtifactRegistryError,
    calculate_content_hash,
    mark_dependents_stale,
    register_artifact,
)
from session import SessionPaths, get_session_lock, get_session_paths, write_text_atomic_async
from routers.common import (
    read_optional_text,
    read_required,
    require_consumable_artifact,
)
from agents.reconciliation import (
    Reconciler,
    normalize_focus,
    reconciliation_from_markdown,
    reconciliation_to_markdown,
    upsert_focus_line,
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
    return read_optional_text(paths.RESUME_MATCH_REPORT_FILE)


@router.get("/latest", response_model=ReconciliationResponse)
async def get_latest_reconciliation(
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    content = read_optional_text(paths.RECONCILIATION_FILE)
    if content is None:
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
    if match_content is not None:
        require_consumable_artifact(
            paths.dir,
            "match",
            paths.RESUME_MATCH_REPORT_FILE,
            current_input_hashes={
                "resume": calculate_content_hash(resume_content),
                "job_description": calculate_content_hash(job_content),
            },
        )

    result = reconciler.reconcile(
        profile_content,
        resume_content,
        job_content,
        match_content=match_content,
        focus=request.focus,
    )

    reconciliation_markdown = reconciliation_to_markdown(result)
    input_hashes = {
        "profile": calculate_content_hash(profile_content),
        "resume": calculate_content_hash(resume_content),
        "job_description": calculate_content_hash(job_content),
        "focus": calculate_content_hash(result["focus"]),
    }
    if match_content is not None:
        input_hashes["match"] = calculate_content_hash(match_content)

    async with get_session_lock(paths.session_id):
        try:
            register_artifact(
                paths.dir,
                "reconciliation",
                content=reconciliation_markdown,
                input_hashes=input_hashes,
                generator_version="reconciliation:v1",
            )
        except ArtifactRegistryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        await write_text_atomic_async(
            paths.RECONCILIATION_FILE,
            reconciliation_markdown,
        )

    return result


# ── Foco da candidatura (PUT) ────────────────────────────────────────────────


class FocusUpdateRequest(BaseModel):
    focus: str

    @field_validator("focus")
    @classmethod
    def validate_focus_value(cls, value: str) -> str:
        focus = normalize_focus(value)
        if focus is None:
            raise ValueError("Foco deve ser perfil, curriculo ou vaga.")
        return focus


class FocusUpdateResponse(BaseModel):
    focus: str


@router.put("/focus", response_model=FocusUpdateResponse)
async def set_candidacy_focus(
    body: FocusUpdateRequest,
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    """Fixa o foco da candidatura no perfil (``user-profile.md``).

    Persiste a linha "Foco da candidatura: {perfil|curriculo|vaga}", lida depois
    pela reconciliação e pelos agentes de match, tailoring e PDI para priorizar a
    fonte escolhida. Foco inválido → 422; perfil ausente/vazio → 400.
    """
    profile_content = read_required(
        paths.PROFILE_FILE,
        "Conclua o quiz de perfil primeiro.",
        "O perfil está vazio. Refaça o diagnóstico.",
    )
    updated = upsert_focus_line(profile_content, body.focus)
    async with get_session_lock(paths.session_id):
        try:
            mark_dependents_stale(paths.dir, "focus")
            register_artifact(
                paths.dir,
                "focus",
                content=body.focus,
                input_hashes={
                    "profile": calculate_content_hash(updated),
                },
                generator_version="focus:v1",
            )
        except ArtifactRegistryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        await write_text_atomic_async(paths.PROFILE_FILE, updated)
    return {"focus": body.focus}
