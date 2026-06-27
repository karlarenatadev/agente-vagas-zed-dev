"""Testes de corrupção/ilegibilidade de artefatos Markdown.

Garantem que arquivos binários / não-UTF-8 salvos com o nome esperado geram
um erro HTTP 409 controlado (com mensagem clara de "gere o artefato novamente")
em vez de um 500 genérico com traceback. Também checam que a rota não destrói
o arquivo corrompido nem produz artefatos derivados.

Os artefatos de sessão vivem na pasta da sessão default
(`tmp_path/sessions/_default/`); nenhum teste lê ou escreve no diretório
`data/` real e nenhum caminho depende de OpenAI/Firecrawl.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import config
from agents.resume_matcher import ResumeMatcher, match_report_to_markdown
from routers.common import read_required
from main import app


def _default_dir(tmp_path):
    """Diretório resolvido pela sessão default (sem header X-Session-Id)."""
    d = tmp_path / "sessions" / "_default"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return TestClient(app)


def _write(path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_binary(path) -> None:
    path.write_bytes(b"\x80\x81\xff\xfe lixo \x00 binario")


def _write_match_report(tmp_path, job_markdown: str, resume_markdown: str) -> str:
    report = ResumeMatcher().match(job_markdown, resume_markdown)
    markdown = match_report_to_markdown(report)
    _write(_default_dir(tmp_path) / "resume-match-report.md", markdown)
    return markdown


def test_match_curriculo_corrompido_retorna_409(
    tmp_path,
    monkeypatch,
    job_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    resume_path = base / "resume-analysis.md"
    _write_binary(resume_path)
    original_bytes = resume_path.read_bytes()

    response = client.post("/api/resume-match/analyze", json={})

    assert response.status_code == 409
    assert "detail" in response.json()
    assert "Traceback" not in response.text
    # O artefato corrompido não pode ser sobrescrito/apagado pela rota.
    assert resume_path.read_bytes() == original_bytes
    # E nenhum relatório derivado pode ter sido criado.
    assert not (base / "resume-match-report.md").exists()


def test_match_latest_corrompido_retorna_409(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    report_path = _default_dir(tmp_path) / "resume-match-report.md"
    _write_binary(report_path)
    original_bytes = report_path.read_bytes()

    response = client.get("/api/resume-match/latest")

    assert response.status_code == 409
    assert "detail" in response.json()
    assert "Traceback" not in response.text
    assert report_path.read_bytes() == original_bytes


def test_sugestoes_match_corrompido_retorna_409(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)
    _write_binary(base / "resume-match-report.md")

    response = client.post("/api/resume-tailoring/generate", json={})

    assert response.status_code == 409
    assert "detail" in response.json()
    assert "Traceback" not in response.text
    assert not (base / "resume-tailoring-suggestions.md").exists()


def test_pdi_sugestoes_corrompido_retorna_409(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)
    _write_match_report(tmp_path, job_markdown, resume_markdown)
    _write_binary(base / "resume-tailoring-suggestions.md")

    response = client.post("/api/pdi/generate", json={})

    assert response.status_code == 409
    assert "detail" in response.json()
    assert "Traceback" not in response.text
    assert not (base / "pdi-plan.md").exists()


def test_read_required_arquivo_binario_retorna_409(tmp_path):
    arquivo = tmp_path / "corrompido.md"
    _write_binary(arquivo)

    with pytest.raises(HTTPException) as exc:
        read_required(arquivo, "faltou", "invalido")

    assert exc.value.status_code == 409
