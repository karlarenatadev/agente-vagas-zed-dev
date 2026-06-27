"""Utilitários compartilhados pelos routers de análise (match, tailoring, pdi)."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException

from agents.reconciliation import normalize_focus, parse_focus
from logging_config import get_logger

logger = get_logger(__name__)


def read_required(path: Path, missing_message: str, invalid_message: str) -> str:
    """Lê um artefato obrigatório de data/.

    Retorna o conteúdo já sem espaços nas pontas. Levanta HTTP 400 com
    `missing_message` se o arquivo não existir e com `invalid_message` se
    estiver vazio. Arquivo corrompido/não-UTF-8 vira 409 controlado; falha de
    I/O genérica vira 500 (logado), em vez de erro não tratado.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail=missing_message)
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=409,
            detail=(
                f"{invalid_message} O arquivo parece corrompido ou nao e um "
                "Markdown de texto valido. Gere o artefato novamente."
            ),
        )
    except OSError:
        logger.exception(
            "Falha ao ler artefato obrigatorio",
            extra={"event": "artifact_read_error", "path": str(path)},
        )
        raise HTTPException(status_code=500, detail="Falha ao ler o artefato. Tente novamente.")

    content = raw.strip()
    if not content:
        raise HTTPException(status_code=400, detail=invalid_message)
    return content


def read_optional_text(path: Path) -> str | None:
    """Le um artefato opcional. Ausente -> None; corrompido/ilegivel -> 409 controlado."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=409,
            detail="Artefato corrompido ou ilegivel. Gere o artefato novamente.",
        )
    except OSError:
        logger.exception(
            "Falha ao ler artefato opcional",
            extra={"event": "artifact_read_error", "path": str(path)},
        )
        raise HTTPException(status_code=500, detail="Falha ao ler o artefato. Tente novamente.")


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
