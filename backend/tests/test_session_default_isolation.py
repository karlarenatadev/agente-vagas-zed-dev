"""Isolamento da sessão default frente ao legado solto em `data/*.md`.

A sessão default (chamada sem header ``X-Session-Id``) resolve seus artefatos em
``data/sessions/_default/``. Os arquivos Markdown soltos na raiz de ``data/`` são
LEGADO: não são consumidos automaticamente e tampouco apagados. Estes testes
travam esse contrato usando um relatório de aderência real (sem mocks).
"""

from fastapi.testclient import TestClient

import config
from agents.resume_matcher import ResumeMatcher, match_report_to_markdown
from main import app
from session import SessionPaths


def _default_dir(tmp_path):
    """Diretório resolvido pela sessão default (sem header X-Session-Id)."""
    d = tmp_path / "sessions" / "_default"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return TestClient(app)


def _valid_report_markdown(job_markdown: str, resume_markdown: str) -> str:
    report = ResumeMatcher().match(job_markdown, resume_markdown)
    return match_report_to_markdown(report)


def test_legacy_md_na_raiz_nao_e_consumido_pela_default(
    tmp_path, monkeypatch, job_markdown, resume_markdown
):
    client = _client(tmp_path, monkeypatch)
    # Legado solto direto na raiz de data/ (contrato antigo).
    legacy_path = tmp_path / "resume-match-report.md"
    legacy_path.write_text(
        _valid_report_markdown(job_markdown, resume_markdown), encoding="utf-8"
    )

    resp = client.get("/api/resume-match/latest")

    # A sessão default lê de data/sessions/_default/, então o legado é ignorado.
    assert resp.status_code == 404
    # E o arquivo legado continua intacto na raiz (não apagado, não movido).
    assert legacy_path.exists()


def test_artefato_na_sessao_default_e_consumido(
    tmp_path, monkeypatch, job_markdown, resume_markdown
):
    client = _client(tmp_path, monkeypatch)
    report_path = _default_dir(tmp_path) / "resume-match-report.md"
    report_path.write_text(
        _valid_report_markdown(job_markdown, resume_markdown), encoding="utf-8"
    )

    resp = client.get("/api/resume-match/latest")

    assert resp.status_code == 200
    assert isinstance(resp.json()["overall_score"], int)


def test_sessionpaths_default_isolado(tmp_path):
    paths = SessionPaths(None, base_dir=tmp_path)
    assert paths.dir == tmp_path / "sessions" / "_default"
