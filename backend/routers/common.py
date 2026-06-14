"""Utilitários compartilhados pelos routers de análise (match, tailoring, pdi)."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException


def read_required(path: Path, missing_message: str, invalid_message: str) -> str:
    """Lê um artefato obrigatório de data/.

    Retorna o conteúdo já sem espaços nas pontas. Levanta HTTP 400 com
    `missing_message` se o arquivo não existir e com `invalid_message` se
    estiver vazio.
    """
    try:
        content = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=missing_message)

    if not content:
        raise HTTPException(status_code=400, detail=invalid_message)
    return content
