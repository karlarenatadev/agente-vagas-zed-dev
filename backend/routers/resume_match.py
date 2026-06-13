"""Endpoints da comparação entre vaga analisada e currículo analisado."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from agents.resume_matcher import (
    ResumeMatcher,
    match_report_to_markdown,
    validate_job_analysis,
    validate_resume_analysis,
)

router = APIRouter()
matcher = ResumeMatcher()


class ResumeMatchRequest(BaseModel):
    use_latest_job_analysis: bool = True
    use_latest_resume_analysis: bool = True


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


def _read_required(path, missing_message: str, invalid_message: str) -> str:
    try:
        content = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=missing_message)

    if not content:
        raise HTTPException(status_code=400, detail=invalid_message)
    return content


@router.post("/analyze", response_model=ResumeMatchResponse)
async def analyze_resume_match(body: ResumeMatchRequest | None = None) -> dict[str, Any]:
    request = body or ResumeMatchRequest()
    if not request.use_latest_job_analysis or not request.use_latest_resume_analysis:
        raise HTTPException(
            status_code=400,
            detail="Esta versão compara apenas as análises mais recentes salvas em data/.",
        )

    job_content = _read_required(
        config.JOB_DESCRIPTION_ANALYSIS_FILE,
        "Analise uma descrição de vaga primeiro.",
        "A análise da vaga está vazia ou inválida. Analise a vaga novamente.",
    )
    if not validate_job_analysis(job_content):
        raise HTTPException(
            status_code=400,
            detail="A análise da vaga está vazia ou inválida. Analise a vaga novamente.",
        )

    resume_content = _read_required(
        config.RESUME_ANALYSIS_FILE,
        "Envie e analise um currículo primeiro.",
        "A análise do currículo está vazia ou inválida. Envie o currículo novamente.",
    )
    if not validate_resume_analysis(resume_content):
        raise HTTPException(
            status_code=400,
            detail="A análise do currículo está vazia ou inválida. Envie o currículo novamente.",
        )

    report = matcher.match(job_content, resume_content)
    config.RESUME_MATCH_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.RESUME_MATCH_REPORT_FILE.write_text(
        match_report_to_markdown(report),
        encoding="utf-8",
    )

    # Próxima etapa: usar este relatório para gerar sugestões de adaptação
    # em resume-tailoring-suggestions.md e, depois, o PDI em pdi-plan.md.
    return report
