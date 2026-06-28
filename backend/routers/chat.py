"""Router WebSocket para comunicacao em tempo real com o frontend."""

from __future__ import annotations

import base64
import binascii
import json
from typing import Any, Literal

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

import config
from agents.base import LLMProviderError
from agents.maestro import MaestroAgent
from logging_config import get_logger
from session import (
    SessionPaths,
    get_session_lock,
    read_text_async,
    write_text_atomic_async,
)


router = APIRouter()
logger = get_logger(__name__)


class IncomingChatMessage(BaseModel):
    """Contrato estrito para mensagens recebidas do frontend."""

    model_config = ConfigDict(extra="forbid", strict=True)

    type: Literal["message"]
    content: str
    date_filter: Literal["24h", "7d", "1m"] | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("content nao pode ser vazio")
        return normalized


class RecoverableProtocolError(ValueError):
    """Payload rejeitado sem necessidade de encerrar a conexao."""


class MessageTooLargeError(ValueError):
    """Violacao grave: conteudo excede o limite operacional."""


def _parse_incoming_message(raw: str) -> IncomingChatMessage:
    data = json.loads(raw)

    if (
        isinstance(data, dict)
        and isinstance(data.get("content"), str)
        and len(data["content"]) > config.WS_MAX_MESSAGE_CHARS
    ):
        raise MessageTooLargeError

    try:
        return IncomingChatMessage.model_validate(data)
    except ValidationError as exc:
        raise RecoverableProtocolError(
            "Mensagem invalida. Envie type='message', content textual nao vazio "
            "e date_filter opcional (24h, 7d ou 1m)."
        ) from exc


def _initial_session() -> dict[str, Any]:
    return {
        "mode": "init",
        "quiz_step": 0,
        "quiz_answers": {},
        "coach_step": 0,
        "interview_context": "",
        "active_agent": "Maestro",
    }


def _session_payload(session: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "mode": session.get("mode", "init"),
        "quiz_step": int(session.get("quiz_step") or 0),
        "quiz_answers": session.get("quiz_answers") or {},
        "coach_step": int(session.get("coach_step") or 0),
        "interview_context": session.get("interview_context") or "",
    }

    active_agent = session.get("active_agent")
    if active_agent:
        payload["active_agent"] = active_agent

    return payload


def _apply_state_update(session: dict[str, Any], update: dict[str, Any]) -> None:
    mode = update.get("mode", session.get("mode", "init"))
    session.update(update)

    if mode in {"init", "quiz", "quiz_resume", "menu", "await_job_description"}:
        session["active_agent"] = "Maestro"
    elif mode == "scout":
        session["active_agent"] = "Scout"
    elif mode == "curator":
        session["active_agent"] = "Curator"
    elif mode == "coach":
        session["active_agent"] = "Coach"
    elif mode == "agent_running":
        session["active_agent"] = update.get(
            "active_agent",
            session.get("active_agent", "Maestro"),
        )

    if mode != "coach":
        session["coach_step"] = 0

    if mode in {"init", "quiz", "quiz_resume"}:
        session["interview_context"] = ""

    if mode not in {"quiz", "quiz_resume"}:
        session["quiz_step"] = 0
        if mode == "init":
            session["quiz_answers"] = {}


def _parse_state_token(token: str) -> dict[str, Any] | None:
    if not token.startswith("__STATE__:"):
        return None

    parts = token[len("__STATE__:") :].split(":", 2)
    mode = parts[0]
    state: dict[str, Any] = {"mode": mode}

    if mode == "quiz" and len(parts) >= 2:
        try:
            state["quiz_step"] = int(parts[1])
        except ValueError:
            state["quiz_step"] = 0
        if len(parts) == 3:
            try:
                decoded = base64.b64decode(parts[2]).decode()
                state["quiz_answers"] = json.loads(decoded)
            except (binascii.Error, json.JSONDecodeError, UnicodeDecodeError):
                state["quiz_answers"] = {}

    elif mode == "coach" and len(parts) >= 2:
        try:
            state["coach_step"] = int(parts[1])
        except ValueError:
            state["coach_step"] = 0
        if len(parts) == 3:
            state["interview_context"] = parts[2]

    elif mode == "agent_running" and len(parts) >= 2:
        agent_key = parts[1].strip().lower()
        state["active_agent"] = {
            "scout": "Scout",
            "curator": "Curator",
            "coach": "Coach",
            "maestro": "Maestro",
        }.get(agent_key, "Maestro")

    return state


def _state_log_payload(session: dict[str, Any], session_id: str) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "mode": session.get("mode", "init"),
        "active_agent": session.get("active_agent", "Maestro"),
        "quiz_step": int(session.get("quiz_step") or 0),
        "coach_step": int(session.get("coach_step") or 0),
    }


def _normalize_session_state(raw_state: dict[str, Any]) -> dict[str, Any]:
    session = _initial_session()

    mode = raw_state.get("mode")
    if isinstance(mode, str) and mode:
        session["mode"] = mode

    active_agent = raw_state.get("active_agent")
    if isinstance(active_agent, str) and active_agent:
        session["active_agent"] = active_agent

    quiz_answers = raw_state.get("quiz_answers")
    if isinstance(quiz_answers, dict):
        session["quiz_answers"] = quiz_answers

    interview_context = raw_state.get("interview_context")
    if isinstance(interview_context, str):
        session["interview_context"] = interview_context

    for key in ("quiz_step", "coach_step"):
        try:
            session[key] = int(raw_state.get(key) or 0)
        except (TypeError, ValueError):
            session[key] = 0

    return session


async def _load_session_state(paths: SessionPaths) -> tuple[dict[str, Any], bool]:
    try:
        content = await read_text_async(paths.CHAT_STATE_FILE)
        if not content.strip():
            return _initial_session(), False

        payload = json.loads(content)
        if not isinstance(payload, dict):
            logger.warning(
                "Estado persistido do WebSocket tem formato invalido",
                extra={
                    "event": "websocket_state_invalid_payload",
                    "session_id": paths.session_id,
                    "path": str(paths.CHAT_STATE_FILE),
                    "payload_type": type(payload).__name__,
                },
            )
            return _initial_session(), False

        session = _normalize_session_state(payload)
        logger.info(
            "Estado persistido do WebSocket restaurado",
            extra={
                "event": "websocket_state_restored",
                **_state_log_payload(session, paths.session_id),
                "path": str(paths.CHAT_STATE_FILE),
            },
        )
        return session, True
    except json.JSONDecodeError as exc:
        logger.exception(
            "JSON invalido ao restaurar estado do WebSocket",
            extra={
                "event": "websocket_state_restore_json_error",
                "session_id": paths.session_id,
                "path": str(paths.CHAT_STATE_FILE),
                "error_type": type(exc).__name__,
            },
        )
        return _initial_session(), False
    except OSError:
        logger.exception(
            "Falha de I/O ao restaurar estado do WebSocket",
            extra={
                "event": "websocket_state_restore_io_error",
                "session_id": paths.session_id,
                "path": str(paths.CHAT_STATE_FILE),
            },
        )
        return _initial_session(), False


async def _persist_session_state(
    session: dict[str, Any],
    paths: SessionPaths,
    reason: str,
) -> None:
    payload = _session_payload(session)
    try:
        async with get_session_lock(paths.session_id):
            await write_text_atomic_async(
                paths.CHAT_STATE_FILE,
                json.dumps(payload, ensure_ascii=False, indent=2),
            )
        logger.info(
            "Estado do WebSocket persistido",
            extra={
                "event": "websocket_state_persisted",
                **_state_log_payload(session, paths.session_id),
                "path": str(paths.CHAT_STATE_FILE),
                "reason": reason,
            },
        )
    except OSError:
        logger.exception(
            "Falha de I/O ao persistir estado do WebSocket",
            extra={
                "event": "websocket_state_persist_io_error",
                **_state_log_payload(session, paths.session_id),
                "path": str(paths.CHAT_STATE_FILE),
                "reason": reason,
            },
        )


def _public_error_message(exc: LLMProviderError | OSError | RuntimeError | ValueError) -> str:
    if isinstance(exc, LLMProviderError):
        return exc.public_message
    return "Erro no processamento da mensagem. Tente novamente."


async def _release_session_resources(session: dict[str, Any], paths: SessionPaths) -> None:
    await _persist_session_state(session, paths, "release")
    logger.info(
        "Recursos em memoria da sessao liberados",
        extra={
            "event": "websocket_session_released",
            **_state_log_payload(session, paths.session_id),
        },
    )
    session.clear()


async def _send_error_response(
    websocket: WebSocket,
    message: str,
    session: dict[str, Any],
    session_id: str,
) -> None:
    try:
        await websocket.send_json({"type": "error", "content": message})
    except WebSocketDisconnect:
        logger.info(
            "WebSocket desconectado antes do envio de erro",
            extra={
                "event": "websocket_disconnected_during_error_send",
                **_state_log_payload(session, session_id),
            },
        )
    except (OSError, RuntimeError) as exc:
        logger.warning(
            "Falha ao enviar erro pelo WebSocket",
            extra={
                "event": "websocket_error_send_failed",
                **_state_log_payload(session, session_id),
                "error_type": type(exc).__name__,
            },
        )


async def _send_stream_token(
    websocket: WebSocket,
    token: str,
    session: dict[str, Any],
    paths: SessionPaths,
) -> None:
    """Envia texto e estado sem descartar pedacos da resposta."""
    session_id = paths.session_id
    if "__STATE__:" not in token:
        await websocket.send_json({"type": "token", "content": token})
        logger.debug(
            "Token enviado ao WebSocket",
            extra={
                "event": "websocket_token_sent",
                "session_id": session_id,
                "content_length": len(token),
            },
        )
        return

    text_part, state_and_tail = token.split("__STATE__:", 1)
    state_line, separator, tail = state_and_tail.partition("\n")

    if text_part:
        await websocket.send_json({"type": "token", "content": text_part})
        logger.debug(
            "Token textual enviado antes de atualizacao de estado",
            extra={
                "event": "websocket_token_sent",
                "session_id": session_id,
                "content_length": len(text_part),
            },
        )

    state_update = _parse_state_token("__STATE__:" + state_line)
    if state_update:
        _apply_state_update(session, state_update)
        await websocket.send_json({"type": "state", "content": _session_payload(session)})
        await _persist_session_state(session, paths, "state_update")
        logger.info(
            "Estado da sessao atualizado via stream",
            extra={
                "event": "websocket_state_updated",
                **_state_log_payload(session, session_id),
            },
        )

    if separator and tail:
        await websocket.send_json({"type": "token", "content": tail})
        logger.debug(
            "Token textual enviado apos atualizacao de estado",
            extra={
                "event": "websocket_token_sent",
                "session_id": session_id,
                "content_length": len(tail),
            },
        )


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """Endpoint WebSocket principal."""
    await websocket.accept()

    paths = SessionPaths(websocket.query_params.get("session_id"))
    session_id = paths.session_id
    logger.info(
        "WebSocket aceito",
        extra={
            "event": "websocket_connected",
            "session_id": session_id,
            "client": str(websocket.client) if websocket.client else None,
        },
    )

    session, restored = await _load_session_state(paths)
    await websocket.send_json({"type": "state", "content": _session_payload(session)})
    logger.info(
        "Estado inicial enviado",
        extra={
            "event": "websocket_initial_state_sent",
            **_state_log_payload(session, session_id),
            "restored": restored,
        },
    )

    maestro = MaestroAgent(paths)
    wants_replay = websocket.query_params.get("replay") == "1"

    try:
        should_skip_welcome = restored and session.get("mode") != "init"
        if should_skip_welcome and wants_replay:
            # Primeiro load do cliente (reload): repinta o prompt atual da sessão
            # restaurada (pergunta do quiz, menu, entrevista) sem replayar o
            # welcome inteiro e sem alterar estado. Em reconexões transitórias
            # (sem replay=1) nada é re-emitido — não expõe a reconexão ao usuário
            # nem duplica o prompt.
            logger.info(
                "Replay do prompt atual no primeiro load",
                extra={
                    "event": "websocket_replay_prompt",
                    **_state_log_payload(session, session_id),
                },
            )
            async for token in maestro.replay_current_prompt(dict(session)):
                await websocket.send_json({"type": "token", "content": token})
            await websocket.send_json({"type": "done", "content": ""})
        elif should_skip_welcome:
            logger.info(
                "Stream inicial ignorado porque estado persistido foi restaurado",
                extra={
                    "event": "websocket_welcome_stream_skipped",
                    **_state_log_payload(session, session_id),
                },
            )
        else:
            logger.info(
                "Stream de boas-vindas iniciado",
                extra={
                    "event": "websocket_welcome_stream_start",
                    **_state_log_payload(session, session_id),
                },
            )
            context = {**session, "message": ""}
            async for token in maestro.run(context):
                await _send_stream_token(websocket, token, session, paths)

            await websocket.send_json({"type": "done", "content": ""})
            logger.info(
                "Stream de boas-vindas concluido",
                extra={
                    "event": "websocket_welcome_stream_finish",
                    **_state_log_payload(session, session_id),
                },
            )
    except WebSocketDisconnect:
        logger.info(
            "WebSocket desconectado durante boas-vindas",
            extra={
                "event": "websocket_disconnected",
                **_state_log_payload(session, session_id),
            },
        )
        await _release_session_resources(session, paths)
        return
    except (LLMProviderError, OSError, RuntimeError, ValueError) as exc:
        logger.exception(
            "Erro no stream inicial do WebSocket",
            extra={
                "event": "websocket_welcome_stream_error",
                **_state_log_payload(session, session_id),
                "error_type": type(exc).__name__,
            },
        )
        await _send_error_response(
            websocket,
            _public_error_message(exc),
            session,
            session_id,
        )

    close_without_persisting = False
    while True:
        try:
            raw = await websocket.receive_text()
            message = _parse_incoming_message(raw)
            logger.info(
                "Mensagem recebida do WebSocket",
                extra={
                    "event": "websocket_message_received",
                    **_state_log_payload(session, session_id),
                    "message_type": message.type,
                    "raw_length": len(raw),
                    "content_length": len(message.content),
                },
            )

            context = {
                **session,
                "message": message.content,
                "date_filter": message.date_filter or "",
            }

            logger.info(
                "Execucao do Maestro iniciada para mensagem",
                extra={
                    "event": "websocket_agent_run_start",
                    **_state_log_payload(session, session_id),
                    "message_length": len(message.content),
                    "date_filter": message.date_filter or "",
                },
            )
            async for token in maestro.run(context):
                await _send_stream_token(websocket, token, session, paths)

            await websocket.send_json({"type": "done", "content": ""})
            await _persist_session_state(session, paths, "message_processed")
            logger.info(
                "Execucao do Maestro concluida para mensagem",
                extra={
                    "event": "websocket_agent_run_finish",
                    **_state_log_payload(session, session_id),
                },
            )

        except WebSocketDisconnect:
            logger.info(
                "WebSocket desconectado",
                extra={
                    "event": "websocket_disconnected",
                    **_state_log_payload(session, session_id),
                },
            )
            break
        except json.JSONDecodeError:
            logger.warning(
                "Mensagem WebSocket com JSON invalido",
                extra={
                    "event": "websocket_invalid_json",
                    **_state_log_payload(session, session_id),
                },
            )
            await _send_error_response(
                websocket,
                "Mensagem invalida",
                session,
                session_id,
            )
        except RecoverableProtocolError as exc:
            logger.warning(
                "Mensagem WebSocket fora do contrato",
                extra={
                    "event": "websocket_invalid_payload",
                    **_state_log_payload(session, session_id),
                },
            )
            await _send_error_response(websocket, str(exc), session, session_id)
        except MessageTooLargeError:
            logger.warning(
                "Mensagem WebSocket acima do limite",
                extra={
                    "event": "websocket_message_too_large",
                    **_state_log_payload(session, session_id),
                    "max_message_chars": config.WS_MAX_MESSAGE_CHARS,
                },
            )
            await websocket.close(
                code=1009,
                reason=(
                    "Mensagem excede o limite de "
                    f"{config.WS_MAX_MESSAGE_CHARS} caracteres."
                ),
            )
            close_without_persisting = True
            break
        except (LLMProviderError, OSError, RuntimeError, ValueError) as exc:
            logger.exception(
                "Erro durante processamento de mensagem WebSocket",
                extra={
                    "event": "websocket_message_error",
                    **_state_log_payload(session, session_id),
                    "error_type": type(exc).__name__,
                },
            )
            await _send_error_response(
                websocket,
                _public_error_message(exc),
                session,
                session_id,
            )
            try:
                await websocket.send_json({"type": "done", "content": ""})
            except (WebSocketDisconnect, OSError, RuntimeError):
                logger.info(
                    "WebSocket desconectado antes do envio de done",
                    extra={
                        "event": "websocket_disconnected_during_done_send",
                        **_state_log_payload(session, session_id),
                    },
                )
                break

    if close_without_persisting:
        logger.info(
            "Sessao descartada sem persistencia apos violacao de protocolo",
            extra={
                "event": "websocket_protocol_violation_released",
                **_state_log_payload(session, session_id),
            },
        )
        session.clear()
    else:
        await _release_session_resources(session, paths)
