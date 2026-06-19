"""
Router de dados — endpoints REST para leitura dos arquivos data/.
Permite ao frontend exibir resultados de vagas, cursos e entrevistas.

Todos os caminhos vêm do SessionPaths da requisição (header X-Session-Id), de
modo que cada sessão lê apenas os próprios artefatos.
"""

from pathlib import Path

from fastapi import APIRouter, Depends

from session import SessionPaths, get_session_paths

router = APIRouter()


def _read_artifact(path: Path) -> dict:
    """Lê um artefato Markdown e devolve o envelope {exists, content}."""
    try:
        return {"exists": True, "content": path.read_text(encoding="utf-8")}
    except FileNotFoundError:
        return {"exists": False, "content": ""}


@router.get("/jobs")
async def get_job_results(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna os resultados de busca de vagas."""
    return _read_artifact(paths.JOB_RESULTS_FILE)


@router.get("/courses")
async def get_course_recommendations(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna as recomendações de cursos."""
    return _read_artifact(paths.COURSE_RECS_FILE)


@router.get("/interview")
async def get_interview_session(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna a sessão de entrevista atual."""
    return _read_artifact(paths.INTERVIEW_FILE)


@router.get("/resume-analysis")
async def get_resume_analysis(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna a última análise de currículo."""
    return _read_artifact(paths.RESUME_ANALYSIS_FILE)


@router.get("/job-description")
async def get_job_description_analysis(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna a última análise de descrição de vaga."""
    return _read_artifact(paths.JOB_DESCRIPTION_ANALYSIS_FILE)


@router.get("/resume-match")
async def get_resume_match_report(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna o último relatório de aderência entre vaga e currículo."""
    return _read_artifact(paths.RESUME_MATCH_REPORT_FILE)


@router.get("/reconciliation")
async def get_reconciliation_report(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna o último relatório de reconciliação entre perfil, currículo e vaga."""
    return _read_artifact(paths.RECONCILIATION_FILE)


@router.get("/resume-tailoring")
async def get_resume_tailoring_suggestions(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna as últimas sugestões seguras de currículo."""
    return _read_artifact(paths.RESUME_TAILORING_SUGGESTIONS_FILE)


@router.get("/pdi")
async def get_pdi_plan(paths: SessionPaths = Depends(get_session_paths)):
    """Retorna o último PDI personalizado por vaga."""
    return _read_artifact(paths.PDI_PLAN_FILE)
