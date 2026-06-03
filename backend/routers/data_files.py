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
