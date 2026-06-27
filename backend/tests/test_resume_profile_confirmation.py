"""Testes do fluxo currículo -> perfil com confirmação explícita.

Garantem que o upload de currículo NÃO grava mais o `user-profile.md` de forma
silenciosa e que a atualização do perfil só acontece via `/apply-profile` com
confirmação explícita. Todos os artefatos são sintéticos e gravados em
`tmp_path`; nenhum teste lê ou escreve no diretório `data/` real.
"""

from fastapi.testclient import TestClient

import config
from main import app

RESUME_CONTENT = (
    "Nome: Pessoa Teste\n"
    "Analista de dados junior com experiencia em Python, SQL, Excel e Power BI.\n"
    "Boa comunicacao, trabalho em equipe e projetos de dashboards."
)


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return TestClient(app)


def _default_dir(tmp_path):
    """Diretório resolvido pela sessão default (sem header X-Session-Id)."""
    d = tmp_path / "sessions" / "_default"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _profile_path(tmp_path):
    return _default_dir(tmp_path) / "user-profile.md"


def _upload(client: TestClient):
    return client.post(
        "/api/resume/upload",
        files={"file": ("curriculo.txt", RESUME_CONTENT.encode("utf-8"), "text/plain")},
    )


def _parse_profile(content: str) -> dict[str, str]:
    profile: dict[str, str] = {}
    for line in content.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        profile[key.strip()] = value.strip()
    return profile


def test_upload_nao_cria_nem_altera_perfil(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = _upload(client)

    assert response.status_code == 200
    body = response.json()
    # O upload não pode mais gravar o perfil de forma silenciosa.
    assert not _profile_path(tmp_path).exists()
    assert body["profile_updated"] is False
    assert body["profile_confirmation_required"] is True
    assert body["profile_suggestions"]


def test_upload_nao_sobrescreve_perfil_existente(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    profile_path = _profile_path(tmp_path)
    known_content = (
        "Área de interesse: Frontend\n"
        "Nível de experiência: Pleno\n"
        "Concluído: true"
    )
    profile_path.write_text(known_content, encoding="utf-8")
    before = profile_path.read_bytes()

    response = _upload(client)

    assert response.status_code == 200
    # Bytes do perfil existente permanecem inalterados após o upload.
    assert profile_path.read_bytes() == before


def test_apply_profile_sem_confirmacao_retorna_400_e_nao_altera(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    assert _upload(client).status_code == 200

    response = client.post("/api/resume/apply-profile", json={"confirm": False})

    assert response.status_code == 400
    assert response.json()["detail"]
    # Sem confirmação, nada é gravado: o perfil continua inexistente.
    assert not _profile_path(tmp_path).exists()


def test_apply_profile_com_confirmacao_atualiza_somente_campos_aprovados(
    tmp_path, monkeypatch
):
    client = _client(tmp_path, monkeypatch)
    assert _upload(client).status_code == 200

    response = client.post(
        "/api/resume/apply-profile",
        json={"confirm": True, "fields": ["Área de interesse"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["updated_fields"] == ["Área de interesse"]

    profile = _parse_profile(
        _profile_path(tmp_path).read_text(encoding="utf-8")
    )
    # Campo aprovado foi preenchido.
    assert profile["Área de interesse"]
    # Campos não aprovados permanecem vazios.
    assert profile.get("Soft skills", "") == ""
    assert profile.get("Habilidades atuais", "") == ""


def test_apply_profile_curriculo_ausente_retorna_400(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    response = client.post("/api/resume/apply-profile", json={"confirm": True})

    assert response.status_code == 400
    assert response.json()["detail"]
