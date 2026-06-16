"""Endpoints para análise de descrições de vagas coladas pelo usuário."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException

from session import SessionPaths, get_session_paths
from agents.job_description_analyzer import (
    JobDescriptionAnalyzer,
    analysis_from_markdown,
    analysis_to_markdown,
)

router = APIRouter()
analyzer = JobDescriptionAnalyzer()


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
    paths.JOB_DESCRIPTION_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.JOB_DESCRIPTION_ANALYSIS_FILE.write_text(
        analysis_to_markdown(analysis),
        encoding="utf-8",
    )

    # Próxima etapa: combinar este resultado com RESUME_ANALYSIS_FILE para
    # produzir resume-match-report.md e, depois, um pdi-plan.md.
    return analysis
