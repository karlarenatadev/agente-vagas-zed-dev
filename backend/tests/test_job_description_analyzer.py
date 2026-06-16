"""Testes da análise heurística de descrição de vaga.

Este é o tipo mais fácil de teste: a função `analyze()` é pura — recebe um
texto e devolve um dicionário, sem rede, sem arquivo, sem LLM. Mesmo texto
sempre gera o mesmo resultado, então dá pra afirmar com certeza o que esperar.
"""

from agents.job_description_analyzer import (
    JobDescriptionAnalyzer,
    analysis_from_markdown,
    analysis_to_markdown,
)
from agents.resume_matcher import validate_job_analysis


# Uma descrição de vaga realista que usamos em vários testes.
VAGA_EXEMPLO = """
Analista de Dados Júnior
Empresa Acme Tech

Responsabilidades:
- Desenvolver dashboards no Power BI
- Analisar indicadores e KPIs
- Criar pipelines de ETL

Requisitos:
- Experiência com Python e SQL
- Conhecimento de Excel
- Boa comunicação e trabalho em equipe

Diferenciais:
- Conhecimento de AWS
"""


def test_analyze_extrai_hard_skills_e_ferramentas():
    # Arrange: o analyzer não tem estado, pode instanciar à vontade.
    analyzer = JobDescriptionAnalyzer()

    # Act: roda a análise.
    resultado = analyzer.analyze(VAGA_EXEMPLO)

    # Assert: o texto cita Python, SQL, Power BI e Excel — têm que aparecer.
    assert "Python" in resultado["hard_skills"]
    assert "SQL" in resultado["hard_skills"]
    assert "Power BI" in resultado["tools"]
    assert "Excel" in resultado["tools"]


def test_analyze_extrai_soft_skills():
    resultado = JobDescriptionAnalyzer().analyze(VAGA_EXEMPLO)

    assert "Comunicação" in resultado["soft_skills"]
    assert "Trabalho em equipe" in resultado["soft_skills"]


def test_analyze_sempre_retorna_as_chaves_esperadas():
    # Garante o "contrato" do dicionário: a rota e o frontend dependem
    # destas chaves existirem sempre, mesmo com texto pobre.
    resultado = JobDescriptionAnalyzer().analyze("vaga qualquer sem detalhes")

    for chave in (
        "title", "company", "seniority", "modality", "location",
        "keywords", "hard_skills", "soft_skills", "tools",
        "responsibilities", "required_requirements", "nice_to_have",
        "alerts", "next_steps",
    ):
        assert chave in resultado


def test_markdown_roundtrip_preserva_skills():
    # Round-trip: dict -> markdown -> dict. O que sai tem que voltar igual
    # no que importa. Isso protege a serialização que grava em data/.
    original = JobDescriptionAnalyzer().analyze(VAGA_EXEMPLO)

    markdown = analysis_to_markdown(original)
    recuperado = analysis_from_markdown(markdown)

    assert recuperado is not None
    assert set(recuperado["hard_skills"]) == set(original["hard_skills"])
    assert set(recuperado["tools"]) == set(original["tools"])


def test_analysis_from_markdown_devolve_none_para_lixo():
    # Texto que não é uma análise válida tem que virar None,
    # não estourar exceção.
    assert analysis_from_markdown("isto não é uma análise") is None


def test_validate_job_analysis():
    markdown = analysis_to_markdown(JobDescriptionAnalyzer().analyze(VAGA_EXEMPLO))
    assert validate_job_analysis(markdown) is True
    assert validate_job_analysis("texto vazio sem skills") is False
