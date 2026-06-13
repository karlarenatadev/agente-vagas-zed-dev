"""
Router de dados — endpoints REST para leitura dos arquivos data/.
Permite ao frontend exibir resultados de vagas, cursos e entrevistas.
"""

from fastapi import APIRouter, HTTPException

import config

router = APIRouter()


@router.get("/jobs")
async def get_job_results():
    """Retorna os resultados de busca de vagas."""
    try:
        content = config.JOB_RESULTS_FILE.read_text(encoding="utf-8")
        return {"exists": True, "content": content}
    except FileNotFoundError:
        return {"exists": False, "content": ""}


@router.get("/courses")
async def get_course_recommendations():
    """Retorna as recomendações de cursos."""
    try:
        content = config.COURSE_RECS_FILE.read_text(encoding="utf-8")
        return {"exists": True, "content": content}
    except FileNotFoundError:
        return {"exists": False, "content": ""}


@router.get("/interview")
async def get_interview_session():
    """Retorna a sessão de entrevista atual."""
    try:
        content = config.INTERVIEW_FILE.read_text(encoding="utf-8")
        return {"exists": True, "content": content}
    except FileNotFoundError:
        return {"exists": False, "content": ""}


@router.get("/job-description")
async def get_job_description_analysis():
    """Retorna a última análise de descrição de vaga."""
    try:
        content = config.JOB_DESCRIPTION_ANALYSIS_FILE.read_text(encoding="utf-8")
        return {"exists": True, "content": content}
    except FileNotFoundError:
        return {"exists": False, "content": ""}


@router.get("/resume-match")
async def get_resume_match_report():
    """Retorna o último relatório de aderência entre vaga e currículo."""
    try:
        content = config.RESUME_MATCH_REPORT_FILE.read_text(encoding="utf-8")
        return {"exists": True, "content": content}
    except FileNotFoundError:
        return {"exists": False, "content": ""}


@router.get("/resume-tailoring")
async def get_resume_tailoring_suggestions():
    """Retorna as últimas sugestões seguras de currículo."""
    try:
        content = config.RESUME_TAILORING_SUGGESTIONS_FILE.read_text(
            encoding="utf-8"
        )
        return {"exists": True, "content": content}
    except FileNotFoundError:
        return {"exists": False, "content": ""}


@router.get("/pdi")
async def get_pdi_plan():
    """Retorna o último PDI personalizado por vaga."""
    try:
        content = config.PDI_PLAN_FILE.read_text(encoding="utf-8")
        return {"exists": True, "content": content}
    except FileNotFoundError:
        return {"exists": False, "content": ""}
