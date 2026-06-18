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
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Redireciona a pasta de dados para a pasta temporária do teste. A sessão
    # default (sem header X-Session-Id) escreve direto em config.DATA_DIR, então
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


def test_analyze_recusa_descricao_curta_com_400(client):
    # Menos de 40 caracteres: a rota tem que recusar com 400.
    resp = client.post("/api/job-description/analyze", json={"description": "vaga"})

    assert resp.status_code == 400


def test_analyze_persiste_e_latest_le_de_volta(client):
    # Fluxo completo: analisa (grava o arquivo) e depois lê via GET /latest.
    client.post("/api/job-description/analyze", json={"description": VAGA_VALIDA})

    resp = client.get("/api/job-description/latest")

    assert resp.status_code == 200
    assert "Python" in resp.json()["hard_skills"]


def test_analyze_invalida_artefatos_dependentes(client, tmp_path):
    dependent_files = [
        tmp_path / "resume-match-report.md",
        tmp_path / "resume-tailoring-suggestions.md",
        tmp_path / "pdi-plan.md",
    ]
    for path in dependent_files:
        path.write_text("artefato antigo", encoding="utf-8")

    resp = client.post("/api/job-description/analyze", json={"description": VAGA_VALIDA})

    assert resp.status_code == 200
    assert (tmp_path / "job-description-analysis.md").exists()
    assert all(not path.exists() for path in dependent_files)


def test_latest_retorna_404_sem_analise_previa(client):
    # Sem nenhuma análise gravada, /latest tem que dar 404.
    resp = client.get("/api/job-description/latest")

    assert resp.status_code == 404
