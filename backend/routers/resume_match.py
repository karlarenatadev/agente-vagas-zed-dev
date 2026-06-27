"""Endpoints da comparação entre vaga analisada e currículo analisado."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from session import SessionPaths, get_session_lock, get_session_paths, write_text_atomic_async
from routers.common import read_optional_text, read_required, resolve_focus
from agents.resume_matcher import (
    ResumeMatcher,
    match_report_from_markdown,
    match_report_to_markdown,
    validate_job_analysis,
    validate_resume_analysis,
)

router = APIRouter()
matcher = ResumeMatcher()


class ResumeMatchRequest(BaseModel):
    use_latest_job_analysis: bool = True
    use_latest_resume_analysis: bool = True
    # Foco da candidatura (perfil/curriculo/vaga). Ausente → lê do perfil; se
    # ainda faltar, assume "vaga". Valor inválido cai no fallback (sem erro).
    focus: str | None = None


class ScoreBreakdown(BaseModel):
    hard_skills: int
    tools: int
    soft_skills: int
    keywords: int
    seniority_area: int


class ResumeMatchResponse(BaseModel):
    overall_score: int
    readiness_level: str
    job_title: str
    resume_summary: str
    score_breakdown: ScoreBreakdown
    strong_evidence: list[str]
    partial_evidence: list[str]
    missing_requirements: list[str]
    hard_skills_found: list[str]
    hard_skills_missing: list[str]
    soft_skills_found: list[str]
    soft_skills_missing: list[str]
    tools_found: list[str]
    tools_missing: list[str]
    matched_keywords: list[str]
    missing_keywords: list[str]
    strengths: list[str]
    critical_gaps: list[str]
    safe_resume_suggestions: list[str]
    do_not_claim: list[str]
    next_steps: list[str]


@router.get("/latest", response_model=ResumeMatchResponse)
async def get_latest_resume_match(
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    content = read_optional_text(paths.RESUME_MATCH_REPORT_FILE)
    if content is None:
        raise HTTPException(
            status_code=404,
            detail="Nenhum relatório de aderência foi gerado ainda.",
        )

    report = match_report_from_markdown(content)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Nenhum relatório de aderência válido foi encontrado.",
        )

    return report


@router.post("/analyze", response_model=ResumeMatchResponse)
async def analyze_resume_match(
    body: ResumeMatchRequest | None = None,
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    request = body or ResumeMatchRequest()
    if not request.use_latest_job_analysis or not request.use_latest_resume_analysis:
        raise HTTPException(
            status_code=400,
            detail="Esta versão compara apenas as análises mais recentes salvas em data/.",
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

    # Foco da candidatura: corpo da requisição > perfil > "vaga".
    try:
        profile_content = paths.PROFILE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        profile_content = None
    focus = resolve_focus(profile_content, request.focus)

    report = matcher.match(job_content, resume_content, focus=focus)
    async with get_session_lock(paths.session_id):
        await write_text_atomic_async(
            paths.RESUME_MATCH_REPORT_FILE,
            match_report_to_markdown(report),
        )

    # Próxima etapa: usar este relatório para gerar sugestões de adaptação
    # em resume-tailoring-suggestions.md e, depois, o PDI em pdi-plan.md.
    return report
