"""Testes do match heurístico entre vaga e currículo.

`match()` recebe os dois markdowns (vaga e currículo) e devolve um relatório.
As fixtures `job_markdown` e `resume_markdown` vêm do conftest.py — repare que
basta nomeá-las nos parâmetros que o pytest as injeta.
"""

from agents.resume_matcher import (
    ResumeMatcher,
    match_report_from_markdown,
    match_report_to_markdown,
    validate_job_analysis,
    validate_resume_analysis,
)


def test_match_score_fica_entre_0_e_100(job_markdown, resume_markdown):
    report = ResumeMatcher().match(job_markdown, resume_markdown)

    assert isinstance(report["overall_score"], int)
    assert 0 <= report["overall_score"] <= 100


def test_match_reconhece_skill_presente_no_curriculo(job_markdown, resume_markdown):
    # O currículo tem Python e SQL, que a vaga pede. Têm que cair como
    # evidência encontrada (forte ou parcial), não como ausente.
    report = ResumeMatcher().match(job_markdown, resume_markdown)

    encontrados = report["hard_skills_found"] + report["strong_evidence"]
    assert "Python" in encontrados
    assert "Python" not in report["hard_skills_missing"]


def test_match_aponta_skill_ausente(job_markdown, resume_markdown):
    # A vaga pede Excel, mas o currículo não cita. Tem que aparecer como ausente
    # em algum lugar (ferramentas ausentes, no caso).
    report = ResumeMatcher().match(job_markdown, resume_markdown)

    ausentes = report["hard_skills_missing"] + report["tools_missing"]
    assert "Excel" in ausentes


def test_match_devolve_o_contrato_esperado(job_markdown, resume_markdown):
    report = ResumeMatcher().match(job_markdown, resume_markdown)

    for chave in (
        "overall_score", "readiness_level", "score_breakdown",
        "strong_evidence", "partial_evidence", "missing_requirements",
        "safe_resume_suggestions", "do_not_claim", "next_steps",
    ):
        assert chave in report


def test_match_report_roundtrip(job_markdown, resume_markdown):
    original = ResumeMatcher().match(job_markdown, resume_markdown)

    markdown = match_report_to_markdown(original)
    recuperado = match_report_from_markdown(markdown)

    assert recuperado is not None
    assert recuperado["overall_score"] == original["overall_score"]


def test_validadores_aceitam_markdown_real(job_markdown, resume_markdown):
    assert validate_job_analysis(job_markdown) is True
    assert validate_resume_analysis(resume_markdown) is True


def test_validadores_rejeitam_lixo():
    assert validate_job_analysis("nada útil aqui") is False
    assert validate_resume_analysis("nada útil aqui") is False
