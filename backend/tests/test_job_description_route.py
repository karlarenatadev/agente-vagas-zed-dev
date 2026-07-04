"""Testes de integração da rota de análise de vaga.

Diferente dos outros, aqui subimos o app FastAPI inteiro e fazemos requisições
HTTP de verdade com o TestClient. É o teste mais próximo do uso real: passa pela
validação do Pydantic, pelo roteamento e pela escrita em arquivo.

Para não escrever no `data/` real, redirecionamos o arquivo de saída para uma
pasta temporária com `monkeypatch`.
"""

import pytest
from fastapi.testclient import TestClient

import config
from artifacts import (
    MANIFEST_FILENAME,
    get_artifact_status,
    register_artifact,
)
from main import app


def _default_dir(tmp_path):
    """Diretório resolvido pela sessão default (sem header X-Session-Id)."""
    d = tmp_path / "sessions" / "_default"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _seed_registered_dependents(base):
    paths = {
        "match": base / "resume-match-report.md",
        "reconciliation": base / "reconciliation.md",
        "tailoring": base / "resume-tailoring-suggestions.md",
        "pdi": base / "pdi-plan.md",
        "interview": base / "interview-session.md",
    }
    for name, path in paths.items():
        path.write_text(f"artefato antigo: {name}", encoding="utf-8")
        register_artifact(
            base,
            name,
            path,
            generator_version=f"{name}:test",
        )
    return paths


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Redireciona a pasta de dados para a pasta temporária do teste. A sessão
    # default (sem header X-Session-Id) escreve em data/sessions/_default/, então
    # isolar a DATA_DIR isola tudo. monkeypatch desfaz sozinho ao fim do teste.
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return TestClient(app)


VAGA_VALIDA = (
    "Analista de Dados Júnior na Acme. Requisitos: Python, SQL e Power BI. "
    "Boa comunicação e trabalho em equipe."
)


def test_analyze_retorna_200_e_skills(client):
    resp = client.post("/api/job-description/analyze", json={"description": VAGA_VALIDA})

    assert resp.status_code == 200
    corpo = resp.json()
    assert "Python" in corpo["hard_skills"]
    assert "SQL" in corpo["hard_skills"]


def test_analyze_recusa_descricao_curta_com_400(client, tmp_path):
    base = _default_dir(tmp_path)
    source_path = base / "job-description-analysis.md"
    source_path.write_text("vaga anterior", encoding="utf-8")
    register_artifact(
        base,
        "job_description",
        source_path,
        generator_version="job-description:test",
    )
    manifest_path = base / MANIFEST_FILENAME
    manifest_before = manifest_path.read_bytes()

    # Menos de 40 caracteres: a rota tem que recusar com 400.
    resp = client.post("/api/job-description/analyze", json={"description": "vaga"})

    assert resp.status_code == 400
    assert manifest_path.read_bytes() == manifest_before
    assert source_path.read_text(encoding="utf-8") == "vaga anterior"


def test_analyze_persiste_e_latest_le_de_volta(client):
    # Fluxo completo: analisa (grava o arquivo) e depois lê via GET /latest.
    client.post("/api/job-description/analyze", json={"description": VAGA_VALIDA})

    resp = client.get("/api/job-description/latest")

    assert resp.status_code == 200
    assert "Python" in resp.json()["hard_skills"]


def test_analyze_marca_dependentes_stale_sem_apagar(client, tmp_path):
    base = _default_dir(tmp_path)
    dependent_files = _seed_registered_dependents(base)

    resp = client.post("/api/job-description/analyze", json={"description": VAGA_VALIDA})

    assert resp.status_code == 200
    source_path = base / "job-description-analysis.md"
    assert get_artifact_status(
        base,
        "job_description",
        artifact_path=source_path,
    ) == "current"
    assert all(path.exists() for path in dependent_files.values())
    assert all(
        get_artifact_status(base, name, artifact_path=path) == "stale"
        for name, path in dependent_files.items()
    )


def test_analyze_sessao_legada_preserva_derivados(client, tmp_path):
    base = _default_dir(tmp_path)
    match_path = base / "resume-match-report.md"
    match_path.write_text("match legado", encoding="utf-8")

    resp = client.post("/api/job-description/analyze", json={"description": VAGA_VALIDA})

    assert resp.status_code == 200
    assert match_path.read_text(encoding="utf-8") == "match legado"
    assert get_artifact_status(base, "match", artifact_path=match_path) == "legacy"


def test_analyze_manifesto_corrompido_retorna_409_sem_alterar_entrada(
    client,
    tmp_path,
):
    base = _default_dir(tmp_path)
    source_path = base / "job-description-analysis.md"
    source_path.write_text("vaga anterior", encoding="utf-8")
    manifest_path = base / MANIFEST_FILENAME
    invalid_manifest = '{"schema_version": 1, "artifacts":'
    manifest_path.write_text(invalid_manifest, encoding="utf-8")

    resp = client.post("/api/job-description/analyze", json={"description": VAGA_VALIDA})

    assert resp.status_code == 409
    assert source_path.read_text(encoding="utf-8") == "vaga anterior"
    assert manifest_path.read_text(encoding="utf-8") == invalid_manifest


def test_latest_retorna_404_sem_analise_previa(client):
    # Sem nenhuma análise gravada, /latest tem que dar 404.
    resp = client.get("/api/job-description/latest")

    assert resp.status_code == 404
