"""Classe base para todos os agentes do sistema."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, AsyncGenerator

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    AsyncOpenAI,
    RateLimitError,
)

import config
from logging_config import get_logger
from session import SessionPaths, write_text_atomic


logger = get_logger(__name__)


class LLMProviderError(RuntimeError):
    """Erro controlado para falhas de infraestrutura do provedor LLM."""

    public_message = "Servico de IA temporariamente indisponivel. Tente novamente em instantes."

    def __init__(self, message: str, *, provider_error: str) -> None:
        super().__init__(message)
        self.provider_error = provider_error


class BaseAgent(ABC):
    """Interface base para Scout, Curator e Coach."""

    name: str = "BaseAgent"

    def __init__(self, paths: SessionPaths | None = None):
        # base_url vazio => None preserva o padrao do SDK (api.openai.com).
        # Com LLM_BASE_URL definido (ex.: OpenRouter), o cliente passa a usar o
        # provedor compativel correto, evitando 401 e o consequente fallback.
        self.client = AsyncOpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.LLM_BASE_URL or None,
        )
        self.model = config.LLM_MODEL
        self.paths = paths or SessionPaths()
        logger.debug(
            "Agente inicializado",
            extra={
                "event": "agent_initialized",
                "agent": self.name,
                "session_id": self.paths.session_id,
                "model": self.model,
            },
        )

    def _read_file(self, path: Path) -> str:
        """Le um arquivo e retorna string vazia quando ele ainda nao existe."""
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.debug(
                "Arquivo de contexto ausente",
                extra={
                    "event": "agent_file_missing",
                    "agent": self.name,
                    "session_id": self.paths.session_id,
                    "path": str(path),
                },
            )
            return ""
        except OSError:
            logger.exception(
                "Falha ao ler arquivo de contexto",
                extra={
                    "event": "agent_file_read_error",
                    "agent": self.name,
                    "session_id": self.paths.session_id,
                    "path": str(path),
                },
            )
            raise

    def _write_file(self, path: Path, content: str) -> None:
        """Escreve conteudo em um arquivo, criando diretorios se necessario."""
        try:
            write_text_atomic(path, content)
            logger.debug(
                "Arquivo de contexto gravado",
                extra={
                    "event": "agent_file_written",
                    "agent": self.name,
                    "session_id": self.paths.session_id,
                    "path": str(path),
                    "content_length": len(content),
                },
            )
        except OSError:
            logger.exception(
                "Falha ao gravar arquivo de contexto",
                extra={
                    "event": "agent_file_write_error",
                    "agent": self.name,
                    "session_id": self.paths.session_id,
                    "path": str(path),
                    "content_length": len(content),
                },
            )
            raise

    async def stream_llm(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncGenerator[str, None]:
        """Faz chamada ao LLM com streaming e emite tokens conforme chegam."""
        started_at = time.perf_counter()
        token_count = 0
        logger.info(
            "Chamada LLM streaming iniciada",
            extra={
                "event": "llm_stream_start",
                "agent": self.name,
                "session_id": self.paths.session_id,
                "model": self.model,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
            },
        )

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
                temperature=0.7,
            )
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    token_count += 1
                    yield delta
        # APIError e a classe-base do SDK: cobre conexao, status (401/429/5xx)
        # e erros genericos repassados pelo provedor (ex.: upstream do OpenRouter
        # no meio do stream). Garante que toda falha vire LLMProviderError
        # controlado em vez de vazar como excecao crua.
        except (APIError, TimeoutError) as exc:
            logger.exception(
                "Chamada LLM streaming falhou",
                extra={
                    "event": "llm_stream_error",
                    "agent": self.name,
                    "session_id": self.paths.session_id,
                    "model": self.model,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                    "token_count": token_count,
                    "error_type": type(exc).__name__,
                },
            )
            raise LLMProviderError(
                self._llm_public_message(exc),
                provider_error=type(exc).__name__,
            ) from exc
        else:
            logger.info(
                "Chamada LLM streaming concluida",
                extra={
                    "event": "llm_stream_finish",
                    "agent": self.name,
                    "session_id": self.paths.session_id,
                    "model": self.model,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                    "token_count": token_count,
                },
            )

    async def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Faz chamada ao LLM sem streaming. Retorna resposta completa."""
        started_at = time.perf_counter()
        logger.info(
            "Chamada LLM iniciada",
            extra={
                "event": "llm_call_start",
                "agent": self.name,
                "session_id": self.paths.session_id,
                "model": self.model,
                "system_prompt_length": len(system_prompt),
                "user_prompt_length": len(user_prompt),
            },
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
        # APIError e a classe-base do SDK: cobre conexao, status (401/429/5xx)
        # e erros genericos repassados pelo provedor (ex.: upstream do OpenRouter
        # no meio do stream). Garante que toda falha vire LLMProviderError
        # controlado em vez de vazar como excecao crua.
        except (APIError, TimeoutError) as exc:
            logger.exception(
                "Chamada LLM falhou",
                extra={
                    "event": "llm_call_error",
                    "agent": self.name,
                    "session_id": self.paths.session_id,
                    "model": self.model,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                    "error_type": type(exc).__name__,
                },
            )
            raise LLMProviderError(
                self._llm_public_message(exc),
                provider_error=type(exc).__name__,
            ) from exc

        content = response.choices[0].message.content or "" if response.choices else ""
        logger.info(
            "Chamada LLM concluida",
            extra={
                "event": "llm_call_finish",
                "agent": self.name,
                "session_id": self.paths.session_id,
                "model": self.model,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "response_length": len(content),
                "choice_count": len(response.choices),
            },
        )
        return content

    def _llm_public_message(
        self,
        exc: APIError | TimeoutError,
    ) -> str:
        if isinstance(exc, RateLimitError):
            return "Limite temporario do servico de IA atingido. Tente novamente em instantes."
        if isinstance(exc, (APIConnectionError, TimeoutError)):
            return "Nao consegui conectar ao servico de IA agora. Tente novamente em instantes."
        if isinstance(exc, APIStatusError):
            return "O servico de IA retornou uma falha temporaria. Tente novamente em instantes."
        return LLMProviderError.public_message

    @abstractmethod
    async def run(self, context: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Executa o agente com o contexto fornecido."""
        ...
