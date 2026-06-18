"""Testes da lógica heurística do Scout.

O `run()` do Scout depende de Firecrawl (rede/subprocess), então NÃO o
testamos aqui. Mas a parte que decide aderência, prioridade e lacunas é pura
e determinística — é o miolo que vale proteger. Chamamos os métodos internos
diretamente; em teste isso é legítimo, são unidades de lógica.
"""

import pytest

from agents.scout import ScoutAgent


PROFILE = (
    "Area de interesse: dados\n"
    "Localizacao: remoto\n"
    "Nivel de experiencia: junior\n"
    "Habilidades atuais: Python, SQL\n"
    "Soft skills: Comunicacao\n"
)


@pytest.fixture
def scout():
    return ScoutAgent()


async def _collect(agent: ScoutAgent, context: dict) -> str:
    chunks = []
    async for chunk in agent.run(context):
        chunks.append(chunk)
    return "".join(chunks)


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
    assert entry["source"] == "real"
    assert entry["fallback_reason"] == ""
    assert isinstance(entry["score_aderencia"], int)
    assert entry["prioridade_candidatura"] in {"Alta", "Média", "Baixa"}
    # Python casa (matched), Docker não foi pedido; SQL não está no currículo.
    assert "SQL" in entry["habilidades_faltantes"]


def test_simulate_opportunities_marca_source_simulated(scout):
    jobs = scout._simulate_opportunities(
        {"Area de interesse": "dados", "Localizacao": "remoto"},
        ["Python"],
        ["Comunicacao"],
        "firecrawl_empty",
    )

    assert jobs
    assert {job["source"] for job in jobs} == {"simulated"}
    assert {job["fallback_reason"] for job in jobs} == {"firecrawl_empty"}
    assert all(job["fallback_message"] for job in jobs)


@pytest.mark.asyncio
async def test_run_resultado_real_emite_source_real(monkeypatch, scout):
    async def fake_search(_query: str, _tbs: str = ""):
        return [
            {
                "url": "https://jobs.example.com/vaga-123",
                "title": "Analista de Dados Junior",
                "description": "Vaga com Python e SQL.",
            }
        ], ""

    async def fake_scrape(_url: str):
        return "Vaga real com Python, SQL e comunicacao."

    async def fake_llm(_system: str, _prompt: str):
        return (
            "empresa: Acme\n"
            "localizacao: Remoto\n"
            "salario: Nao informado na descricao\n"
            "beneficios: Nao informado na descricao\n"
            "habilidades_requeridas: Python, SQL\n"
            "soft_skills_requeridas: Comunicacao\n"
            "dica_curriculo: Destaque projetos com dados.\n"
        )

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "_run_firecrawl_scrape", fake_scrape)
    monkeypatch.setattr(scout, "call_llm", fake_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "source: real" in output
    assert "link: https://jobs.example.com/vaga-123" in output
    assert "source: simulated" not in output


@pytest.mark.asyncio
async def test_run_firecrawl_com_erro_emite_fallback_estruturado(monkeypatch, scout):
    async def fake_search(_query: str, _tbs: str = ""):
        return [], "firecrawl_error"

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)

    output = await _collect(scout, {"profile": PROFILE})

    assert "source: simulated" in output
    assert "fallback_reason: firecrawl_error" in output
    assert "fallback_message: Firecrawl falhou" in output


@pytest.mark.asyncio
async def test_run_firecrawl_sem_resultados_emite_fallback_empty(monkeypatch, scout):
    async def fake_search(_query: str, _tbs: str = ""):
        return [], "firecrawl_empty"

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)

    output = await _collect(scout, {"profile": PROFILE})

    assert "source: simulated" in output
    assert "fallback_reason: firecrawl_empty" in output
    assert "fallback_message: Firecrawl nao retornou vagas reais" in output
