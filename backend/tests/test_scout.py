"""Testes da lógica heurística do Scout.

O `run()` do Scout depende de Firecrawl (rede/subprocess), então NÃO o
testamos aqui. Mas a parte que decide aderência, prioridade e lacunas é pura
e determinística — é o miolo que vale proteger. Chamamos os métodos internos
diretamente; em teste isso é legítimo, são unidades de lógica.
"""

import pytest

from agents.scout import ScoutAgent


@pytest.fixture
def scout():
    return ScoutAgent()


def test_match_skills_e_case_insensitive_e_separa_faltantes(scout):
    matched, missing = scout._match_skills(
        required=["Python", "SQL", "Docker"],
        current=["python", "sql básico"],
    )

    assert "Python" in matched
    assert "SQL" in matched          # casa "sql" dentro de "sql básico"
    assert "Docker" in missing


def test_priority_from_score():
    scout = ScoutAgent()
    assert scout._priority_from_score(80) == "Alta"
    assert scout._priority_from_score(60) == "Média"
    assert scout._priority_from_score(30) == "Baixa"


def test_score_opportunity_nunca_passa_de_100(scout):
    # Todas as skills batem e o nível aparece no título: score alto, mas <= 100.
    score = scout._score_opportunity(
        matched_tech=["Python", "SQL"],
        required_tech=["Python", "SQL"],
        matched_soft=["Comunicação"],
        required_soft=["Comunicação"],
        level="Júnior",
        title="Analista Júnior",
    )

    assert 0 <= score <= 100
    assert score >= 75  # match total tem que dar prioridade alta


def test_area_skills_usa_default_para_area_desconhecida(scout):
    skills = scout._area_skills("área que não existe no mapa")

    assert isinstance(skills, list)
    assert "Git" in skills  # default conhecido do código


def test_build_job_entry_monta_o_dict_esperado(scout):
    entry = scout._build_job_entry(
        title="Analista de Dados",
        company="Acme",
        location="Remoto",
        salary="Não informado",
        benefits="Não informado",
        link="https://exemplo.com/vaga",
        required_skills=["Python", "SQL"],
        required_soft=["Comunicação"],
        current_skills=["python"],
        current_soft=["comunicação"],
        level="Júnior",
        area="Dados",
    )

    assert entry["titulo"] == "Analista de Dados"
    assert isinstance(entry["score_aderencia"], int)
    assert entry["prioridade_candidatura"] in {"Alta", "Média", "Baixa"}
    # Python casa (matched), Docker não foi pedido; SQL não está no currículo.
    assert "SQL" in entry["habilidades_faltantes"]
