"""Testes HTTP mínimos dos fluxos críticos do backend.

Todos os artefatos são sintéticos e gravados na pasta da sessão default
(`tmp_path/sessions/_default/`); nenhum teste lê ou escreve no diretório `data/`
real e nenhum caminho depende de OpenAI/Firecrawl.
"""

from fastapi.testclient import TestClient

import artifacts
import config
from agents.pdi_generator import PdiGenerator, pdi_from_markdown
from agents.resume_matcher import ResumeMatcher, match_report_to_markdown
from agents.resume_tailor import ResumeTailor, tailoring_to_markdown
from artifacts import (
    MANIFEST_FILENAME,
    calculate_content_hash,
    get_artifact_status,
    load_manifest,
    mark_dependents_stale,
    register_artifact,
)
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


def _seed_registered_dependents(base) -> dict[str, object]:
    paths = {
        "match": base / "resume-match-report.md",
        "reconciliation": base / "reconciliation.md",
        "tailoring": base / "resume-tailoring-suggestions.md",
        "pdi": base / "pdi-plan.md",
        "interview": base / "interview-session.md",
    }
    for name, path in paths.items():
        _write(path, f"artefato antigo: {name}")
        register_artifact(
            base,
            name,
            path,
            generator_version=f"{name}:test",
        )
    return paths


def _write_match_report(tmp_path, job_markdown: str, resume_markdown: str) -> str:
    report = ResumeMatcher().match(job_markdown, resume_markdown)
    markdown = match_report_to_markdown(report)
    _write(_default_dir(tmp_path) / "resume-match-report.md", markdown)
    return markdown


def _write_tailoring(
    tmp_path,
    resume_markdown: str,
    job_markdown: str,
    match_markdown: str,
) -> str:
    result = ResumeTailor().generate(resume_markdown, job_markdown, match_markdown)
    markdown = tailoring_to_markdown(result)
    _write(_default_dir(tmp_path) / "resume-tailoring-suggestions.md", markdown)
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
    assert (_default_dir(tmp_path) / "resume-analysis.md").exists()

    latest = client.get("/api/resume/latest")
    assert latest.status_code == 200
    assert "Python" in latest.json()["technical_skills"]


def test_resume_upload_marca_dependentes_stale_sem_apagar(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    dependent_files = _seed_registered_dependents(base)

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
    assert (base / "resume-analysis.md").exists()
    assert get_artifact_status(
        base,
        "resume",
        artifact_path=base / "resume-analysis.md",
    ) == "current"
    assert all(path.exists() for path in dependent_files.values())
    assert all(
        get_artifact_status(base, name, artifact_path=path) == "stale"
        for name, path in dependent_files.items()
    )


def test_resume_upload_sessao_legada_preserva_derivados(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    dependent_path = base / "resume-match-report.md"
    _write(dependent_path, "match legado")
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
    assert dependent_path.read_text(encoding="utf-8") == "match legado"
    assert get_artifact_status(base, "match", artifact_path=dependent_path) == "legacy"
    assert get_artifact_status(
        base,
        "resume",
        artifact_path=base / "resume-analysis.md",
    ) == "current"


def test_resume_upload_manifesto_parcial_preserva_nao_registrados(
    tmp_path,
    monkeypatch,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    match_path = base / "resume-match-report.md"
    interview_path = base / "interview-session.md"
    _write(match_path, "match registrado")
    _write(interview_path, "entrevista legada")
    register_artifact(base, "match", match_path, generator_version="match:test")
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
    assert get_artifact_status(base, "match", artifact_path=match_path) == "stale"
    assert (
        get_artifact_status(base, "interview", artifact_path=interview_path)
        == "legacy"
    )
    assert match_path.exists()
    assert interview_path.exists()


def test_resume_upload_recusa_extensao_invalida(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    source_path = base / "resume-analysis.md"
    _write(source_path, "currículo anterior")
    register_artifact(base, "resume", source_path, generator_version="resume:test")
    manifest_path = base / MANIFEST_FILENAME
    manifest_before = manifest_path.read_bytes()

    response = client.post(
        "/api/resume/upload",
        files={"file": ("curriculo.exe", b"conteudo suficiente para teste", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert manifest_path.read_bytes() == manifest_before
    assert source_path.read_text(encoding="utf-8") == "currículo anterior"


def test_resume_upload_manifesto_corrompido_retorna_409_sem_alterar_entrada(
    tmp_path,
    monkeypatch,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    source_path = base / "resume-analysis.md"
    _write(source_path, "currículo anterior")
    manifest_path = base / MANIFEST_FILENAME
    invalid_manifest = '{"schema_version": 1, "artifacts":'
    _write(manifest_path, invalid_manifest)
    content = (
        "Nome: Pessoa Teste\n"
        "Analista de dados junior com experiencia em Python, SQL, Excel e Power BI.\n"
        "Boa comunicacao, trabalho em equipe e projetos de dashboards."
    )

    response = client.post(
        "/api/resume/upload",
        files={"file": ("curriculo.txt", content.encode("utf-8"), "text/plain")},
    )

    assert response.status_code == 409
    assert source_path.read_text(encoding="utf-8") == "currículo anterior"
    assert manifest_path.read_text(encoding="utf-8") == invalid_manifest


def test_resume_upload_falha_ao_salvar_manifesto_preserva_entrada(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    client = TestClient(app, raise_server_exceptions=False)
    base = _default_dir(tmp_path)
    source_path = base / "resume-analysis.md"
    _write(source_path, "currículo anterior")
    content = (
        "Nome: Pessoa Teste\n"
        "Analista de dados junior com experiencia em Python, SQL, Excel e Power BI.\n"
        "Boa comunicacao, trabalho em equipe e projetos de dashboards."
    )

    def fail_manifest_write(path, manifest_content):
        raise OSError("falha simulada no manifesto")

    monkeypatch.setattr(artifacts, "write_text_atomic", fail_manifest_write)

    response = client.post(
        "/api/resume/upload",
        files={"file": ("curriculo.txt", content.encode("utf-8"), "text/plain")},
    )

    assert response.status_code == 409
    assert "manifesto" in response.json()["detail"].casefold()
    assert source_path.read_text(encoding="utf-8") == "currículo anterior"
    assert not (base / MANIFEST_FILENAME).exists()


def test_resume_upload_recusa_pdf_sem_assinatura_valida(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.post(
        "/api/resume/upload",
        files={"file": ("curriculo.pdf", b"conteudo que nao e pdf", "application/pdf")},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False


def test_resume_upload_recusa_arquivo_acima_do_limite(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    monkeypatch.setattr(config, "MAX_RESUME_UPLOAD_SIZE", 12)

    response = client.post(
        "/api/resume/upload",
        files={"file": ("curriculo.pdf", b"%PDF-" + (b"x" * 32), "application/pdf")},
    )

    assert response.status_code == 413
    assert response.json()["success"] is False


def test_match_sem_curriculo_retorna_400(tmp_path, monkeypatch, job_markdown):
    client = _client(tmp_path, monkeypatch)
    _write(_default_dir(tmp_path) / "job-description-analysis.md", job_markdown)

    response = client.post("/api/resume-match/analyze", json={})

    assert response.status_code == 400
    assert "curr" in response.json()["detail"].casefold()


def test_match_sem_vaga_valida_retorna_400(tmp_path, monkeypatch, resume_markdown):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", "conteudo invalido")
    _write(base / "resume-analysis.md", resume_markdown)
    pdi_path = base / "pdi-plan.md"
    _write(pdi_path, "pdi anterior")
    register_artifact(base, "pdi", pdi_path, generator_version="pdi:test")
    manifest_path = base / MANIFEST_FILENAME
    manifest_before = manifest_path.read_bytes()

    response = client.post("/api/resume-match/analyze", json={})

    assert response.status_code == 400
    assert "vaga" in response.json()["detail"].casefold()
    assert manifest_path.read_bytes() == manifest_before


def test_match_com_artefatos_validos_persiste_relatorio(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)

    response = client.post("/api/resume-match/analyze", json={})

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["overall_score"], int)
    match_path = base / "resume-match-report.md"
    assert match_path.exists()
    assert get_artifact_status(base, "match", artifact_path=match_path) == "current"
    metadata = load_manifest(base).artifacts["match"]
    assert metadata.generator_version == "match:v1"
    assert metadata.input_hashes == {
        "resume": calculate_content_hash(resume_markdown.strip()),
        "job_description": calculate_content_hash(job_markdown.strip()),
    }


def test_match_marca_derivados_stale_sem_apagar(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    dependent_files = _seed_registered_dependents(base)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)

    response = client.post("/api/resume-match/analyze", json={})

    assert response.status_code == 200
    assert get_artifact_status(
        base,
        "match",
        artifact_path=dependent_files["match"],
    ) == "current"
    expected_stale = {"reconciliation", "tailoring", "pdi", "interview"}
    assert all(dependent_files[name].exists() for name in expected_stale)
    assert all(
        get_artifact_status(
            base,
            name,
            artifact_path=dependent_files[name],
        )
        == "stale"
        for name in expected_stale
    )


def test_sugestoes_sem_relatorio_de_match_retorna_400(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)

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
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)
    _write_match_report(tmp_path, job_markdown, resume_markdown)

    response = client.post("/api/resume-tailoring/generate", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["summary_suggestions"]
    tailoring_path = base / "resume-tailoring-suggestions.md"
    assert tailoring_path.exists()
    assert (
        get_artifact_status(base, "tailoring", artifact_path=tailoring_path)
        == "current"
    )


def test_sugestoes_bloqueiam_match_stale_sem_apagar(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)
    match_markdown = _write_match_report(tmp_path, job_markdown, resume_markdown)
    match_path = base / "resume-match-report.md"
    register_artifact(
        base,
        "match",
        match_path,
        input_hashes={
            "resume": calculate_content_hash(resume_markdown.strip()),
            "job_description": calculate_content_hash(job_markdown.strip()),
        },
        generator_version="match:v1",
    )
    mark_dependents_stale(base, "resume")

    response = client.post("/api/resume-tailoring/generate", json={})

    assert response.status_code == 409
    assert "obsoleto" in response.json()["detail"].casefold()
    assert match_path.read_text(encoding="utf-8") == match_markdown
    assert not (base / "resume-tailoring-suggestions.md").exists()


def test_sugestoes_bloqueiam_match_corrompido_sem_apagar(
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
    match_path = base / "resume-match-report.md"
    register_artifact(base, "match", match_path, generator_version="match:v1")
    _write(match_path, match_path.read_text(encoding="utf-8") + "\nalterado")

    response = client.post("/api/resume-tailoring/generate", json={})

    assert response.status_code == 409
    assert "corrompido" in response.json()["detail"].casefold()
    assert match_path.read_text(encoding="utf-8").endswith("alterado")
    assert not (base / "resume-tailoring-suggestions.md").exists()


def test_pdi_sem_sugestoes_retorna_400(
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

    response = client.post("/api/pdi/generate", json={})

    assert response.status_code == 400
    assert "sugest" in response.json()["detail"].casefold()


def test_pdi_sem_relatorio_de_match_retorna_400(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)

    response = client.post("/api/pdi/generate", json={})

    assert response.status_code == 400
    detail = response.json()["detail"].casefold()
    assert "compar" in detail or "ader" in detail


def test_pdi_com_artefatos_validos_persiste_e_le_latest(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)
    match_markdown = _write_match_report(tmp_path, job_markdown, resume_markdown)
    _write_tailoring(tmp_path, resume_markdown, job_markdown, match_markdown)

    response = client.post("/api/pdi/generate", json={})

    assert response.status_code == 200
    body = response.json()
    assert body["main_goal"]
    persisted = (base / "pdi-plan.md").read_text(encoding="utf-8")
    assert pdi_from_markdown(persisted) is not None
    assert (
        get_artifact_status(base, "pdi", artifact_path=base / "pdi-plan.md")
        == "current"
    )

    latest = client.get("/api/pdi/latest")
    assert latest.status_code == 200
    assert latest.json()["main_goal"] == body["main_goal"]


def test_pdi_bloqueia_tailoring_stale_sem_apagar(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)
    match_markdown = _write_match_report(tmp_path, job_markdown, resume_markdown)
    tailoring_markdown = _write_tailoring(
        tmp_path,
        resume_markdown,
        job_markdown,
        match_markdown,
    )
    match_path = base / "resume-match-report.md"
    tailoring_path = base / "resume-tailoring-suggestions.md"
    register_artifact(
        base,
        "match",
        match_path,
        input_hashes={
            "resume": calculate_content_hash(resume_markdown.strip()),
            "job_description": calculate_content_hash(job_markdown.strip()),
        },
        generator_version="match:v1",
    )
    register_artifact(
        base,
        "tailoring",
        tailoring_path,
        input_hashes={
            "resume": calculate_content_hash(resume_markdown.strip()),
            "job_description": calculate_content_hash(job_markdown.strip()),
            "match": calculate_content_hash(match_markdown.strip()),
            "focus": calculate_content_hash("vaga"),
        },
        generator_version="tailoring:v1",
    )
    mark_dependents_stale(base, "focus")

    response = client.post("/api/pdi/generate", json={})

    assert response.status_code == 409
    assert "tailoring" in response.json()["detail"].casefold()
    assert "obsoleto" in response.json()["detail"].casefold()
    assert tailoring_path.read_text(encoding="utf-8") == tailoring_markdown
    assert not (base / "pdi-plan.md").exists()


def test_reconciliacao_bloqueia_match_stale(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    profile = (
        "Área de interesse: Dados\n"
        "Nível de experiência: Pleno\n"
        "Habilidades atuais: Python, SQL\n"
        "Funções alvo: Analista de Dados\n"
        "Concluído: true\n"
    )
    _write(base / "user-profile.md", profile)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)
    match_markdown = _write_match_report(tmp_path, job_markdown, resume_markdown)
    match_path = base / "resume-match-report.md"
    register_artifact(
        base,
        "match",
        match_path,
        input_hashes={
            "resume": calculate_content_hash(resume_markdown),
            "job_description": calculate_content_hash(job_markdown),
        },
        generator_version="match:v1",
    )
    mark_dependents_stale(base, "resume")

    response = client.post("/api/reconciliation/analyze", json={})

    assert response.status_code == 409
    assert "match" in response.json()["detail"].casefold()
    assert "obsoleto" in response.json()["detail"].casefold()
    assert match_path.read_text(encoding="utf-8") == match_markdown
    assert not (base / "reconciliation.md").exists()


def test_reconciliacao_legada_e_registrada_apos_geracao(
    tmp_path,
    monkeypatch,
    job_markdown,
    resume_markdown,
):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    profile = (
        "Área de interesse: Dados\n"
        "Nível de experiência: Pleno\n"
        "Habilidades atuais: Python, SQL\n"
        "Funções alvo: Analista de Dados\n"
        "Concluído: true\n"
    )
    _write(base / "user-profile.md", profile)
    _write(base / "job-description-analysis.md", job_markdown)
    _write(base / "resume-analysis.md", resume_markdown)
    _write_match_report(tmp_path, job_markdown, resume_markdown)

    response = client.post("/api/reconciliation/analyze", json={})

    assert response.status_code == 200
    reconciliation_path = base / "reconciliation.md"
    assert reconciliation_path.exists()
    assert (
        get_artifact_status(
            base,
            "reconciliation",
            artifact_path=reconciliation_path,
        )
        == "current"
    )
