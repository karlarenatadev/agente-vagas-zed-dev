"""Fixtures compartilhadas pelos testes.

O pytest carrega `conftest.py` automaticamente e injeta qualquer fixture daqui
em qualquer teste que peça pelo nome no parâmetro. Útil pra não repetir os
mesmos dados de exemplo em vários arquivos.
"""

import pytest

import config
from agents.job_description_analyzer import (
    JobDescriptionAnalyzer,
    analysis_to_markdown,
)
from agents.resume_matcher import ResumeMatcher, match_report_to_markdown


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch):
    """Garante uma chave qualquer pro cliente OpenAI ser instanciável.

    Scout e Curator herdam de BaseAgent, que cria um AsyncOpenAI no __init__.
    Sem uma chave, isso estoura — mesmo que o teste nunca chame o LLM.
    `autouse=True` aplica esta fixture a TODOS os testes automaticamente.
    """
    if not config.OPENAI_API_KEY:
        monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key-não-usada")


@pytest.fixture
def job_markdown() -> str:
    """Markdown de análise de vaga, no formato que os agentes leem de data/."""
    descricao = (
        "Analista de Dados Júnior na Acme. "
        "Responsabilidades: desenvolver dashboards no Power BI, analisar KPIs. "
        "Requisitos: experiência com Python e SQL, conhecimento de Excel. "
        "Boa comunicação e trabalho em equipe."
    )
    return analysis_to_markdown(JobDescriptionAnalyzer().analyze(descricao))


@pytest.fixture
def resume_markdown() -> str:
    """Markdown de análise de currículo, no formato esperado por _parse_markdown."""
    return (
        "# Análise de currículo\n\n"
        "## Habilidades técnicas detectadas\n"
        "- Python\n"
        "- SQL\n\n"
        "## Soft skills detectadas\n"
        "- Comunicação\n"
        "- Trabalho em equipe\n"
    )


@pytest.fixture
def match_markdown(job_markdown: str, resume_markdown: str) -> str:
    """Markdown de relatório de aderência, no formato real do `resume-match-report.md`."""
    report = ResumeMatcher().match(job_markdown, resume_markdown)
    return match_report_to_markdown(report)
