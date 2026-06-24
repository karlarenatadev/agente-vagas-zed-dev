"""Utilitários compartilhados pelos routers de análise (match, tailoring, pdi)."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from agents.reconciliation import normalize_focus, parse_focus


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


def resolve_focus(profile_content: str | None, explicit: str | None = None) -> str:
    """Resolve o foco da candidatura por precedência: explícito > perfil > "vaga".

    ``explicit`` vem do corpo da requisição; ``profile_content`` é o
    ``user-profile.md`` (que pode conter a linha "Foco da candidatura:").
    Valores inválidos são ignorados, caindo no próximo nível. Espelha a mesma
    precedência usada pela reconciliação.
    """
    if explicit:
        normalized = normalize_focus(explicit)
        if normalized:
            return normalized
    if profile_content:
        parsed = parse_focus(profile_content)
        if parsed:
            return parsed
    return "vaga"
