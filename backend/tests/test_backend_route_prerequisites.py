"""Testes HTTP mínimos dos fluxos críticos do backend.

Todos os artefatos são sintéticos e gravados em `tmp_path`; nenhum teste lê ou
escreve no diretório `data/` real e nenhum caminho depende de OpenAI/Firecrawl.
"""

from fastapi.testclient import TestClient

import config
from agents.pdi_generator import PdiGenerator, pdi_from_markdown
from agents.resume_matcher import ResumeMatcher, match_report_to_markdown
from agents.resume_tailor import ResumeTailor, tailoring_to_markdown
from main import app


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return TestClient(app)


def _write(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_match_report(tmp_path, job_markdown: str, resume_markdown: str) -> str:
    report = ResumeMatcher().match(job_markdown, resume_markdown)
    markdown = match_report_to_markdown(report)
    _write(tmp_path / "resume-match-report.md", markdown)
    return markdown


def _write_tailoring(
    tmp_path,
    resume_markdown: str,
    job_markdown: str,
    match_markdown: str,
) -> str:
    result = ResumeTailor().generate(resume_markdown, job_markdown, match_markdown)
    markdown = tailoring_to_markdown(result)
    _write(tmp_path / "resume-tailoring-suggestions.md", markdown)
    return markdown


def test_resume_upload_txt_persiste_analise_em_tmp_path(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    content = (
        "Nome: Pessoa Teste\n"
        "Analista de dados junior com experiencia em Python, SQL, Excel e Power BI.\n"
        "Boa comunicacao, trabalho em equipe e projetos de dashboards."
    )

    response = client.post(
        "/api/resume/upload",
        files={"file": ("curriculo.txt", content.encode("utf-8"), "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "Python" in body["analysis"]["technical_skills"]
    assert (tmp_path / "resume-analysis.md").exists()

    latest = client.get("/api/resume/latest")
    assert latest.status_code == 200
    assert "Python" in latest.json()["technical_skills"]


def test_resume_upload_recusa_extensao_invalida(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/api/resume/upload",
        files={"file": ("curriculo.exe", b"conteudo suficiente para teste", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_match_sem_curriculo_retorna_400(tmp_path, monkeypatch, job_markdown):
    client = _client(tmp_path, monkeypatch)
    _write(tmp_path / "job-description-analysis.md", job_markdown)

    response = client.post("/api/resume-match/analyze", json={})

    assert response.status_code == 400
    assert "curr" in response.json()["detail"].casefold()


def test_match_sem_vaga_valida_retorna_400(tmp_path, monkeypatch, resume_markdown):
    client = _client(tmp_path, monkeypatch)
    _write(tmp_path / "job-description-analysis.md", "conteudo invalido")
    _write(tmp_path / "resume-analysis.md", resume_markdown)

    response = client.post("/api/resume-match/analyze", json={})

    assert response.status_code == 400
    assert "vaga" in response.json()["detail"].casefold()


def test_match_com_artefatos_validos_persiste_relatorio(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    _write(tmp_path / "job-description-analysis.md", job_markdown)
    _write(tmp_path / "resume-analysis.md", resume_markdown)

    response = client.post("/api/resume-match/analyze", json={})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["overall_score"], int)
    assert (tmp_path / "resume-match-report.md").exists()


def test_sugestoes_sem_relatorio_de_match_retorna_400(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    _write(tmp_path / "job-description-analysis.md", job_markdown)
    _write(tmp_path / "resume-analysis.md", resume_markdown)

    response = client.post("/api/resume-tailoring/generate", json={})

    assert response.status_code == 400
    assert "compare" in response.json()["detail"].casefold()


def test_sugestoes_com_artefatos_validos_persistem_markdown(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    _write(tmp_path / "job-description-analysis.md", job_markdown)
    _write(tmp_path / "resume-analysis.md", resume_markdown)
    _write_match_report(tmp_path, job_markdown, resume_markdown)

    response = client.post("/api/resume-tailoring/generate", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["summary_suggestions"]
    assert (tmp_path / "resume-tailoring-suggestions.md").exists()


def test_pdi_sem_sugestoes_retorna_400(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    _write(tmp_path / "job-description-analysis.md", job_markdown)
    _write(tmp_path / "resume-analysis.md", resume_markdown)
    _write_match_report(tmp_path, job_markdown, resume_markdown)

    response = client.post("/api/pdi/generate", json={})

    assert response.status_code == 400
    assert "sugest" in response.json()["detail"].casefold()


def test_pdi_com_artefatos_validos_persiste_e_le_latest(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    _write(tmp_path / "job-description-analysis.md", job_markdown)
    _write(tmp_path / "resume-analysis.md", resume_markdown)
    match_markdown = _write_match_report(tmp_path, job_markdown, resume_markdown)
    _write_tailoring(tmp_path, resume_markdown, job_markdown, match_markdown)

    response = client.post("/api/pdi/generate", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["main_goal"]
    persisted = (tmp_path / "pdi-plan.md").read_text(encoding="utf-8")
    assert pdi_from_markdown(persisted) is not None

    latest = client.get("/api/pdi/latest")
    assert latest.status_code == 200
    assert latest.json()["main_goal"] == body["main_goal"]
