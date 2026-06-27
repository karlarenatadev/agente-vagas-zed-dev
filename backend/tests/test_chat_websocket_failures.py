"""Matriz de falhas do WebSocket de chat (`/ws/chat`).

Cobre o protocolo do endpoint sem rede, sem LLM e sem servidor real: o fluxo de
welcome/menu/quiz do Maestro é determinístico (a fixture autouse do conftest já
injeta uma OPENAI_API_KEY fake). Cada teste isola o estado em
`tmp_path/sessions/<sid>/` via `monkeypatch.setattr(config, "DATA_DIR", tmp_path)`.

Protocolo exercitado:
- Ao conectar, o servidor sempre envia primeiro `{"type":"state", ...}`.
- Sessão nova (mode "init"): state inicial → tokens → `{"type":"done"}`.
- Reconexão silenciosa (estado mode != "init", sem `replay=1`): só o state inicial;
  o welcome é pulado e o handler aguarda input (nada de tokens/done).
- `replay=1` com estado restaurado: state inicial → prompt re-emitido como tokens
  → `done`, sem emitir novo `state` e sem avançar/gravar estado.
- JSON inválido do cliente → `{"type":"error","content":"Mensagem invalida"}` e a
  conexão segue viva.
- Estado persistido corrompido → fallback seguro para sessão inicial (mode "init").
"""

import json

from fastapi.testclient import TestClient

import config
from main import app


def _drain_until_done(ws):
    """Lê mensagens até um `done`/`error`, retornando tudo que chegou."""
    msgs = []
    while True:
        m = ws.receive_json()
        msgs.append(m)
        if m.get("type") in {"done", "error"}:
            return msgs


def _session_dir(tmp_path, sid):
    d = tmp_path / "sessions" / sid
    d.mkdir(parents=True, exist_ok=True)
    return d


def _menu_state() -> str:
    return json.dumps(
        {
            "mode": "menu",
            "quiz_step": 0,
            "quiz_answers": {},
            "coach_step": 0,
            "interview_context": "",
        }
    )


def test_conexao_nova_envia_state_e_conclui_welcome(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    with TestClient(app).websocket_connect("/ws/chat?session_id=novo1") as ws:
        first = ws.receive_json()
        assert first["type"] == "state"
        assert first["content"]["mode"] == "init"

        msgs = _drain_until_done(ws)

    # O welcome de sessão nova precisa produzir tokens e terminar em `done`,
    # sem ficar preso esperando input.
    assert any(m["type"] == "token" for m in msgs)
    assert msgs[-1]["type"] == "done"


def test_mensagem_json_invalida_retorna_erro_controlado(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    with TestClient(app).websocket_connect("/ws/chat?session_id=erro1") as ws:
        assert ws.receive_json()["type"] == "state"
        _drain_until_done(ws)  # consome o welcome até o done

        ws.send_text("isto nao e json")
        resposta = ws.receive_json()

    # Erro controlado (JSON estruturado), não traceback; conexão seguiu viva o
    # suficiente para entregar a mensagem de erro.
    assert resposta["type"] == "error"
    assert resposta["content"] == "Mensagem invalida"


def test_estado_corrompido_cai_em_sessao_inicial(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    (_session_dir(tmp_path, "corr1") / "chat_state.json").write_text(
        "{lixo nao json", encoding="utf-8"
    )

    with TestClient(app).websocket_connect("/ws/chat?session_id=corr1") as ws:
        first = ws.receive_json()
        # Fallback seguro: estado corrompido não é tratado como válido nem estoura.
        assert first["type"] == "state"
        assert first["content"]["mode"] == "init"

        msgs = _drain_until_done(ws)

    assert msgs[-1]["type"] == "done"


def test_reconexao_sem_replay_nao_reemite_welcome(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    (_session_dir(tmp_path, "menu1") / "chat_state.json").write_text(
        _menu_state(), encoding="utf-8"
    )

    with TestClient(app).websocket_connect("/ws/chat?session_id=menu1") as ws:
        first = ws.receive_json()
        assert first["type"] == "state"
        assert first["content"]["mode"] == "menu"
        # Reconexão silenciosa: nada além do state inicial é re-emitido. Fecha-se
        # aqui para não bloquear esperando um welcome que (corretamente) não vem.


def test_reconexao_com_replay_reemite_prompt_sem_avancar_estado(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    state_file = _session_dir(tmp_path, "menu2") / "chat_state.json"
    state_file.write_text(_menu_state(), encoding="utf-8")

    with TestClient(app).websocket_connect("/ws/chat?session_id=menu2&replay=1") as ws:
        first = ws.receive_json()
        assert first["type"] == "state"
        assert first["content"]["mode"] == "menu"

        msgs = _drain_until_done(ws)

    assert msgs[-1]["type"] == "done"
    texto = "".join(m["content"] for m in msgs if m["type"] == "token")
    assert "ESTEIRA" in texto or "[A]" in texto
    # Replay repinta o prompt sem emitir novo `state`...
    assert not any(m["type"] == "state" for m in msgs)
    # ...e sem avançar/duplicar o estado persistido.
    persisted = json.loads(state_file.read_text(encoding="utf-8"))
    assert persisted["mode"] == "menu"


def test_desconexao_persiste_estado_e_nao_estoura(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)

    with TestClient(app).websocket_connect("/ws/chat?session_id=disc1") as ws:
        assert ws.receive_json()["type"] == "state"
        _drain_until_done(ws)  # welcome completo
        # Sai do `with` → desconecta. O handler libera recursos e persiste o
        # estado no disconnect, sem exceção.

    assert (_session_dir(tmp_path, "disc1") / "chat_state.json").exists()
