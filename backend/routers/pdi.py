"""Endpoints para geração do PDI personalizado por vaga."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import config
from routers.common import read_required
from agents.pdi_generator import (
    PdiGenerator,
    pdi_to_markdown,
    validate_job_analysis,
    validate_match_report,
    validate_resume_analysis,
    validate_tailoring_suggestions,
)

router = APIRouter()
generator = PdiGenerator()


class PdiRequest(BaseModel):
    use_latest_resume_analysis: bool = True
    use_latest_job_analysis: bool = True
    use_latest_match_report: bool = True
    use_latest_tailoring_suggestions: bool = True


class PdiResponse(BaseModel):
    target_role: str
    overall_score: int
    readiness_level: str
    main_goal: str
    priority_gaps: list[str]
    quick_wins: list[str]
    seven_day_plan: list[str]
    thirty_day_plan: list[str]
    sixty_day_plan: list[str]
    portfolio_projects: list[str]
    resume_evidence_to_create: list[str]
    study_resources: list[str]
    interview_preparation: list[str]
    next_steps: list[str]


@router.post("/generate", response_model=PdiResponse)
async def generate_pdi(body: PdiRequest | None = None) -> dict[str, Any]:
    request = body or PdiRequest()
    if not all(
        (
            request.use_latest_resume_analysis,
            request.use_latest_job_analysis,
            request.use_latest_match_report,
            request.use_latest_tailoring_suggestions,
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Esta versão usa apenas os artefatos mais recentes salvos em data/.",
        )

    resume_content = read_required(
        config.RESUME_ANALYSIS_FILE,
        "Envie e analise um currículo primeiro.",
        "A análise do currículo está vazia ou inválida. Envie o currículo novamente.",
    )
    if not validate_resume_analysis(resume_content):
        raise HTTPException(
            status_code=400,
            detail="A análise do currículo está vazia ou inválida. Envie o currículo novamente.",
        )

    job_content = read_required(
        config.JOB_DESCRIPTION_ANALYSIS_FILE,
        "Analise uma descrição de vaga primeiro.",
        "A análise da vaga está vazia ou inválida. Analise a vaga novamente.",
    )
    if not validate_job_analysis(job_content):
        raise HTTPException(
            status_code=400,
            detail="A análise da vaga está vazia ou inválida. Analise a vaga novamente.",
        )

    match_content = read_required(
        config.RESUME_MATCH_REPORT_FILE,
        "Compare a vaga com o currículo primeiro.",
        "O relatório de aderência está vazio ou inválido. Execute a comparação novamente.",
    )
    if not validate_match_report(match_content):
        raise HTTPException(
            status_code=400,
            detail="O relatório de aderência está vazio ou inválido. Execute a comparação novamente.",
        )

    tailoring_content = read_required(
        config.RESUME_TAILORING_SUGGESTIONS_FILE,
        "Gere sugestões seguras de currículo primeiro.",
        "As sugestões de currículo estão vazias ou inválidas. Gere as sugestões novamente.",
    )
    if not validate_tailoring_suggestions(tailoring_content):
        raise HTTPException(
            status_code=400,
            detail="As sugestões de currículo estão vazias ou inválidas. Gere as sugestões novamente.",
        )

    result = generator.generate(
        resume_content,
        job_content,
        match_content,
        tailoring_content,
    )
    config.PDI_PLAN_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.PDI_PLAN_FILE.write_text(
        pdi_to_markdown(result),
        encoding="utf-8",
    )

    # Próxima etapa: usar este PDI no Coach para uma entrevista específica.
    # Exportação e geração de currículo final permanecem fora desta etapa.
    return result
