"""Valida arquivos rastreados/staged contra vazamento de dados e segredos.

Uso local:
    python scripts/validate_data_guard.py

O script usa somente a biblioteca padrao. Ele verifica os caminhos presentes no
indice Git e, quando diferente, tambem o conteudo atual do arquivo rastreado.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


ALLOWED_DATA_FILE = PurePosixPath("data/README.md")
ALLOWED_DATA_EXAMPLE_SUFFIX = ".example.md"
ALLOWED_ENV_EXAMPLE = ".env.example"


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    reason: str


SPECIFIC_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "chave privada detectada",
        re.compile(
            r"-----BEGIN\s+(?:RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE\s+KEY-----",
            re.IGNORECASE,
        ),
    ),
    (
        "access key AWS detectada",
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ),
    (
        "token OpenAI detectado",
        re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    ),
    (
        "token Firecrawl detectado",
        re.compile(r"\bfc-[A-Za-z0-9_-]{20,}\b"),
    ),
    (
        "token GitHub detectado",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"
        ),
    ),
    (
        "bearer token detectado",
        re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}={0,2}\b", re.IGNORECASE),
    ),
    (
        "JWT detectado",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{10,}\."
            r"eyJ[A-Za-z0-9_-]{10,}\."
            r"[A-Za-z0-9_-]{10,}\b"
        ),
    ),
)

GENERIC_CREDENTIAL_ASSIGNMENT = re.compile(
    r"""
    (?:
        api[_-]?key
        | access[_-]?key
        | secret(?:[_-]?key)?
        | client[_-]?secret
        | auth[_-]?token
        | access[_-]?token
        | bearer[_-]?token
        | password
        | passwd
    )
    \b
    [ \t]*[:=][ \t]*
    ["']?
    (?P<value>[^\s"'`;,\#\}\{]+)
    """,
    re.IGNORECASE | re.VERBOSE,
)

PLACEHOLDER_MARKERS = (
    "example",
    "sample",
    "placeholder",
    "replace-with",
    "changeme",
    "change-me",
    "redacted",
    "dummy",
    "fake",
    "test-",
    "your-",
    "your_",
    "informe-",
)

REFERENCE_PREFIXES = (
    "$",
    "<",
    "[",
    "os.",
    "env.",
    "config.",
    "settings.",
    "process.env",
    "self.",
)


class GuardExecutionError(RuntimeError):
    """Falha operacional ao consultar o repositorio."""


def _run_git(repo_root: Path, *args: str) -> bytes:
    process = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        error = process.stderr.decode("utf-8", errors="replace").strip()
        raise GuardExecutionError(error or f"git {' '.join(args)} falhou")
    return process.stdout


def find_repo_root(explicit_root: str | None) -> Path:
    if explicit_root:
        root = Path(explicit_root).resolve()
        _run_git(root, "rev-parse", "--show-toplevel")
        return root

    process = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        error = process.stderr.decode("utf-8", errors="replace").strip()
        raise GuardExecutionError(error or "nao foi possivel localizar o repositorio Git")
    return Path(process.stdout.decode("utf-8").strip()).resolve()


def tracked_paths(repo_root: Path) -> list[str]:
    raw = _run_git(repo_root, "ls-files", "--cached", "-z")
    return sorted(
        path
        for path in raw.decode("utf-8", errors="surrogateescape").split("\0")
        if path
    )


def validate_path(path_text: str) -> list[Finding]:
    path = PurePosixPath(path_text)
    findings: list[Finding] = []

    if path.parts and path.parts[0] == "data":
        if len(path.parts) >= 2 and path.parts[1] == "sessions":
            findings.append(
                Finding(path_text, "conteudo de data/sessions/ e proibido")
            )
        elif path == ALLOWED_DATA_FILE:
            pass
        elif (
            len(path.parts) == 2
            and path.name.endswith(ALLOWED_DATA_EXAMPLE_SUFFIX)
        ):
            pass
        else:
            findings.append(
                Finding(
                    path_text,
                    "arquivo em data/ fora da allowlist "
                    "(permitidos: data/README.md e data/*.example.md)",
                )
            )

    name = path.name.lower()
    is_allowed_env_example = name == ALLOWED_ENV_EXAMPLE
    is_dangerous_env = (
        name == ".env"
        or name == ".envrc"
        or name.startswith(".env.")
        or name.endswith(".env")
        or ".env." in name
    )
    if is_dangerous_env and not is_allowed_env_example:
        findings.append(
            Finding(path_text, "arquivo de ambiente real ou perigoso e proibido")
        )

    return findings


def _line_number(content: str, offset: int) -> int:
    return content.count("\n", 0, offset) + 1


def _is_placeholder_or_reference(raw_value: str) -> bool:
    value = raw_value.strip().strip("\"'")
    lowered = value.lower()
    if len(value) < 8:
        return True
    if not value or "..." in value:
        return True
    if lowered in {"none", "null", "undefined", "true", "false"}:
        return True
    if lowered.startswith(REFERENCE_PREFIXES):
        return True
    if any(marker in lowered for marker in PLACEHOLDER_MARKERS):
        return True
    if "getenv(" in lowered or "environ[" in lowered or "secrets." in lowered:
        return True
    if value.startswith(("/", "./", "../")):
        return True
    return False


def scan_content(path_text: str, raw_content: bytes) -> list[Finding]:
    content = raw_content.decode("utf-8", errors="ignore")
    findings: list[Finding] = []

    for label, pattern in SPECIFIC_SECRET_PATTERNS:
        for match in pattern.finditer(content):
            line = _line_number(content, match.start())
            findings.append(Finding(path_text, f"{label} na linha {line}"))

    for match in GENERIC_CREDENTIAL_ASSIGNMENT.finditer(content):
        value = match.group("value")
        if _is_placeholder_or_reference(value):
            continue
        line = _line_number(content, match.start())
        findings.append(
            Finding(
                path_text,
                f"credencial em texto claro detectada na linha {line}",
            )
        )

    return findings


def _index_content(repo_root: Path, path_text: str) -> bytes:
    return _run_git(repo_root, "show", "--no-textconv", f":{path_text}")


def _worktree_content(repo_root: Path, path_text: str) -> bytes | None:
    path = repo_root.joinpath(*PurePosixPath(path_text).parts)
    if not path.exists() and not path.is_symlink():
        return None
    if path.is_symlink():
        return os.readlink(path).encode("utf-8", errors="surrogateescape")
    if not path.is_file():
        return None
    return path.read_bytes()


def content_versions(repo_root: Path, path_text: str) -> Iterable[bytes]:
    index = _index_content(repo_root, path_text)
    yield index

    worktree = _worktree_content(repo_root, path_text)
    if worktree is not None and worktree != index:
        yield worktree


def validate_repository(repo_root: Path) -> tuple[list[Finding], int]:
    paths = tracked_paths(repo_root)
    findings: set[Finding] = set()

    for path_text in paths:
        findings.update(validate_path(path_text))
        for content in content_versions(repo_root, path_text):
            findings.update(scan_content(path_text, content))

    return sorted(findings), len(paths)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bloqueia dados de runtime, arquivos .env e segredos no Git."
    )
    parser.add_argument(
        "--repo-root",
        help="Raiz do repositorio a validar. Por padrao usa git rev-parse.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        repo_root = find_repo_root(args.repo_root)
        findings, checked_count = validate_repository(repo_root)
    except (GuardExecutionError, OSError) as exc:
        print(f"Data Guard: ERRO DE EXECUCAO: {exc}", file=sys.stderr)
        return 2

    if findings:
        print("Data Guard: FALHOU")
        for finding in findings:
            print(f"- {finding.path}: {finding.reason}")
        print(f"Total de violacoes: {len(findings)}")
        return 1

    print(f"Data Guard: OK - {checked_count} arquivos rastreados/staged verificados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
