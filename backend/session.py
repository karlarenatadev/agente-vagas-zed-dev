"""Isolamento de dados por sessão.

Cada sessão (um navegador, identificado por um ID anônimo) tem sua própria
pasta sob ``data/sessions/{session_id}/``. Assim dois usuários simultâneos não
sobrescrevem perfil, currículo, vaga, match, PDI etc. uns dos outros.

`SessionPaths` espelha os nomes de atributo de `config` (PROFILE_FILE,
RESUME_ANALYSIS_FILE, ...), então migrar o código é quase mecânico:
trocar `config.PROFILE_FILE` por `paths.PROFILE_FILE`.

Sem um ID válido, cai numa sessão default que usa a própria pasta `data/`
(comportamento legado), preservando compatibilidade com chamadas sem header.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import Header

import config

# Só permitimos estes caracteres no ID; o resto é removido. Isso neutraliza
# path traversal (".." perde os pontos, "/" e "\" são removidos) antes de o ID
# virar nome de pasta.
_SAFE_RE = re.compile(r"[^a-zA-Z0-9_-]")
_MAX_LEN = 64

# ID reservado para a sessão default (sem isolamento, usa data/ direto).
DEFAULT_SESSION = "_default"


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


class SessionPaths:
    """Resolve os caminhos dos artefatos de uma sessão."""

    def __init__(self, session_id: str | None = None, base_dir: Path | None = None):
        base = Path(base_dir) if base_dir is not None else config.DATA_DIR
        self.session_id = sanitize_session_id(session_id)
        # A sessão default escreve direto em data/ (legado); sessões reais
        # ficam isoladas em data/sessions/{id}/.
        if self.session_id == DEFAULT_SESSION:
            self.dir = base
        else:
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
    def APPLICATIONS_FILE(self) -> Path:
        return self.dir / "applications.json"

    def __repr__(self) -> str:  # pragma: no cover - debug
        return f"SessionPaths(session_id={self.session_id!r}, dir={self.dir})"


def get_session_paths(x_session_id: str | None = Header(default=None)) -> SessionPaths:
    """Dependency FastAPI: monta o SessionPaths a partir do header X-Session-Id.

    Use com `Depends(get_session_paths)` nas rotas. Sem o header, cai na sessão
    default (pasta data/), preservando o comportamento anterior.
    """
    return SessionPaths(x_session_id)
