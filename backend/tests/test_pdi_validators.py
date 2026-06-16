"""Testes dos validadores de pré-requisito do PDI.

Antes de gerar um PDI, o gerador checa se os artefatos de entrada existem e
fazem sentido. Aqui testamos esses validadores — inclusive alimentando-os com
o relatório de match REAL gerado pelo matcher (os testes se encadeiam).
"""

from agents.resume_matcher import ResumeMatcher, match_report_to_markdown
from agents.pdi_generator import (
    pdi_from_markdown,
    validate_job_analysis,
    validate_match_report,
    validate_resume_analysis,
)


def test_validate_match_report_aceita_relatorio_real(job_markdown, resume_markdown):
    # Gera um relatório de aderência de verdade e confirma que o PDI o aceita
    # como entrada válida. É o tipo de teste que pega quebras de contrato entre
    # dois agentes que conversam por arquivo.
    report_md = match_report_to_markdown(
        ResumeMatcher().match(job_markdown, resume_markdown)
    )

    assert validate_match_report(report_md) is True


def test_validate_job_e_resume_analysis(job_markdown, resume_markdown):
    assert validate_job_analysis(job_markdown) is True
    assert validate_resume_analysis(resume_markdown) is True


def test_validadores_rejeitam_conteudo_invalido():
    assert validate_match_report("sem score nem listas") is False
    assert validate_job_analysis("texto solto") is False
    assert validate_resume_analysis("texto solto") is False


def test_pdi_from_markdown_devolve_none_para_lixo():
    # Sem score/vaga/objetivo, não dá pra reconstruir um PDI: tem que ser None.
    assert pdi_from_markdown("isto não é um PDI") is None
