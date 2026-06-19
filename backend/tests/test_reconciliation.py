"""Testes da reconciliação heurística entre perfil, currículo e vaga.

``Reconciler.reconcile`` recebe as strings Markdown (perfil, currículo, vaga,
opcionalmente o match) e devolve um diagnóstico de consistência. Os testes
cobrem validadores, parsing do foco, detecção de conflitos nos dois pares
novos (perfil↔currículo e perfil↔vaga), variação do foco e round-trip do
Markdown. As fixtures ``job_markdown`` e ``resume_markdown`` vêm do conftest.py.
"""

from agents.job_description_analyzer import (
    JobDescriptionAnalyzer,
    analysis_to_markdown,
)
from agents.reconciliation import (
    FOCUS_OPTIONS,
    Reconciler,
    normalize_focus,
    parse_focus,
    reconciliation_from_markdown,
    reconciliation_to_markdown,
    validate_profile,
)


# ── Fixtures locais de Markdown ──────────────────────────────────────────────

PROFILE_ALIGNED = (
    "# Perfil\n"
    "Área de interesse: Dados\n"
    "Nível de experiência: Júnior\n"
    "Preferências de trabalho: Remoto\n"
    "Localização: São Paulo\n"
    "Soft skills: Comunicação, Trabalho em equipe\n"
    "Objetivo de carreira: Crescer como analista\n"
    "Habilidades atuais: Python, SQL, Power BI\n"
    "Funções alvo: Analista de Dados\n"
    "Concluído: true\n"
)

# Mesma área/nível do perfil, mas skills de backend (conflito intencional).
PROFILE_DIVERGENT = (
    "# Perfil\n"
    "Área de interesse: Backend\n"
    "Nível de experiência: Sênior\n"
    "Preferências de trabalho: Presencial\n"
    "Localização: Curitiba\n"
    "Soft skills: Liderança\n"
    "Objetivo de carreira: Arquiteto de software\n"
    "Habilidades atuais: Java, Spring\n"
    "Funções alvo: Desenvolvedor Backend\n"
    "Concluído: true\n"
)

PROFILE_INCOMPLETE = (
    "# Perfil\n"
    "Área de interesse: Dados\n"
    "Concluído: false\n"
)

PROFILE_NO_ACCENT_KEYS = (
    # Chaves sem acento NÃO devem validar (o quiz real sempre usa acento).
    "Area de interesse: Dados\n"
    "Nivel de experiencia: Junior\n"
    "Habilidades atuais: Python\n"
    "Concluido: true\n"
)


def _job_markdown(descricao: str = None) -> str:
    """Gera um job-description-analysis.md real via analyzer."""
    if descricao is None:
        descricao = (
            "Analista de Dados Júnior na Acme. "
            "Responsabilidades: desenvolver dashboards no Power BI, analisar KPIs. "
            "Requisitos: experiência com Python e SQL, conhecimento de Excel. "
            "Boa comunicação e trabalho em equipe."
        )
    return analysis_to_markdown(JobDescriptionAnalyzer().analyze(descricao))


# ── validate_profile ─────────────────────────────────────────────────────────


def test_validate_profile_aceita_perfil_completo():
    assert validate_profile(PROFILE_ALIGNED) is True


def test_validate_profile_rejeita_incompleto():
    assert validate_profile(PROFILE_INCOMPLETE) is False


def test_validate_profile_rejeita_chaves_sem_acento():
    # O quiz real grava com acento; chaves sem acento não devem passar.
    assert validate_profile(PROFILE_NO_ACCENT_KEYS) is False


def test_validate_profile_rejeita_nao_concluido():
    perfil = PROFILE_ALIGNED.replace("Concluído: true", "Concluído: false")
    assert validate_profile(perfil) is False


# ── parse_focus ──────────────────────────────────────────────────────────────


def test_parse_focus_le_foco_valido_com_acento():
    perfil = PROFILE_ALIGNED + "Foco da candidatura: currículo\n"
    assert parse_focus(perfil) == "curriculo"


def test_parse_focus_le_foco_valido_sem_acento():
    perfil = PROFILE_ALIGNED + "Foco da candidatura: perfil\n"
    assert parse_focus(perfil) == "perfil"


def test_parse_focus_retorna_none_se_ausente():
    assert parse_focus(PROFILE_ALIGNED) is None


def test_parse_focus_retorna_none_se_invalido():
    perfil = PROFILE_ALIGNED + "Foco da candidatura: dinheiro\n"
    assert parse_focus(perfil) is None


def test_normalize_focus_aceita_curriculo_com_acento():
    assert normalize_focus("currículo") == "curriculo"


def test_normalize_focus_rejeita_valor_invalido():
    assert normalize_focus("dinheiro") is None


def test_focus_options_contem_os_tres_valores():
    assert FOCUS_OPTIONS == {"perfil", "curriculo", "vaga"}


# ── Reconciler.reconcile — conflitos ─────────────────────────────────────────


def test_reconcile_detecta_conflito_perfil_curriculo(resume_markdown):
    # Perfil declara backend/Java; currículo tem Python/SQL.
    result = Reconciler().reconcile(
        PROFILE_DIVERGENT, resume_markdown, _job_markdown(), focus="vaga"
    )
    fields_pr = {c["field"] for c in result["profile_resume_conflicts"]}
    # Habilidades técnicas e Soft skills divergem radicalmente.
    assert "Habilidades técnicas" in fields_pr


def test_reconcile_detecta_conflito_perfil_vaga(resume_markdown):
    result = Reconciler().reconcile(
        PROFILE_DIVERGENT, resume_markdown, _job_markdown(), focus="vaga"
    )
    fields_pj = {c["field"] for c in result["profile_job_conflicts"]}
    # Nível (Sênior vs Júnior) e skills divergem.
    assert "Nível" in fields_pj
    assert "Habilidades técnicas" in fields_pj


def test_reconcile_nao_gera_conflito_quando_alinhado(job_markdown, resume_markdown):
    # Perfil declarado coincide com currículo e vaga (dados, júnior, Python/SQL).
    result = Reconciler().reconcile(
        PROFILE_ALIGNED, resume_markdown, job_markdown, focus="vaga"
    )
    # Pode haver pequenos desalinhamentos de skills (Excel/Power BI), mas
    # nível e área NÃO devem aparecer como conflito.
    all_conflicts = (
        result["profile_resume_conflicts"] + result["profile_job_conflicts"]
    )
    fields = {c["field"] for c in all_conflicts}
    assert "Nível" not in fields
    assert "Área" not in fields


def test_reconcile_devolve_contrato_completo(job_markdown, resume_markdown):
    result = Reconciler().reconcile(
        PROFILE_ALIGNED, resume_markdown, job_markdown, focus="vaga"
    )
    for chave in (
        "focus",
        "consistency_score",
        "consistency_level",
        "profile_resume_conflicts",
        "profile_job_conflicts",
        "resume_job_summary",
        "match_score",
        "aligned_fields",
        "focus_recommendations",
        "next_steps",
    ):
        assert chave in result


def test_reconcile_score_fica_entre_0_e_100(job_markdown, resume_markdown):
    result = Reconciler().reconcile(
        PROFILE_ALIGNED, resume_markdown, job_markdown, focus="vaga"
    )
    assert isinstance(result["consistency_score"], int)
    assert 0 <= result["consistency_score"] <= 100


def test_reconcile_respeita_foco_perfil(job_markdown, resume_markdown):
    result = Reconciler().reconcile(
        PROFILE_DIVERGENT, resume_markdown, job_markdown, focus="perfil"
    )
    assert result["focus"] == "perfil"
    # Com foco no perfil, a recomendação manda manter o perfil como referência.
    recs = " ".join(result["focus_recommendations"]).lower()
    assert "perfil" in recs


def test_reconcile_normaliza_foco_explicito_com_acento(job_markdown, resume_markdown):
    result = Reconciler().reconcile(
        PROFILE_DIVERGENT, resume_markdown, job_markdown, focus="currículo"
    )
    assert result["focus"] == "curriculo"
    recs = " ".join(result["focus_recommendations"]).lower()
    assert "currículo" in recs


def test_reconcile_rejeita_foco_explicito_invalido(job_markdown, resume_markdown):
    import pytest

    with pytest.raises(ValueError):
        Reconciler().reconcile(
            PROFILE_ALIGNED, resume_markdown, job_markdown, focus="dinheiro"
        )


def test_reconcile_le_foco_do_perfil_se_nao_passado(job_markdown, resume_markdown):
    perfil_com_foco = PROFILE_ALIGNED + "Foco da candidatura: currículo\n"
    result = Reconciler().reconcile(
        perfil_com_foco, resume_markdown, job_markdown
    )
    assert result["focus"] == "curriculo"


def test_reconcile_default_vaga_quando_sem_foco(job_markdown, resume_markdown):
    result = Reconciler().reconcile(
        PROFILE_ALIGNED, resume_markdown, job_markdown
    )
    assert result["focus"] == "vaga"


def test_reconcile_reusa_match_quando_fornecido(job_markdown, resume_markdown):
    # Passa um match_content sintético; o match_score vem dele, não recalculado.
    from agents.resume_matcher import match_report_to_markdown

    fake_match = {
        "overall_score": 77,
        "readiness_level": "parcialmente aderente",
        "job_title": "Analista de Dados",
        "resume_summary": "Currículo de dados",
        "score_breakdown": {
            "hard_skills": 40,
            "tools": 15,
            "soft_skills": 10,
            "keywords": 7,
            "seniority_area": 5,
        },
        "strong_evidence": [],
        "partial_evidence": [],
        "missing_requirements": [],
        "hard_skills_found": [],
        "hard_skills_missing": [],
        "soft_skills_found": [],
        "soft_skills_missing": [],
        "tools_found": [],
        "tools_missing": [],
        "matched_keywords": [],
        "missing_keywords": [],
        "strengths": [],
        "critical_gaps": [],
        "safe_resume_suggestions": [],
        "do_not_claim": [],
        "next_steps": [],
    }
    match_md = match_report_to_markdown(fake_match)
    result = Reconciler().reconcile(
        PROFILE_ALIGNED,
        resume_markdown,
        job_markdown,
        match_content=match_md,
        focus="vaga",
    )
    assert result["match_score"] == 77


def test_reconcile_ignora_nao_identificado_em_listas(resume_markdown):
    job_sem_ferramentas = (
        "# Análise da descrição da vaga\n\n"
        "## Resumo\n\n"
        "* Título: Analista de Dados\n"
        "* Empresa: Acme\n"
        "* Senioridade: Júnior\n"
        "* Modalidade: Remoto\n"
        "* Localização: São Paulo\n\n"
        "## Hard skills\n\n"
        "* Python\n"
        "* SQL\n\n"
        "## Soft skills\n\n"
        "* Comunicação\n\n"
        "## Ferramentas\n\n"
        "* Não identificado\n"
    )
    result = Reconciler().reconcile(
        PROFILE_ALIGNED, resume_markdown, job_sem_ferramentas, focus="vaga"
    )
    assert {
        c["field"] for c in result["profile_job_conflicts"]
    } == set()


# ── Round-trip Markdown ──────────────────────────────────────────────────────


def test_reconciliation_roundtrip(job_markdown, resume_markdown):
    original = Reconciler().reconcile(
        PROFILE_DIVERGENT, resume_markdown, job_markdown, focus="curriculo"
    )
    markdown = reconciliation_to_markdown(original)
    recuperado = reconciliation_from_markdown(markdown)

    assert recuperado is not None
    assert recuperado["focus"] == original["focus"]
    assert recuperado["consistency_score"] == original["consistency_score"]
    assert recuperado["match_score"] == original["match_score"]


def test_reconciliation_from_markdown_retorna_none_para_lixo():
    assert reconciliation_from_markdown("# qualquer coisa\nsem score") is None
