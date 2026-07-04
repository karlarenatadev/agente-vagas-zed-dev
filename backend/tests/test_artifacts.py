"""Testes do registro central de artefatos."""

from __future__ import annotations

from dataclasses import replace

import pytest

import session
from artifacts import (
    MANIFEST_FILENAME,
    ArtifactManifest,
    ArtifactManifestError,
    ArtifactMetadata,
    ArtifactStateError,
    calculate_content_hash,
    ensure_artifact_consumable,
    get_artifact_status,
    load_manifest,
    mark_dependents_stale,
    register_artifact,
    save_manifest,
)


GENERATED_AT = "2026-07-04T00:00:00Z"


def _metadata(
    content: str,
    *,
    status: str = "current",
    input_hashes: dict[str, str] | None = None,
) -> ArtifactMetadata:
    return ArtifactMetadata(
        schema_version=1,
        status=status,
        content_hash=calculate_content_hash(content),
        input_hashes=input_hashes or {},
        generator_version="test:v1",
        generated_at=GENERATED_AT,
    )


def test_hash_igual_para_o_mesmo_conteudo():
    assert calculate_content_hash("conteúdo") == calculate_content_hash("conteúdo")
    assert calculate_content_hash("conteúdo") == calculate_content_hash(
        "conteúdo".encode("utf-8")
    )


def test_hash_diferente_para_conteudo_diferente():
    assert calculate_content_hash("conteúdo A") != calculate_content_hash("conteúdo B")


def test_manifesto_ausente_retorna_sessao_legada(tmp_path):
    manifest = load_manifest(tmp_path)

    assert manifest.legacy is True
    assert manifest.schema_version == 1
    assert manifest.artifacts == {}
    assert get_artifact_status(tmp_path, "match") == "legacy"
    assert not (tmp_path / MANIFEST_FILENAME).exists()


def test_manifesto_e_salvo_e_carregado_corretamente(tmp_path):
    manifest = ArtifactManifest(
        artifacts={"match": _metadata("match atual")},
    )

    save_manifest(tmp_path, manifest)
    loaded = load_manifest(tmp_path)

    assert loaded.legacy is False
    assert loaded == manifest


def test_registro_cria_metadados_esperados(tmp_path):
    artifact_path = tmp_path / "resume-match-report.md"
    artifact_path.write_text("match atual", encoding="utf-8")
    resume_hash = calculate_content_hash("currículo")
    job_hash = calculate_content_hash("vaga")

    metadata = register_artifact(
        tmp_path,
        "match",
        artifact_path,
        input_hashes={"resume": resume_hash, "job_description": job_hash},
        generator_version="match:v1",
        generated_at=GENERATED_AT,
    )

    assert metadata.status == "current"
    assert metadata.content_hash == calculate_content_hash("match atual")
    assert metadata.input_hashes == {
        "resume": resume_hash,
        "job_description": job_hash,
    }
    assert metadata.generator_version == "match:v1"
    assert metadata.generated_at == GENERATED_AT
    assert load_manifest(tmp_path).artifacts["match"] == metadata


def test_registro_aceita_conteudo_antes_da_escrita_do_artefato(tmp_path):
    artifact_path = tmp_path / "resume-analysis.md"

    metadata = register_artifact(
        tmp_path,
        "resume",
        content="currículo analisado",
        generator_version="resume-analysis:v1",
        generated_at=GENERATED_AT,
    )

    assert metadata.content_hash == calculate_content_hash("currículo analisado")
    assert load_manifest(tmp_path).artifacts["resume"] == metadata
    assert not artifact_path.exists()


def test_conteudo_alterado_fora_da_aplicacao_e_detectado_sem_apagar(tmp_path):
    artifact_path = tmp_path / "resume-match-report.md"
    artifact_path.write_text("match original", encoding="utf-8")
    register_artifact(
        tmp_path,
        "match",
        artifact_path,
        generator_version="match:v1",
        generated_at=GENERATED_AT,
    )

    artifact_path.write_text("match alterado externamente", encoding="utf-8")

    assert (
        get_artifact_status(tmp_path, "match", artifact_path=artifact_path)
        == "corrupted"
    )
    assert artifact_path.read_text(encoding="utf-8") == "match alterado externamente"
    assert load_manifest(tmp_path).artifacts["match"].status == "current"


def test_hash_de_entrada_divergente_retorna_stale(tmp_path):
    artifact_path = tmp_path / "resume-match-report.md"
    artifact_path.write_text("match atual", encoding="utf-8")
    original_resume_hash = calculate_content_hash("currículo original")
    register_artifact(
        tmp_path,
        "match",
        artifact_path,
        input_hashes={"resume": original_resume_hash},
        generator_version="match:v1",
        generated_at=GENERATED_AT,
    )

    status = get_artifact_status(
        tmp_path,
        "match",
        artifact_path=artifact_path,
        current_input_hashes={
            "resume": calculate_content_hash("currículo atualizado")
        },
    )

    assert status == "stale"
    assert artifact_path.exists()


@pytest.mark.parametrize("status", ["stale", "corrupted"])
def test_consumo_de_artefato_invalido_gera_erro_controlado(
    tmp_path,
    status,
):
    artifact_path = tmp_path / "resume-match-report.md"
    artifact_path.write_text("match atual", encoding="utf-8")
    manifest = ArtifactManifest(
        artifacts={"match": _metadata("match atual", status=status)},
    )
    save_manifest(tmp_path, manifest)

    with pytest.raises(ArtifactStateError) as error:
        ensure_artifact_consumable(tmp_path, "match", artifact_path)

    assert error.value.status == status
    assert "match" in str(error.value).casefold()
    assert artifact_path.exists()


def test_consumo_de_artefato_legado_preserva_compatibilidade(tmp_path):
    artifact_path = tmp_path / "resume-match-report.md"
    artifact_path.write_text("match legado", encoding="utf-8")

    status = ensure_artifact_consumable(tmp_path, "match", artifact_path)

    assert status == "legacy"
    assert artifact_path.read_text(encoding="utf-8") == "match legado"


def test_alteracao_de_entrada_marca_dependentes_stale_sem_apagar(tmp_path):
    dependent_names = {
        "match",
        "reconciliation",
        "tailoring",
        "pdi",
        "interview",
    }
    original_contents: dict[str, bytes] = {}
    manifest = ArtifactManifest()
    for name in dependent_names:
        artifact_path = tmp_path / f"{name}.md"
        artifact_path.write_text(f"conteúdo de {name}", encoding="utf-8")
        original_contents[name] = artifact_path.read_bytes()
        manifest.artifacts[name] = _metadata(f"conteúdo de {name}")
    save_manifest(tmp_path, manifest)

    marked = mark_dependents_stale(tmp_path, "resume")
    loaded = load_manifest(tmp_path)

    assert marked == dependent_names
    assert all(loaded.artifacts[name].status == "stale" for name in marked)
    assert all(
        (tmp_path / f"{name}.md").read_bytes() == original_contents[name]
        for name in marked
    )


def test_dependentes_transitivos_nao_duplicam_e_corrupcao_e_preservada(tmp_path):
    manifest = ArtifactManifest(
        artifacts={
            "match": _metadata("match"),
            "reconciliation": _metadata("reconciliation"),
            "tailoring": _metadata("tailoring"),
            "pdi": _metadata("pdi"),
            "interview": _metadata("interview", status="corrupted"),
        }
    )
    save_manifest(tmp_path, manifest)

    marked = mark_dependents_stale(tmp_path, "resume")
    loaded = load_manifest(tmp_path)

    assert marked == {"match", "reconciliation", "tailoring", "pdi"}
    assert len(marked) == 4
    assert loaded.artifacts["interview"].status == "corrupted"


def test_manifesto_invalido_gera_erro_controlado_e_e_preservado(tmp_path):
    path = tmp_path / MANIFEST_FILENAME
    invalid_content = '{"schema_version": 1, "artifacts":'
    path.write_text(invalid_content, encoding="utf-8")

    with pytest.raises(ArtifactManifestError, match="corrompido"):
        load_manifest(tmp_path)

    assert path.read_text(encoding="utf-8") == invalid_content


def test_falha_atomica_preserva_manifesto_anterior_e_remove_temporario(
    tmp_path,
    monkeypatch,
):
    original = ArtifactManifest(artifacts={"match": _metadata("match original")})
    save_manifest(tmp_path, original)
    manifest_path = tmp_path / MANIFEST_FILENAME
    original_bytes = manifest_path.read_bytes()
    updated = ArtifactManifest(
        artifacts={
            "match": replace(
                original.artifacts["match"],
                content_hash=calculate_content_hash("match atualizado"),
            )
        }
    )

    def fail_replace(source, destination):
        raise OSError("falha simulada")

    monkeypatch.setattr(session.os, "replace", fail_replace)

    with pytest.raises(OSError, match="falha simulada"):
        save_manifest(tmp_path, updated)

    assert manifest_path.read_bytes() == original_bytes
    assert list(tmp_path.glob(f"{MANIFEST_FILENAME}.tmp-*")) == []
