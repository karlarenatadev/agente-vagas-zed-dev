"""
Classe base para todos os agentes do sistema.
Define a interface comum e utilitários compartilhados.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import AsyncGenerator

from openai import AsyncOpenAI

import config


class BaseAgent(ABC):
    """Interface base para Scout, Curator e Coach."""

    name: str = "BaseAgent"

    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.LLM_MODEL

    def _read_file(self, path) -> str:
        """Lê um arquivo e retorna seu conteúdo. Retorna string vazia se não existir."""
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def _write_file(self, path, content: str) -> None:
        """Escreve conteúdo em um arquivo, criando diretórios se necessário."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    async def stream_llm(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncGenerator[str, None]:
        """
        Faz chamada ao LLM com streaming.
        Yields tokens de texto conforme chegam.
        """
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
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Faz chamada ao LLM sem streaming. Retorna resposta completa."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content or ""

    @abstractmethod
    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        """
        Executa o agente com o contexto fornecido.
        Yields tokens de texto para streaming ao frontend.
        """
        ...
