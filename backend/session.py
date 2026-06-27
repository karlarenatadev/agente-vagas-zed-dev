"""Isolamento de dados por sessão.

Cada sessão (um navegador, identificado por um ID anônimo) tem sua própria
pasta sob ``data/sessions/{session_id}/``. Assim dois usuários simultâneos não
sobrescrevem perfil, currículo, vaga, match, PDI etc. uns dos outros.

`SessionPaths` espelha os nomes de atributo de `config` (PROFILE_FILE,
RESUME_ANALYSIS_FILE, ...), então migrar o código é quase mecânico:
trocar `config.PROFILE_FILE` por `paths.PROFILE_FILE`.

Sem um ID válido (chamada sem header ``X-Session-Id``), cai numa sessão default
isolada em ``data/sessions/_default/`` — não na raiz de ``data/``. Os arquivos
Markdown soltos em ``data/*.md`` são considerados LEGADO e NÃO são consumidos:
para reaproveitá-los é preciso regerá-los dentro da sessão (ou movê-los
manualmente para ``data/sessions/_default/``). Nenhum arquivo legado é apagado.
"""

from __future__ import annotations

import asyncio
import os
import re
import time
import uuid
from pathlib import Path

from fastapi import Header

import config
from logging_config import get_logger


logger = get_logger(__name__)

# Só permitimos estes caracteres no ID; o resto é removido. Isso neutraliza
# path traversal (".." perde os pontos, "/" e "\" são removidos) antes de o ID
# virar nome de pasta.
_SAFE_RE = re.compile(r"[^a-zA-Z0-9_-]")
_MAX_LEN = 64

# ID reservado para a sessão default (sem header X-Session-Id). Mesmo a default
# fica isolada em data/sessions/_default/ — a raiz de data/ não é mais usada
# como diretório de sessão.
DEFAULT_SESSION = "_default"
_session_locks: dict[str, asyncio.Lock] = {}
_ATOMIC_REPLACE_ATTEMPTS = 10
_ATOMIC_REPLACE_RETRY_SECONDS = 0.02
_ATOMIC_REPLACE_MAX_BACKOFF_SECONDS = 0.5


def sanitize_session_id(raw: str | None) -> str:
    """Reduz um ID cru a um nome de pasta seguro.

    Remove qualquer caractere fora de [A-Za-z0-9_-], limita o tamanho e cai no
    ID default quando o resultado fica vazio (incluindo tentativas de traversal
    como ".." ou "../etc").
    """
    if not raw:
        return DEFAULT_SESSION
    cleaned = _SAFE_RE.sub("", raw)[:_MAX_LEN]
    return cleaned or DEFAULT_SESSION


def get_session_lock(session_id: str | None) -> asyncio.Lock:
    """Retorna uma trava assincrona compartilhada por sessao."""
    safe_session_id = sanitize_session_id(session_id)
    lock = _session_locks.get(safe_session_id)
    if lock is None:
        lock = asyncio.Lock()
        _session_locks[safe_session_id] = lock
    return lock


def _temp_path_for(path: Path) -> Path:
    suffix = f"{path.suffix}.tmp-{uuid.uuid4().hex}"
    return path.with_suffix(suffix)


def _atomic_write_text_sync(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = _temp_path_for(path)
    try:
        with tmp_path.open("w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
            try:
                os.replace(tmp_path, path)
                break
            except PermissionError:
                # Lock transitório (ex.: antivírus/indexador/sync segurando o
                # destino no Windows). Backoff exponencial com teto amplia a
                # janela de retry sem mudar a semântica de escrita atômica.
                if attempt == _ATOMIC_REPLACE_ATTEMPTS - 1:
                    raise
                backoff = min(
                    _ATOMIC_REPLACE_RETRY_SECONDS * (2 ** attempt),
                    _ATOMIC_REPLACE_MAX_BACKOFF_SECONDS,
                )
                time.sleep(backoff)
    except OSError:
        logger.exception(
            "Falha na escrita atomica de arquivo",
            extra={
                "event": "atomic_file_write_error",
                "path": str(path),
                "tmp_path": str(tmp_path),
                "content_length": len(content),
            },
        )
        raise
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            logger.warning(
                "Falha ao remover arquivo temporario de escrita atomica",
                extra={
                    "event": "atomic_file_tmp_cleanup_error",
                    "path": str(path),
                    "tmp_path": str(tmp_path),
                },
            )


def write_text_atomic(path: Path, content: str) -> None:
    """Escreve texto com troca atomica. Mantem compatibilidade com codigo sync."""
    _atomic_write_text_sync(path, content)
    logger.debug(
        "Arquivo gravado de forma atomica",
        extra={
            "event": "atomic_file_written",
            "path": str(path),
            "content_length": len(content),
        },
    )


async def write_text_atomic_async(path: Path, content: str) -> None:
    """Escreve texto sem bloquear o event loop e troca o arquivo atomicamente."""
    await asyncio.to_thread(_atomic_write_text_sync, path, content)
    logger.debug(
        "Arquivo gravado de forma atomica",
        extra={
            "event": "atomic_file_written",
            "path": str(path),
            "content_length": len(content),
        },
    )


async def read_text_async(path: Path, default: str = "") -> str:
    """Le texto fora do event loop; retorna default para arquivo ausente."""
    try:
        return await asyncio.to_thread(path.read_text, encoding="utf-8")
    except FileNotFoundError:
        return default
    except OSError:
        logger.exception(
            "Falha na leitura de arquivo",
            extra={
                "event": "file_read_error",
                "path": str(path),
            },
        )
        raise


class SessionPaths:
    """Resolve os caminhos dos artefatos de uma sessão."""

    def __init__(self, session_id: str | None = None, base_dir: Path | None = None):
        base = Path(base_dir) if base_dir is not None else config.DATA_DIR
        self.session_id = sanitize_session_id(session_id)
        # TODAS as sessões ficam isoladas sob data/sessions/{id}/ — inclusive a
        # default (data/sessions/_default/). A raiz de data/ guarda apenas
        # legado/README e NÃO é consumida como diretório de sessão.
        self.dir = base / "sessions" / self.session_id

    # ── Artefatos (espelham config.*) ──────────────────────────────────────
    @property
    def QUIZ_FILE(self) -> Path:
        return self.dir / "personality-quiz.md"

    @property
    def PROFILE_FILE(self) -> Path:
        return self.dir / "user-profile.md"

    @property
    def JOB_RESULTS_FILE(self) -> Path:
        return self.dir / "job-search-results.md"

    @property
    def COURSE_RECS_FILE(self) -> Path:
        return self.dir / "course-recommendations.md"

    @property
    def INTERVIEW_FILE(self) -> Path:
        return self.dir / "interview-session.md"

    @property
    def RESUME_ANALYSIS_FILE(self) -> Path:
        return self.dir / "resume-analysis.md"

    @property
    def JOB_DESCRIPTION_ANALYSIS_FILE(self) -> Path:
        return self.dir / "job-description-analysis.md"

    @property
    def RESUME_MATCH_REPORT_FILE(self) -> Path:
        return self.dir / "resume-match-report.md"

    @property
    def RESUME_TAILORING_SUGGESTIONS_FILE(self) -> Path:
        return self.dir / "resume-tailoring-suggestions.md"

    @property
    def PDI_PLAN_FILE(self) -> Path:
        return self.dir / "pdi-plan.md"

    @property
    def RECONCILIATION_FILE(self) -> Path:
        return self.dir / "reconciliation.md"

    @property
    def APPLICATIONS_FILE(self) -> Path:
        return self.dir / "applications.json"

    @property
    def CHAT_STATE_FILE(self) -> Path:
        return self.dir / "chat_state.json"

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"SessionPaths(session_id={self.session_id!r}, dir={self.dir})"


def get_session_paths(x_session_id: str | None = Header(default=None)) -> SessionPaths:
    """Dependency FastAPI: monta o SessionPaths a partir do header X-Session-Id.

    Use com `Depends(get_session_paths)` nas rotas. Sem o header, cai na sessão
    default isolada em `data/sessions/_default/` (a raiz de `data/` não é usada).
    """
    return SessionPaths(x_session_id)
