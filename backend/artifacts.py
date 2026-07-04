"""Registro e validação central de artefatos por sessão."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from artifact_lineage import get_all_dependents
from session import write_text_atomic


MANIFEST_FILENAME = "artifact-manifest.json"
MANIFEST_SCHEMA_VERSION = 1
ArtifactStatus = Literal["current", "stale", "corrupted", "legacy"]
VALID_ARTIFACT_STATUSES = frozenset({"current", "stale", "corrupted", "legacy"})


class ArtifactRegistryError(RuntimeError):
    """Erro controlado do registro de artefatos."""


class ArtifactManifestError(ArtifactRegistryError):
    """Manifesto ausente de contrato válido."""


class ArtifactContentError(ArtifactRegistryError):
    """Conteúdo de artefato indisponível para registro ou validação."""


@dataclass(frozen=True)
class ArtifactMetadata:
    schema_version: int
    status: ArtifactStatus
    content_hash: str
    input_hashes: dict[str, str]
    generator_version: str
    generated_at: str


@dataclass
class ArtifactManifest:
    schema_version: int = MANIFEST_SCHEMA_VERSION
    artifacts: dict[str, ArtifactMetadata] = field(default_factory=dict)
    legacy: bool = False


def calculate_content_hash(content: str | bytes) -> str:
    payload = content.encode("utf-8") if isinstance(content, str) else content
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def load_manifest(session_dir: Path) -> ArtifactManifest:
    path = Path(session_dir) / MANIFEST_FILENAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ArtifactManifest(legacy=True)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactManifestError("Manifesto de artefatos corrompido ou ilegível.") from exc
    except OSError as exc:
        raise ArtifactManifestError("Não foi possível ler o manifesto de artefatos.") from exc

    return _parse_manifest(payload)


def save_manifest(session_dir: Path, manifest: ArtifactManifest) -> None:
    payload = _manifest_to_dict(manifest)
    _parse_manifest(payload)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    write_text_atomic(Path(session_dir) / MANIFEST_FILENAME, serialized)


def register_artifact(
    session_dir: Path,
    artifact_name: str,
    artifact_path: Path | None = None,
    *,
    content: str | bytes | None = None,
    input_hashes: Mapping[str, str] | None = None,
    generator_version: str,
    schema_version: int = 1,
    generated_at: str | None = None,
) -> ArtifactMetadata:
    if not artifact_name.strip():
        raise ArtifactManifestError("Nome de artefato inválido.")
    if type(schema_version) is not int or schema_version < 1:
        raise ArtifactManifestError("Versão de schema do artefato inválida.")
    if not generator_version.strip():
        raise ArtifactManifestError("Versão do gerador inválida.")

    normalized_inputs = dict(input_hashes or {})
    _validate_hashes(normalized_inputs, "input_hashes")

    if (artifact_path is None) == (content is None):
        raise ArtifactContentError(
            "Informe exatamente um caminho ou conteúdo para registrar o artefato."
        )
    if content is None:
        try:
            artifact_content: str | bytes = Path(artifact_path).read_text(
                encoding="utf-8"
            )
        except (OSError, UnicodeDecodeError) as exc:
            raise ArtifactContentError(
                f"Não foi possível ler o artefato '{artifact_name}'."
            ) from exc
    else:
        artifact_content = content

    metadata = ArtifactMetadata(
        schema_version=schema_version,
        status="current",
        content_hash=calculate_content_hash(artifact_content),
        input_hashes=normalized_inputs,
        generator_version=generator_version,
        generated_at=generated_at or _utc_now(),
    )
    manifest = load_manifest(session_dir)
    manifest.legacy = False
    manifest.artifacts[artifact_name] = metadata
    save_manifest(session_dir, manifest)
    return metadata


def get_artifact_status(
    session_dir: Path,
    artifact_name: str,
    *,
    artifact_path: Path | None = None,
    current_input_hashes: Mapping[str, str] | None = None,
) -> ArtifactStatus:
    manifest = load_manifest(session_dir)
    if manifest.legacy:
        return "legacy"

    metadata = manifest.artifacts.get(artifact_name)
    if metadata is None:
        return "legacy"

    if artifact_path is not None:
        try:
            content = Path(artifact_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            return "corrupted"
        except UnicodeDecodeError:
            return "corrupted"
        except OSError as exc:
            raise ArtifactContentError(
                f"Não foi possível validar o artefato '{artifact_name}'."
            ) from exc
        if calculate_content_hash(content) != metadata.content_hash:
            return "corrupted"

    if current_input_hashes is not None:
        normalized_inputs = dict(current_input_hashes)
        _validate_hashes(normalized_inputs, "current_input_hashes")
        if normalized_inputs != metadata.input_hashes:
            return "stale"

    return metadata.status


def mark_dependents_stale(session_dir: Path, artifact_name: str) -> set[str]:
    manifest = load_manifest(session_dir)
    if manifest.legacy:
        return set()

    stale_dependents: set[str] = set()
    changed = False
    for dependent in get_all_dependents(artifact_name):
        metadata = manifest.artifacts.get(dependent)
        if metadata is None or metadata.status in {"corrupted", "legacy"}:
            continue
        stale_dependents.add(dependent)
        if metadata.status != "stale":
            manifest.artifacts[dependent] = replace(metadata, status="stale")
            changed = True

    if changed:
        save_manifest(session_dir, manifest)
    return stale_dependents


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_manifest(payload: object) -> ArtifactManifest:
    if not isinstance(payload, dict):
        raise ArtifactManifestError("Manifesto de artefatos deve ser um objeto JSON.")

    schema_version = payload.get("schema_version")
    if type(schema_version) is not int or schema_version != MANIFEST_SCHEMA_VERSION:
        raise ArtifactManifestError("Versão do manifesto de artefatos não suportada.")

    raw_artifacts = payload.get("artifacts")
    if not isinstance(raw_artifacts, dict):
        raise ArtifactManifestError("Campo 'artifacts' inválido no manifesto.")

    artifacts: dict[str, ArtifactMetadata] = {}
    for artifact_name, raw_metadata in raw_artifacts.items():
        if not isinstance(artifact_name, str) or not artifact_name.strip():
            raise ArtifactManifestError("Nome de artefato inválido no manifesto.")
        artifacts[artifact_name] = _parse_metadata(raw_metadata)

    return ArtifactManifest(schema_version=schema_version, artifacts=artifacts)


def _parse_metadata(payload: object) -> ArtifactMetadata:
    if not isinstance(payload, dict):
        raise ArtifactManifestError("Metadados de artefato inválidos.")

    schema_version = payload.get("schema_version")
    status = payload.get("status")
    content_hash = payload.get("content_hash")
    input_hashes = payload.get("input_hashes")
    generator_version = payload.get("generator_version")
    generated_at = payload.get("generated_at")

    if type(schema_version) is not int or schema_version < 1:
        raise ArtifactManifestError("Versão de schema de artefato inválida.")
    if not isinstance(status, str) or status not in VALID_ARTIFACT_STATUSES:
        raise ArtifactManifestError("Status de artefato inválido.")
    if not isinstance(content_hash, str) or not _is_sha256(content_hash):
        raise ArtifactManifestError("Hash de conteúdo inválido.")
    if not isinstance(input_hashes, dict):
        raise ArtifactManifestError("Hashes de entrada inválidos.")
    _validate_hashes(input_hashes, "input_hashes")
    if not isinstance(generator_version, str) or not generator_version.strip():
        raise ArtifactManifestError("Versão do gerador inválida.")
    if not isinstance(generated_at, str) or not generated_at.strip():
        raise ArtifactManifestError("Data de geração inválida.")

    return ArtifactMetadata(
        schema_version=schema_version,
        status=status,
        content_hash=content_hash,
        input_hashes=dict(input_hashes),
        generator_version=generator_version,
        generated_at=generated_at,
    )


def _manifest_to_dict(manifest: ArtifactManifest) -> dict[str, object]:
    return {
        "schema_version": manifest.schema_version,
        "artifacts": {
            name: {
                "schema_version": metadata.schema_version,
                "status": metadata.status,
                "content_hash": metadata.content_hash,
                "input_hashes": dict(metadata.input_hashes),
                "generator_version": metadata.generator_version,
                "generated_at": metadata.generated_at,
            }
            for name, metadata in manifest.artifacts.items()
        },
    }


def _validate_hashes(hashes: Mapping[object, object], field_name: str) -> None:
    if any(
        not isinstance(name, str)
        or not name.strip()
        or not isinstance(value, str)
        or not _is_sha256(value)
        for name, value in hashes.items()
    ):
        raise ArtifactManifestError(f"Campo '{field_name}' contém hash inválido.")


def _is_sha256(value: str) -> bool:
    prefix, separator, digest = value.partition(":")
    return (
        separator == ":"
        and prefix == "sha256"
        and len(digest) == 64
        and all(character in "0123456789abcdef" for character in digest)
    )
