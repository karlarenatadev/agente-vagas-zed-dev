"""Testes dos validadores de pré-requisito das sugestões de currículo (tailor).

Mesmo padrão do PDI: o tailor checa as entradas antes de sugerir, e
alimentamos `validate_match_report` com o relatório real do matcher.
"""

from agents.resume_matcher import ResumeMatcher, match_report_to_markdown
from agents.resume_tailor import (
    tailoring_from_markdown,
    validate_job_analysis,
    validate_match_report,
    validate_resume_analysis,
)


def _match_report_with_score(score: str) -> str:
    return f"""# Relatorio de aderencia entre vaga e curriculo

## Resumo

* Score geral: {score}
* Nivel de prontidao: parcialmente aderente
* Vaga analisada: Analista de Dados
* Curriculo analisado: Curriculo analisado

## Evidencias fortes no curriculo

* Python
"""


def _match_report_without_score() -> str:
    return """# Relatorio de aderencia entre vaga e curriculo

## Resumo

* Nivel de prontidao: parcialmente aderente
* Vaga analisada: Analista de Dados
* Curriculo analisado: Curriculo analisado

## Evidencias fortes no curriculo

* Python
"""


def test_validate_match_report_aceita_relatorio_real(job_markdown, resume_markdown):
    report_md = match_report_to_markdown(
        ResumeMatcher().match(job_markdown, resume_markdown)
    )

    assert validate_match_report(report_md) is True


def test_validate_job_e_resume_analysis(job_markdown, resume_markdown):
    assert validate_job_analysis(job_markdown) is True
    assert validate_resume_analysis(resume_markdown) is True


def test_validadores_rejeitam_conteudo_invalido():
    assert validate_match_report("sem score") is False
    assert validate_job_analysis("texto solto") is False
    assert validate_resume_analysis("texto solto") is False


def test_validate_match_report_rejeita_score_fora_do_intervalo():
    assert validate_match_report(_match_report_with_score("-1/100")) is False
    assert validate_match_report(_match_report_with_score("101/100")) is False
    assert validate_match_report(_match_report_with_score("999/100")) is False
    assert validate_match_report(_match_report_with_score("alto/100")) is False
    assert validate_match_report(_match_report_without_score()) is False


def test_validate_match_report_aceita_score_nos_limites():
    assert validate_match_report(_match_report_with_score("0/100")) is True
    assert validate_match_report(_match_report_with_score("1/100")) is True
    assert validate_match_report(_match_report_with_score("50/100")) is True
    assert validate_match_report(_match_report_with_score("100/100")) is True


def test_tailoring_from_markdown_devolve_none_para_lixo():
    assert tailoring_from_markdown("isto não é uma sugestão") is None
