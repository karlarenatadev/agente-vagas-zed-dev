"""Endpoints para análise de descrições de vagas coladas pelo usuário."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from session import SessionPaths, get_session_lock, get_session_paths, write_text_atomic_async
from agents.job_description_analyzer import (
    JobDescriptionAnalyzer,
    analysis_from_markdown,
    analysis_to_markdown,
)

router = APIRouter()
analyzer = JobDescriptionAnalyzer()


def _invalidate_downstream_artifacts(paths: SessionPaths) -> None:
    for path in (
        paths.RESUME_MATCH_REPORT_FILE,
        paths.RESUME_TAILORING_SUGGESTIONS_FILE,
        paths.PDI_PLAN_FILE,
    ):
        path.unlink(missing_ok=True)


class JobDescriptionRequest(BaseModel):
    description: str = Field(max_length=50000)


class JobDescriptionAnalysisResponse(BaseModel):
    title: str
    company: str
    seniority: str
    modality: str
    location: str
    keywords: list[str]
    hard_skills: list[str]
    soft_skills: list[str]
    tools: list[str]
    responsibilities: list[str]
    required_requirements: list[str]
    nice_to_have: list[str]
    alerts: list[str]
    next_steps: list[str]


@router.get("/latest", response_model=JobDescriptionAnalysisResponse)
async def get_latest_job_description(paths: SessionPaths = Depends(get_session_paths)):
    try:
        content = paths.JOB_DESCRIPTION_ANALYSIS_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Nenhuma vaga foi analisada ainda.")

    analysis = analysis_from_markdown(content)
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Nenhuma análise de vaga válida foi encontrada.",
        )

    return analysis


@router.post("/analyze", response_model=JobDescriptionAnalysisResponse)
async def analyze_job_description(
    body: JobDescriptionRequest,
    paths: SessionPaths = Depends(get_session_paths),
):
    description = body.description.strip()
    if len(description) < 40:
        raise HTTPException(
            status_code=400,
            detail="Cole uma descrição de vaga com pelo menos 40 caracteres.",
        )

    analysis = analyzer.analyze(description)
    async with get_session_lock(paths.session_id):
        await write_text_atomic_async(
            paths.JOB_DESCRIPTION_ANALYSIS_FILE,
            analysis_to_markdown(analysis),
        )
        _invalidate_downstream_artifacts(paths)

    # Próxima etapa: combinar este resultado com RESUME_ANALYSIS_FILE para
    # produzir resume-match-report.md e, depois, um pdi-plan.md.
    return analysis
