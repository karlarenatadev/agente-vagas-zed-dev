"""
Router WebSocket — canal de comunicação em tempo real com o frontend.

Protocolo de mensagens:
- Cliente → Servidor: JSON { type: "message", content: str, state: SessionState }
- Servidor → Cliente: JSON { type: "token"|"state"|"error", content: str }

Tokens de estado embutidos no stream:
  __STATE__:menu              → modo menu
  __STATE__:quiz:N            → modo quiz, passo N
  __STATE__:quiz:N:BASE64     → modo quiz, passo N, com respostas parciais
  __STATE__:quiz_resume       → aguardando decisão de continuar/refazer
  __STATE__:coach:N:CONTEXT   → modo coach, passo N
  __STATE__:agent_running:X   → agente X em execução
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from agents.maestro import MaestroAgent

router = APIRouter()


def _parse_state_token(token: str) -> dict[str, Any] | None:
    """
    Extrai informações de estado de um token __STATE__:...
    Retorna dict com campos de estado ou None se não for token de estado.
    """
    if not token.startswith("__STATE__:"):
        return None

    parts = token[len("__STATE__:"):].split(":", 2)
    mode = parts[0]

    state: dict[str, Any] = {"mode": mode}

    if mode == "quiz" and len(parts) >= 2:
        state["quiz_step"] = int(parts[1])
        if len(parts) == 3:
            # Decodifica respostas parciais
            try:
                state["quiz_answers"] = json.loads(base64.b64decode(parts[2]).decode())
            except Exception:
                state["quiz_answers"] = {}

    elif mode == "coach" and len(parts) >= 2:
        state["coach_step"] = int(parts[1])
        if len(parts) == 3:
            state["interview_context"] = parts[2]

    return state


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Endpoint WebSocket principal.
    Mantém estado da sessão em memória durante a conexão.
    """
    await websocket.accept()

    # Estado inicial da sessão
    session: dict[str, Any] = {
        "mode": "init",
        "quiz_step": 0,
        "quiz_answers": {},
        "coach_step": 0,
        "interview_context": "",
    }

    maestro = MaestroAgent()

    # Envia mensagem de boas-vindas ao conectar
    try:
        context = {**session, "message": ""}
        buffer = ""

        async for token in maestro.run(context):
            # Verifica se é token de estado
            if "__STATE__:" in token:
                # Pode haver texto antes do token de estado
                parts = token.split("__STATE__:")
                text_part = parts[0]
                state_part = "__STATE__:" + parts[1].split("\n")[0]

                if text_part:
                    await websocket.send_json({"type": "token", "content": text_part})

                state_update = _parse_state_token(state_part)
                if state_update:
                    session.update(state_update)
                    await websocket.send_json({"type": "state", "content": session})
            else:
                await websocket.send_json({"type": "token", "content": token})

        await websocket.send_json({"type": "done", "content": ""})

    except WebSocketDisconnect:
        return
    except Exception as e:
        await websocket.send_json({"type": "error", "content": str(e)})

    # Loop principal de mensagens
    while True:
        try:
            raw = await websocket.receive_text()
            data = json.loads(raw)

            if data.get("type") == "message":
                user_message = data.get("content", "").strip()

                # Monta contexto com estado atual da sessão
                context = {**session, "message": user_message}

                async for token in maestro.run(context):
                    if "__STATE__:" in token:
                        parts = token.split("__STATE__:")
                        text_part = parts[0]
                        state_raw = parts[1].split("\n")[0]
                        state_part = "__STATE__:" + state_raw

                        if text_part:
                            await websocket.send_json({"type": "token", "content": text_part})

                        state_update = _parse_state_token(state_part)
                        if state_update:
                            session.update(state_update)
                            await websocket.send_json({"type": "state", "content": session})
                    else:
                        await websocket.send_json({"type": "token", "content": token})

                await websocket.send_json({"type": "done", "content": ""})

        except WebSocketDisconnect:
            break
        except json.JSONDecodeError:
            await websocket.send_json({"type": "error", "content": "Mensagem inválida"})
        except Exception as e:
            await websocket.send_json({"type": "error", "content": str(e)})
            await websocket.send_json({"type": "done", "content": ""})
