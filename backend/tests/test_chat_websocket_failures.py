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
from fastapi.websockets import WebSocketDisconnect
import pytest

import config
from main import app
from routers import chat as chat_router


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


@pytest.mark.parametrize(
    ("case_name", "payload"),
    [
        ("lista", []),
        ("numero", 42),
        ("nulo", None),
        ("sem_content", {"type": "message"}),
        ("content_nulo", {"type": "message", "content": None}),
        ("content_numero", {"type": "message", "content": 42}),
        ("content_lista", {"type": "message", "content": ["texto"]}),
        ("content_objeto", {"type": "message", "content": {"text": "oi"}}),
        ("content_vazio", {"type": "message", "content": "   "}),
        ("sem_type", {"content": "oi"}),
        ("type_invalido", {"type": "command", "content": "oi"}),
        (
            "date_filter_invalido",
            {"type": "message", "content": "oi", "date_filter": "1y"},
        ),
    ],
)
def test_payload_recuperavel_invalido_nao_executa_agente_nem_altera_estado(
    case_name,
    payload,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    state_file = _session_dir(tmp_path, f"invalido-{case_name}") / "chat_state.json"
    original_state = _menu_state()
    state_file.write_text(original_state, encoding="utf-8")

    async def forbidden_run(self, context):
        raise AssertionError("payload invalido chegou ao Maestro")
        yield  # pragma: no cover

    monkeypatch.setattr(chat_router.MaestroAgent, "run", forbidden_run)

    with TestClient(app).websocket_connect(
        f"/ws/chat?session_id=invalido-{case_name}"
    ) as ws:
        assert ws.receive_json()["type"] == "state"

        ws.send_text(json.dumps(payload))
        response = ws.receive_json()

        assert response["type"] == "error"
        assert "type='message'" in response["content"]
        assert state_file.read_text(encoding="utf-8") == original_state

        # Um segundo frame invalido comprova que o primeiro erro foi recuperavel.
        ws.send_text("json invalido")
        assert ws.receive_json() == {
            "type": "error",
            "content": "Mensagem invalida",
        }


def test_mensagem_acima_do_limite_fecha_com_1009_sem_persistir(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "WS_MAX_MESSAGE_CHARS", 8)
    state_file = _session_dir(tmp_path, "grande1") / "chat_state.json"
    original_state = _menu_state()
    state_file.write_text(original_state, encoding="utf-8")

    async def forbidden_run(self, context):
        raise AssertionError("mensagem excessiva chegou ao Maestro")
        yield  # pragma: no cover

    monkeypatch.setattr(chat_router.MaestroAgent, "run", forbidden_run)

    with TestClient(app).websocket_connect("/ws/chat?session_id=grande1") as ws:
        assert ws.receive_json()["type"] == "state"
        ws.send_json({"type": "message", "content": "123456789"})

        with pytest.raises(WebSocketDisconnect) as closed:
            ws.receive_json()

        assert closed.value.code == 1009

    assert state_file.read_text(encoding="utf-8") == original_state


def test_payload_valido_encaminha_conteudo_normalizado_e_filtro_suportado(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    state_file = _session_dir(tmp_path, "valido1") / "chat_state.json"
    state_file.write_text(_menu_state(), encoding="utf-8")
    contexts = []

    async def fake_run(self, context):
        contexts.append(context)
        yield "ok"

    monkeypatch.setattr(chat_router.MaestroAgent, "run", fake_run)

    with TestClient(app).websocket_connect("/ws/chat?session_id=valido1") as ws:
        assert ws.receive_json()["type"] == "state"
        ws.send_json(
            {
                "type": "message",
                "content": "  buscar vagas  ",
                "date_filter": "7d",
            }
        )
        assert ws.receive_json() == {"type": "token", "content": "ok"}
        assert ws.receive_json() == {"type": "done", "content": ""}

    assert contexts[0]["message"] == "buscar vagas"
    assert contexts[0]["date_filter"] == "7d"
