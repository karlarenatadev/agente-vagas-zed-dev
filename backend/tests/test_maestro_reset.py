"""Testes do reset completo do Maestro."""

import asyncio

from agents.maestro import MaestroAgent
from session import SessionPaths


def test_reset_remove_todos_os_artefatos_da_sessao(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    artifacts = [
        paths.PROFILE_FILE,
        paths.JOB_RESULTS_FILE,
        paths.COURSE_RECS_FILE,
        paths.INTERVIEW_FILE,
        paths.RESUME_ANALYSIS_FILE,
        paths.JOB_DESCRIPTION_ANALYSIS_FILE,
        paths.RESUME_MATCH_REPORT_FILE,
        paths.RESUME_TAILORING_SUGGESTIONS_FILE,
        paths.PDI_PLAN_FILE,
        paths.APPLICATIONS_FILE,
    ]
    for artifact in artifacts:
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_text("conteudo antigo", encoding="utf-8")

    MaestroAgent(paths)._reset_data_files()

    assert all(not artifact.exists() for artifact in artifacts)


def test_handle_reset_recria_apenas_quiz_vazio(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    paths.RESUME_MATCH_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.RESUME_MATCH_REPORT_FILE.write_text("match antigo", encoding="utf-8")

    agent = MaestroAgent(paths)

    async def run_reset():
        return [token async for token in agent._handle_reset()]

    tokens = asyncio.run(run_reset())

    assert not paths.RESUME_MATCH_REPORT_FILE.exists()
    assert paths.QUIZ_FILE.read_text(encoding="utf-8") == "Concluído: false\n"
    assert any("__STATE__:quiz:0" in token for token in tokens)
