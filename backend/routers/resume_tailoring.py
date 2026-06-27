"""Endpoints para gerar sugestões seguras de adaptação do currículo."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from session import SessionPaths, get_session_lock, get_session_paths, write_text_atomic_async
from routers.common import read_optional_text, read_required, resolve_focus
from agents.resume_tailor import (
    ResumeTailor,
    tailoring_from_markdown,
    tailoring_to_markdown,
    validate_job_analysis,
    validate_match_report,
    validate_resume_analysis,
)

router = APIRouter()
tailor = ResumeTailor()


class ResumeTailoringRequest(BaseModel):
    use_latest_resume_analysis: bool = True
    use_latest_job_analysis: bool = True
    use_latest_match_report: bool = True
    # Foco da candidatura (perfil/curriculo/vaga). Ausente → lê do perfil; se
    # ainda faltar, assume "vaga". Valor inválido cai no fallback (sem erro).
    focus: str | None = None


class ResumeTailoringResponse(BaseModel):
    job_title: str
    match_score: int
    readiness_level: str
    summary_suggestions: list[str]
    skills_suggestions: list[str]
    project_suggestions: list[str]
    experience_suggestions: list[str]
    keywords_to_include: list[str]
    keywords_to_avoid_claiming: list[str]
    can_highlight_better: list[str]
    can_reposition: list[str]
    needs_evidence: list[str]
    do_not_claim: list[str]
    safety_alerts: list[str]
    next_steps: list[str]


@router.get("/latest", response_model=ResumeTailoringResponse)
async def get_latest_resume_tailoring(
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    content = read_optional_text(paths.RESUME_TAILORING_SUGGESTIONS_FILE)
    if content is None:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma sugestão de currículo foi gerada ainda.",
        )

    result = tailoring_from_markdown(content)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma sugestão de currículo válida foi encontrada.",
        )

    return result


@router.post("/generate", response_model=ResumeTailoringResponse)
async def generate_resume_tailoring(
    body: ResumeTailoringRequest | None = None,
    paths: SessionPaths = Depends(get_session_paths),
) -> dict[str, Any]:
    request = body or ResumeTailoringRequest()
    if not all(
        (
            request.use_latest_resume_analysis,
            request.use_latest_job_analysis,
            request.use_latest_match_report,
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Esta versão usa apenas as análises mais recentes salvas em data/.",
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

    match_content = read_required(
        paths.RESUME_MATCH_REPORT_FILE,
        "Compare a vaga com o currículo primeiro.",
        "O relatório de aderência está vazio ou inválido. Execute a comparação novamente.",
    )
    if not validate_match_report(match_content):
        raise HTTPException(
            status_code=400,
            detail="O relatório de aderência está vazio ou inválido. Execute a comparação novamente.",
        )

    # Foco da candidatura: corpo da requisição > perfil > "vaga".
    try:
        profile_content = paths.PROFILE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        profile_content = None
    focus = resolve_focus(profile_content, request.focus)

    result = tailor.generate(resume_content, job_content, match_content, focus=focus)
    async with get_session_lock(paths.session_id):
        await write_text_atomic_async(
            paths.RESUME_TAILORING_SUGGESTIONS_FILE,
            tailoring_to_markdown(result),
        )

    # Próxima etapa: combinar este artefato com o match para gerar pdi-plan.md.
    # Exportação e edição final de PDF/DOCX permanecem fora deste fluxo.
    return result
