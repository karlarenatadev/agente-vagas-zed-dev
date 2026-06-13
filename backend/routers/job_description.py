"""Endpoints para análise de descrições de vagas coladas pelo usuário."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

import config
from agents.job_description_analyzer import (
    JobDescriptionAnalyzer,
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


@router.post("/analyze", response_model=JobDescriptionAnalysisResponse)
async def analyze_job_description(body: JobDescriptionRequest):
    description = body.description.strip()
    if len(description) < 40:
        raise HTTPException(
            status_code=400,
            detail="Cole uma descrição de vaga com pelo menos 40 caracteres.",
        )

    analysis = analyzer.analyze(description)
    config.JOB_DESCRIPTION_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.JOB_DESCRIPTION_ANALYSIS_FILE.write_text(
        analysis_to_markdown(analysis),
        encoding="utf-8",
    )

    # Próxima etapa: combinar este resultado com RESUME_ANALYSIS_FILE para
    # produzir resume-match-report.md e, depois, um pdi-plan.md.
    return analysis
