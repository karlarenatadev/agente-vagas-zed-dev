"""Testes das rotas de candidaturas (applications.json).

Cobre o CRUD que não tinha teste nenhum e valida a escrita atômica adicionada
junto com o lock. Como `applications.py` resolve o caminho do arquivo no import,
redirecionamos `APPLICATIONS_FILE` para a pasta temporária com `monkeypatch`.
"""

import json

import pytest
from fastapi.testclient import TestClient

import config
from main import app


def _default_dir(tmp_path):
    """Diretório resolvido pela sessão default (sem header X-Session-Id)."""
    d = tmp_path / "sessions" / "_default"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture
def client(tmp_path, monkeypatch):
    # A sessão default grava em data/sessions/_default/applications.json; isolar
    # a DATA_DIR aponta tudo para a pasta temporária do teste.
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return TestClient(app)


def _nova_candidatura(**over):
    base = {
        "titulo": "Analista de Dados",
        "empresa": "Acme",
        "localizacao": "Remoto",
        "link": "https://exemplo.com/vaga",
    }
    base.update(over)
    return base


def test_lista_vazia_no_inicio(client):
    resp = client.get("/api/applications/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_arquivo_vazio_eh_lista_vazia_valida(client, tmp_path):
    base = _default_dir(tmp_path)
    arquivo = base / "applications.json"
    arquivo.write_text("", encoding="utf-8")

    resp = client.get("/api/applications/")

    assert resp.status_code == 200
    assert resp.json() == []
    assert arquivo.read_text(encoding="utf-8") == ""
    assert list(base.glob("applications.corrupt-*.json")) == []


def test_json_corrompido_retorna_409_cria_backup_e_preserva_original(client, tmp_path):
    base = _default_dir(tmp_path)
    arquivo = base / "applications.json"
    conteudo_corrompido = '[{"id": "app-1", "empresa": "Acme"}'
    arquivo.write_text(conteudo_corrompido, encoding="utf-8")

    resp = client.get("/api/applications/")

    assert resp.status_code == 409
    assert "corrompido" in resp.json()["detail"]
    assert arquivo.read_text(encoding="utf-8") == conteudo_corrompido
    backups = list(base.glob("applications.corrupt-*.json"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == conteudo_corrompido


def test_json_corrompido_bloqueia_create_sem_sobrescrever(client, tmp_path):
    base = _default_dir(tmp_path)
    arquivo = base / "applications.json"
    conteudo_corrompido = '{"id": "objeto-nao-lista"}'
    arquivo.write_text(conteudo_corrompido, encoding="utf-8")

    resp = client.post("/api/applications/", json=_nova_candidatura())

    assert resp.status_code == 409
    assert "corrompido" in resp.json()["detail"]
    assert arquivo.read_text(encoding="utf-8") == conteudo_corrompido
    backups = list(base.glob("applications.corrupt-*.json"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == conteudo_corrompido


def test_cria_e_lista(client):
    criada = client.post("/api/applications/", json=_nova_candidatura()).json()

    assert criada["id"]                      # ganhou um id
    assert criada["status"] == "salva"       # default
    assert criada["data_salva"]              # carimbo de criação

    lista = client.get("/api/applications/").json()
    assert len(lista) == 1
    assert lista[0]["empresa"] == "Acme"


def test_update_status_aplicada_carimba_data(client):
    criada = client.post("/api/applications/", json=_nova_candidatura()).json()

    resp = client.patch(f"/api/applications/{criada['id']}", json={"status": "aplicada"})

    assert resp.status_code == 200
    atualizada = resp.json()
    assert atualizada["status"] == "aplicada"
    assert atualizada["data_aplicacao"]  # preenchida automaticamente


def test_update_inexistente_da_404(client):
    resp = client.patch("/api/applications/nao-existe", json={"status": "aplicada"})
    assert resp.status_code == 404


def test_delete_remove_e_404_no_segundo(client):
    criada = client.post("/api/applications/", json=_nova_candidatura()).json()

    primeira = client.delete(f"/api/applications/{criada['id']}")
    assert primeira.status_code == 200
    assert client.get("/api/applications/").json() == []

    # Apagar de novo: já não existe.
    segunda = client.delete(f"/api/applications/{criada['id']}")
    assert segunda.status_code == 404


def test_stats_conta_por_status(client):
    client.post("/api/applications/", json=_nova_candidatura())
    segunda = client.post("/api/applications/", json=_nova_candidatura(empresa="Beta")).json()
    client.patch(f"/api/applications/{segunda['id']}", json={"status": "aplicada"})

    stats = client.get("/api/applications/stats").json()

    assert stats["total"] == 2
    assert stats["by_status"]["salva"] == 1
    assert stats["by_status"]["aplicada"] == 1


def test_sessoes_diferentes_nao_compartilham_dados(client):
    # O coração do isolamento multiusuário: a sessão "alice" cria uma
    # candidatura; "bob" não pode enxergá-la, e vice-versa.
    headers_alice = {"X-Session-Id": "alice"}
    headers_bob = {"X-Session-Id": "bob"}

    client.post("/api/applications/", json=_nova_candidatura(empresa="AliceCorp"), headers=headers_alice)

    lista_alice = client.get("/api/applications/", headers=headers_alice).json()
    lista_bob = client.get("/api/applications/", headers=headers_bob).json()

    assert len(lista_alice) == 1
    assert lista_alice[0]["empresa"] == "AliceCorp"
    assert lista_bob == []  # bob não vê nada da alice


def test_escrita_atomica_nao_deixa_tmp_e_json_valido(client, tmp_path):
    client.post("/api/applications/", json=_nova_candidatura())

    base = _default_dir(tmp_path)
    arquivo = base / "applications.json"
    # O arquivo definitivo existe, é JSON válido...
    conteudo = json.loads(arquivo.read_text(encoding="utf-8"))
    assert isinstance(conteudo, list) and len(conteudo) == 1
    # ...e nenhum arquivo temporário ficou para trás.
    assert not (base / "applications.json.tmp").exists()
