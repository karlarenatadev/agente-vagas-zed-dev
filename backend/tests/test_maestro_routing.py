"""Testes do roteamento conversacional da Esteira de Candidatura (E–I).

Cobre:
- Menu E abre await_job_description.
- Colar vaga curta não cria artefato; colar vaga válida analisa, salva e
  invalida downstream; "menu" cancela.
- F/G/H/I bloqueiam com mensagem amigável sem pré-requisitos e rodam quando a
  cadeia está completa, criando os artefatos esperados.
- A cadeia completa E→F→G→H→I sobre o mesmo tmp.
"""

import asyncio

from agents.maestro import MaestroAgent
from artifacts import (
    MANIFEST_FILENAME,
    get_artifact_status,
    register_artifact,
)
from session import SessionPaths


VALID_JOB_DESCRIPTION = (
    "Analista de Dados Júnior na Acme. "
    "Responsabilidades: desenvolver dashboards no Power BI, analisar KPIs. "
    "Requisitos: experiência com Python e SQL, conhecimento de Excel. "
    "Boa comunicação e trabalho em equipe."
)


def _collect(gen):
    """Consome um async generator e devolve a concatenação dos tokens."""
    return asyncio.run(_adrain(gen))


async def _adrain(gen):
    return [token async for token in gen]


def _seed_profile(paths) -> None:
    paths.PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.PROFILE_FILE.write_text(
        "Área de interesse: Dados\n"
        "Nível de experiência: Pleno\n"
        "Habilidades atuais: Python, SQL\n"
        "Funções alvo: Analista de Dados\n"
        "Concluído: true\n",
        encoding="utf-8",
    )


def _seed_resume(paths, resume_markdown: str) -> None:
    paths.RESUME_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.RESUME_ANALYSIS_FILE.write_text(resume_markdown, encoding="utf-8")


# ── Menu E ────────────────────────────────────────────────────────────────────


def test_menu_e_entra_em_await_job_description(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)

    tokens = _collect(agent._handle_menu("E"))

    joined = "".join(tokens)
    assert "__STATE__:await_job_description" in joined
    assert "40 caracteres" in joined
    # Não criou análise ainda — só pediu a descrição.
    assert not paths.JOB_DESCRIPTION_ANALYSIS_FILE.exists()


# ── Colar vaga ────────────────────────────────────────────────────────────────


def test_colar_vaga_curta_reexibe_instrucao(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)
    agent.mode = "await_job_description"

    tokens = _collect(agent._handle_job_description_paste("oi"))

    joined = "".join(tokens)
    assert "muito curta" in joined.lower()
    assert "__STATE__:await_job_description" in joined
    assert not paths.JOB_DESCRIPTION_ANALYSIS_FILE.exists()


def test_colar_vaga_valida_marca_downstream_stale_sem_apagar(
    tmp_path,
    resume_markdown,
    job_markdown,
):
    paths = SessionPaths("alice", base_dir=tmp_path)
    _seed_resume(paths, resume_markdown)
    dependent_paths = {
        "match": paths.RESUME_MATCH_REPORT_FILE,
        "reconciliation": paths.RECONCILIATION_FILE,
        "tailoring": paths.RESUME_TAILORING_SUGGESTIONS_FILE,
        "pdi": paths.PDI_PLAN_FILE,
        "interview": paths.INTERVIEW_FILE,
    }
    for name, path in dependent_paths.items():
        path.write_text(
            job_markdown if name == "match" else f"velho: {name}",
            encoding="utf-8",
        )
        register_artifact(
            paths.dir,
            name,
            path,
            generator_version=f"{name}:test",
        )
    agent = MaestroAgent(paths)
    agent.mode = "await_job_description"

    tokens = _collect(agent._handle_job_description_paste(VALID_JOB_DESCRIPTION))

    joined = "".join(tokens)
    assert paths.JOB_DESCRIPTION_ANALYSIS_FILE.exists()
    assert "Vaga analisada" in joined  # resumo do dispatcher
    assert "Senioridade" in joined  # campo do resumo
    assert "__STATE__:menu" in joined
    assert "preservou os relatórios anteriores" in joined
    assert get_artifact_status(
        paths.dir,
        "job_description",
        artifact_path=paths.JOB_DESCRIPTION_ANALYSIS_FILE,
    ) == "current"
    assert all(path.exists() for path in dependent_paths.values())
    assert all(
        get_artifact_status(paths.dir, name, artifact_path=path) == "stale"
        for name, path in dependent_paths.items()
    )


def test_colar_vaga_manifesto_corrompido_preserva_entrada_e_retorna_menu(
    tmp_path,
):
    paths = SessionPaths("alice", base_dir=tmp_path)
    paths.dir.mkdir(parents=True)
    paths.JOB_DESCRIPTION_ANALYSIS_FILE.write_text(
        "vaga anterior",
        encoding="utf-8",
    )
    manifest_path = paths.dir / MANIFEST_FILENAME
    invalid_manifest = '{"schema_version": 1, "artifacts":'
    manifest_path.write_text(invalid_manifest, encoding="utf-8")
    agent = MaestroAgent(paths)
    agent.mode = "await_job_description"

    tokens = _collect(agent._handle_job_description_paste(VALID_JOB_DESCRIPTION))

    joined = "".join(tokens)
    assert "registro de artefatos" in joined
    assert "__STATE__:menu" in joined
    assert (
        paths.JOB_DESCRIPTION_ANALYSIS_FILE.read_text(encoding="utf-8")
        == "vaga anterior"
    )
    assert manifest_path.read_text(encoding="utf-8") == invalid_manifest


def test_colar_vaga_comando_menu_cancela(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)
    agent.mode = "await_job_description"

    tokens = _collect(agent._handle_job_description_paste("menu"))

    joined = "".join(tokens)
    assert "__STATE__:menu" in joined
    assert "ESTEIRA" in joined
    assert not paths.JOB_DESCRIPTION_ANALYSIS_FILE.exists()


# ── F: match ──────────────────────────────────────────────────────────────────


def test_match_sem_prerequisitos_bloqueia(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)

    tokens = _collect(agent._dispatch_resume_match())

    joined = "".join(tokens)
    assert "__STATE__:menu" in joined
    assert "vaga" in joined.lower() or "currículo" in joined.lower()
    assert not paths.RESUME_MATCH_REPORT_FILE.exists()


def test_match_com_prerequisitos_cria_artefato(tmp_path, resume_markdown, job_markdown):
    paths = SessionPaths("alice", base_dir=tmp_path)
    _seed_resume(paths, resume_markdown)
    paths.JOB_DESCRIPTION_ANALYSIS_FILE.write_text(job_markdown, encoding="utf-8")
    agent = MaestroAgent(paths)

    tokens = _collect(agent._dispatch_resume_match())

    joined = "".join(tokens)
    assert paths.RESUME_MATCH_REPORT_FILE.exists()
    assert "overall_score" in joined.lower() or "/100" in joined
    assert "__STATE__:menu" in joined


# ── G: tailoring ──────────────────────────────────────────────────────────────


def test_tailoring_sem_match_bloqueia(tmp_path, resume_markdown, job_markdown):
    paths = SessionPaths("alice", base_dir=tmp_path)
    _seed_resume(paths, resume_markdown)
    paths.JOB_DESCRIPTION_ANALYSIS_FILE.write_text(job_markdown, encoding="utf-8")
    agent = MaestroAgent(paths)

    tokens = _collect(agent._dispatch_resume_tailoring())

    joined = "".join(tokens)
    assert "__STATE__:menu" in joined
    assert not paths.RESUME_TAILORING_SUGGESTIONS_FILE.exists()


# ── H: PDI ────────────────────────────────────────────────────────────────────


def test_pdi_sem_cadeia_bloqueia(tmp_path, resume_markdown, job_markdown, match_markdown):
    paths = SessionPaths("alice", base_dir=tmp_path)
    _seed_resume(paths, resume_markdown)
    paths.JOB_DESCRIPTION_ANALYSIS_FILE.write_text(job_markdown, encoding="utf-8")
    paths.RESUME_MATCH_REPORT_FILE.write_text(match_markdown, encoding="utf-8")
    # Falta o tailoring → deve bloquear.
    agent = MaestroAgent(paths)

    tokens = _collect(agent._dispatch_pdi())

    joined = "".join(tokens)
    assert "__STATE__:menu" in joined
    assert not paths.PDI_PLAN_FILE.exists()


# ── I: reconciliação ──────────────────────────────────────────────────────────


def test_reconciliacao_sem_perfil_bloqueia(tmp_path, resume_markdown, job_markdown):
    paths = SessionPaths("alice", base_dir=tmp_path)
    _seed_resume(paths, resume_markdown)
    paths.JOB_DESCRIPTION_ANALYSIS_FILE.write_text(job_markdown, encoding="utf-8")
    agent = MaestroAgent(paths)

    tokens = _collect(agent._dispatch_reconciliation())

    joined = "".join(tokens)
    assert "__STATE__:menu" in joined
    assert not paths.RECONCILIATION_FILE.exists()


def test_reconciliacao_completa_cria_artefato(tmp_path, resume_markdown, job_markdown):
    paths = SessionPaths("alice", base_dir=tmp_path)
    _seed_profile(paths)
    _seed_resume(paths, resume_markdown)
    paths.JOB_DESCRIPTION_ANALYSIS_FILE.write_text(job_markdown, encoding="utf-8")
    agent = MaestroAgent(paths)

    tokens = _collect(agent._dispatch_reconciliation())

    joined = "".join(tokens)
    assert paths.RECONCILIATION_FILE.exists()
    assert "/100" in joined
    assert "__STATE__:menu" in joined


# ── Cadeia completa E → F → G → H → I ─────────────────────────────────────────


def test_cadeia_completa_e_f_g_h_i(tmp_path, resume_markdown):
    paths = SessionPaths("alice", base_dir=tmp_path)
    _seed_profile(paths)
    _seed_resume(paths, resume_markdown)
    agent = MaestroAgent(paths)

    # E: colar vaga válida.
    e_tokens = _collect(agent._handle_job_description_paste(VALID_JOB_DESCRIPTION))
    assert paths.JOB_DESCRIPTION_ANALYSIS_FILE.exists()
    assert "__STATE__:menu" in "".join(e_tokens)

    # F: match.
    f_tokens = _collect(agent._dispatch_resume_match())
    assert paths.RESUME_MATCH_REPORT_FILE.exists()
    assert "__STATE__:menu" in "".join(f_tokens)

    # G: tailoring.
    g_tokens = _collect(agent._dispatch_resume_tailoring())
    assert paths.RESUME_TAILORING_SUGGESTIONS_FILE.exists()
    assert "__STATE__:menu" in "".join(g_tokens)

    # H: PDI.
    h_tokens = _collect(agent._dispatch_pdi())
    assert paths.PDI_PLAN_FILE.exists()
    assert "__STATE__:menu" in "".join(h_tokens)

    # I: reconciliação.
    i_tokens = _collect(agent._dispatch_reconciliation())
    assert paths.RECONCILIATION_FILE.exists()
    assert "__STATE__:menu" in "".join(i_tokens)
