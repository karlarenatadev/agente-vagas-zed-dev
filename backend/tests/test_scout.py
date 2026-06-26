"""Testes da lógica heurística do Scout.

O `run()` do Scout depende de Firecrawl (rede/subprocess), então NÃO o
testamos aqui. Mas a parte que decide aderência, prioridade e lacunas é pura
e determinística — é o miolo que vale proteger. Chamamos os métodos internos
diretamente; em teste isso é legítimo, são unidades de lógica.
"""

import asyncio

import pytest

from agents.base import LLMProviderError
from agents.scout import ScoutAgent, _SEARCH_CACHE
from firecrawl_client import FirecrawlProviderError


PROFILE = (
    "Area de interesse: dados\n"
    "Localizacao: remoto\n"
    "Nivel de experiencia: junior\n"
    "Habilidades atuais: Python, SQL\n"
    "Soft skills: Comunicacao\n"
)


@pytest.fixture
def scout():
    _SEARCH_CACHE.clear()
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
async def test_firecrawl_search_rapido_respeita_limite_configurado(monkeypatch, scout):
    async def fake_firecrawl_search(*_args, **_kwargs):
        return [
            {"url": "https://jobs.example.com/1", "title": "Vaga 1", "description": ""},
            {"url": "https://jobs.example.com/2", "title": "Vaga 2", "description": ""},
        ]

    monkeypatch.setenv("FIRECRAWL_TIMEOUT_SECONDS", "1")
    monkeypatch.setenv("FIRECRAWL_MAX_RESULTS", "1")
    monkeypatch.setattr("agents.scout.firecrawl_search", fake_firecrawl_search)

    results, reason, cache_hit = await scout._run_firecrawl_search("vagas dados remoto")

    assert len(results) == 1
    assert reason == ""
    assert cache_hit is False


@pytest.mark.asyncio
async def test_firecrawl_search_timeout_retorna_reason_sem_sucesso(monkeypatch, scout):
    async def slow_firecrawl_search(*_args, **_kwargs):
        await asyncio.sleep(0.05)
        return [{"url": "https://jobs.example.com/1", "title": "Vaga 1", "description": ""}]

    monkeypatch.setenv("FIRECRAWL_TIMEOUT_SECONDS", "0.01")
    monkeypatch.setattr("agents.scout.firecrawl_search", slow_firecrawl_search)

    results, reason, cache_hit = await scout._run_firecrawl_search("vagas dados remoto")

    assert results == []
    assert reason == "firecrawl_timeout"
    assert cache_hit is False


@pytest.mark.asyncio
async def test_firecrawl_search_zero_resultados_retorna_empty(monkeypatch, scout):
    async def empty_firecrawl_search(*_args, **_kwargs):
        return []

    monkeypatch.setattr("agents.scout.firecrawl_search", empty_firecrawl_search)

    results, reason, cache_hit = await scout._run_firecrawl_search("vagas dados remoto")

    assert results == []
    assert reason == "firecrawl_empty"
    assert cache_hit is False


@pytest.mark.asyncio
async def test_firecrawl_search_erro_externo_retorna_error(monkeypatch, scout):
    async def failing_firecrawl_search(*_args, **_kwargs):
        raise FirecrawlProviderError("falha")

    monkeypatch.setattr("agents.scout.firecrawl_search", failing_firecrawl_search)

    results, reason, cache_hit = await scout._run_firecrawl_search("vagas dados remoto")

    assert results == []
    assert reason == "firecrawl_error"
    assert cache_hit is False


@pytest.mark.asyncio
async def test_firecrawl_search_reusa_cache_por_consulta(monkeypatch, scout):
    calls = 0

    async def fake_firecrawl_search(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return [{"url": "https://jobs.example.com/1", "title": "Vaga 1", "description": ""}]

    monkeypatch.setenv("FIRECRAWL_CACHE_TTL_SECONDS", "60")
    monkeypatch.setattr("agents.scout.firecrawl_search", fake_firecrawl_search)

    first_results, first_reason, first_cache_hit = await scout._run_firecrawl_search("vagas dados remoto")
    second_results, second_reason, second_cache_hit = await scout._run_firecrawl_search(" vagas   dados remoto ")

    assert first_results == second_results
    assert first_reason == second_reason == ""
    assert first_cache_hit is False
    assert second_cache_hit is True
    assert calls == 1


@pytest.mark.asyncio
async def test_run_resultado_real_emite_source_real(monkeypatch, scout):
    async def fake_search(_query: str, _tbs: str = ""):
        return [
            {
                "url": "https://jobs.example.com/vaga-123",
                "title": "Analista de Dados Junior",
                "description": "Vaga com Python e SQL.",
            }
        ], "", False

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
    assert "status_busca: real_success" in output
    assert "fallback_simulado: false" in output
    assert "link: https://jobs.example.com/vaga-123" in output
    assert "source: simulated" not in output


@pytest.mark.asyncio
async def test_run_firecrawl_com_erro_emite_fallback_estruturado(monkeypatch, scout):
    async def fake_search(_query: str, _tbs: str = ""):
        return [], "firecrawl_error", False

    async def failing_llm(_system: str, _prompt: str):
        # LLM indisponivel -> cai no ultimo recurso (simulacao).
        raise LLMProviderError("sem llm", provider_error="Test")

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "call_llm", failing_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "source: simulated" in output
    assert "fallback_simulado: true" in output
    assert "fallback_llm: false" in output
    assert "status_busca: external_error" in output
    assert "fallback_reason: firecrawl_error" in output
    assert "fallback_message: Nao conseguimos buscar vagas reais agora" in output


@pytest.mark.asyncio
async def test_run_firecrawl_sem_resultados_emite_fallback_empty(monkeypatch, scout):
    async def fake_search(_query: str, _tbs: str = ""):
        return [], "firecrawl_empty", False

    async def failing_llm(_system: str, _prompt: str):
        raise LLMProviderError("sem llm", provider_error="Test")

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "call_llm", failing_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "source: simulated" in output
    assert "fallback_simulado: true" in output
    assert "status_busca: real_empty" in output
    assert "fallback_reason: firecrawl_empty" in output
    assert "fallback_message: Nenhuma vaga real encontrada" in output


@pytest.mark.asyncio
async def test_run_usa_llm_fallback_quando_firecrawl_vazio(monkeypatch, scout):
    """Firecrawl vazio + LLM disponivel -> vagas com source 'llm', sem simulacao."""

    async def fake_search(_query: str, _tbs: str = ""):
        return [], "firecrawl_empty", False

    async def fake_llm(_system: str, _prompt: str):
        return (
            "titulo: Engenheiro de Dados Junior\n"
            "empresa: DataCorp\n"
            "localizacao: Remoto\n"
            "salario: R$ 4.000 - R$ 6.000\n"
            "beneficios: VR, plano de saude\n"
            "habilidades_requeridas: Python, SQL, ETL\n"
            "soft_skills_requeridas: Comunicacao, Colaboracao\n"
            "dica_curriculo: Destaque projetos com Python e SQL.\n"
            "---\n"
            "titulo: Analista de Dados\n"
            "empresa: Insights Co\n"
            "localizacao: Remoto\n"
            "salario: Nao informado\n"
            "beneficios: Nao informado\n"
            "habilidades_requeridas: SQL, Power BI\n"
            "soft_skills_requeridas: Organizacao\n"
            "dica_curriculo: Mostre dashboards de dados.\n"
        )

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "call_llm", fake_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "fallback_llm: true" in output
    assert "fallback_simulado: false" in output
    assert "source: llm" in output
    assert "source: simulated" not in output
    assert "Sugestoes geradas por IA" in output


@pytest.mark.asyncio
async def test_run_sem_creditos_marca_status_no_credits(monkeypatch, scout):
    """Firecrawl sem creditos: status no_credits; LLM falha -> simulacao."""

    async def fake_search(_query: str, _tbs: str = ""):
        return [], "firecrawl_no_credits", False

    async def failing_llm(_system: str, _prompt: str):
        raise LLMProviderError("sem llm", provider_error="Test")

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "call_llm", failing_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "status_busca: no_credits" in output
    assert "fallback_reason: firecrawl_no_credits" in output
    assert "fallback_simulado: true" in output
    assert "source: simulated" in output


@pytest.mark.asyncio
async def test_run_sem_creditos_usa_llm_quando_disponivel(monkeypatch, scout):
    """Firecrawl sem creditos + LLM disponivel -> vagas do LLM, status no_credits."""

    async def fake_search(_query: str, _tbs: str = ""):
        return [], "firecrawl_no_credits", False

    async def fake_llm(_system: str, _prompt: str):
        return (
            "titulo: Pessoa Desenvolvedora Backend\n"
            "empresa: Acme\n"
            "localizacao: Remoto\n"
            "salario: R$ 9.000\n"
            "beneficios: VR\n"
            "habilidades_requeridas: Python, SQL\n"
            "soft_skills_requeridas: Comunicacao\n"
            "dica_curriculo: Mostre APIs REST.\n"
        )

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "call_llm", fake_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "status_busca: no_credits" in output
    assert "fallback_llm: true" in output
    assert "fallback_simulado: false" in output
    assert "source: llm" in output


def test_split_llm_blocks_com_e_sem_separador(scout):
    com_sep = "titulo: A\nempresa: X\n---\ntitulo: B\nempresa: Y"
    assert len(scout._split_llm_blocks(com_sep)) == 2

    sem_sep = "titulo: A\nempresa: X\ntitulo: B\nempresa: Y"
    assert len(scout._split_llm_blocks(sem_sep)) == 2

    assert scout._split_llm_blocks("") == []
    assert scout._split_llm_blocks("texto sem nenhuma vaga aqui") == []


@pytest.mark.asyncio
async def test_llm_opportunities_parseia_blocos_e_marca_source_llm(monkeypatch, scout):
    async def fake_llm(_system: str, _prompt: str):
        return (
            "titulo: Dev Python Pleno\n"
            "empresa: Acme\n"
            "localizacao: Remoto\n"
            "salario: R$ 8.000\n"
            "beneficios: VR\n"
            "habilidades_requeridas: Python, SQL\n"
            "soft_skills_requeridas: Comunicacao\n"
            "dica_curriculo: Mostre APIs.\n"
        )

    monkeypatch.setattr(scout, "call_llm", fake_llm)

    jobs = await scout._llm_opportunities(
        {"Funcoes alvo": ""},
        ["Python"],
        ["Comunicacao"],
        "backend",
        "Remoto",
        "Pleno",
        "firecrawl_empty",
    )

    assert len(jobs) == 1
    assert jobs[0]["source"] == "llm"
    assert jobs[0]["titulo"] == "Dev Python Pleno"
    assert jobs[0]["fallback_message"]
    assert isinstance(jobs[0]["score_aderencia"], int)
    # O link nunca pode ser uma URL (evita link alucinado apresentado como real).
    assert "http" not in str(jobs[0]["link"]).lower()


@pytest.mark.asyncio
async def test_llm_opportunities_retorna_vazio_quando_llm_falha(monkeypatch, scout):
    async def failing_llm(_system: str, _prompt: str):
        raise LLMProviderError("indisponivel", provider_error="Test")

    monkeypatch.setattr(scout, "call_llm", failing_llm)

    jobs = await scout._llm_opportunities(
        {}, [], [], "backend", "Remoto", "", "firecrawl_empty"
    )

    assert jobs == []


@pytest.mark.asyncio
async def test_run_sinaliza_busca_degradada_quando_query_especifica_falha(scout, monkeypatch):
    """Busca específica falha (erro) e só a ampla recupera vagas REAIS.

    Antes esse caso virava 'real_success' silenciosamente; agora o Scout expõe
    busca_degradada/aviso_degradacao sem cair em modo simulado.
    """
    chamadas = {"n": 0}

    async def fake_search(query, tbs=""):
        chamadas["n"] += 1
        if chamadas["n"] == 1:
            # 1ª query (específica, com nível): erro no Firecrawl.
            return [], "firecrawl_error", False
        # 2ª query (ampla): recupera uma vaga real.
        return (
            [{"url": "https://exemplo.com/vaga", "titulo": "Analista de Dados", "descricao": "Python e SQL"}],
            "",
            False,
        )

    async def fake_scrape(url):
        return ""

    async def fake_llm(system_prompt, user_prompt):
        return ""

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "_run_firecrawl_scrape", fake_scrape)
    monkeypatch.setattr(scout, "call_llm", fake_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "status_busca: real_degraded" in output
    assert "busca_degradada: true" in output
    # Não é simulação: as vagas são reais.
    assert "fallback_simulado: false" in output
    assert "source: real" in output
    # O aviso de degradação não fica vazio.
    assert "aviso_degradacao: A busca" in output


@pytest.mark.asyncio
async def test_run_sucesso_limpo_nao_marca_degradada(scout, monkeypatch):
    """1ª query já retorna vagas reais → sem degradação e sem simulação."""

    async def fake_search(query, tbs=""):
        return (
            [{"url": "https://exemplo.com/vaga", "titulo": "Analista", "descricao": "Python"}],
            "",
            False,
        )

    async def fake_scrape(url):
        return ""

    async def fake_llm(system_prompt, user_prompt):
        return ""

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "_run_firecrawl_scrape", fake_scrape)
    monkeypatch.setattr(scout, "call_llm", fake_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "status_busca: real_success" in output
    assert "busca_degradada: false" in output
    assert "fallback_simulado: false" in output
