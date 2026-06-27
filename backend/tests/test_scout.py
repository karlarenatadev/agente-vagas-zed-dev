"""Testes da lógica heurística do Scout.

O `run()` do Scout depende de Firecrawl (rede/subprocess), então NÃO o
testamos aqui. Mas a parte que decide aderência, prioridade e lacunas é pura
e determinística — é o miolo que vale proteger. Chamamos os métodos internos
diretamente; em teste isso é legítimo, são unidades de lógica.
"""

import asyncio

import pytest

from agents.base import LLMProviderError
from agents.scout import ScoutAgent, ScoutProvenanceError, _SEARCH_CACHE
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
async def test_run_firecrawl_timeout_marca_status_timeout(monkeypatch, scout):
    """Firecrawl excede o tempo limite na busca específica E na ampla, sem
    recuperar vagas reais → status_busca: timeout (Req. 2.5, 8.2).

    Sem créditos/erro envolvidos, o motivo `firecrawl_timeout` propaga até o
    relatório; o LLM falha, então cai na simulação determinística.
    """

    async def fake_search(_query: str, _tbs: str = ""):
        # Tanto a query específica quanto a ampla expiram (timeout) sem reais.
        return [], "firecrawl_timeout", False

    async def failing_llm(_system: str, _prompt: str):
        # LLM indisponivel -> cai no ultimo recurso (simulacao).
        raise LLMProviderError("sem llm", provider_error="Test")

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "call_llm", failing_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "status_busca: timeout" in output
    assert "source: simulated" in output
    assert "fallback_simulado: true" in output
    assert "fallback_reason: firecrawl_timeout" in output
    assert "fallback_message: Nao conseguimos buscar vagas reais dentro do tempo limite" in output
    # timeout sem recuperação real não é degradação (essa exige vagas reais).
    assert "busca_degradada: false" in output


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


# ---------------------------------------------------------------------------
# Guarda de proveniência (_assert_job_provenance) — Requisitos 1.6 e 1.8
# ---------------------------------------------------------------------------


def _real_entry(scout: ScoutAgent) -> dict:
    """Monta uma vaga real válida (source='real', sem campos de fallback)."""
    return scout._build_job_entry(
        title="Analista de Dados",
        company="Acme",
        location="Remoto",
        salary="Não informado na descrição",
        benefits="Não informado na descrição",
        link="https://exemplo.com/vaga",
        required_skills=["Python", "SQL"],
        required_soft=["Comunicação"],
        current_skills=["python"],
        current_soft=["comunicação"],
        level="Júnior",
        area="Dados",
    )


def test_assert_provenance_rejeita_vaga_sem_source_valido(scout):
    """Req. 1.8: vaga sem `source` válido impede a geração do relatório."""
    entry = _real_entry(scout)
    entry["source"] = None  # origem indefinida

    with pytest.raises(ScoutProvenanceError):
        scout._assert_job_provenance([entry])


def test_assert_provenance_rejeita_source_desconhecido(scout):
    """Req. 1.8: um valor de `source` fora do conjunto válido é bloqueado."""
    entry = _real_entry(scout)
    entry["source"] = "scraped"  # não pertence a {real, llm, simulated}

    with pytest.raises(ScoutProvenanceError):
        scout._assert_job_provenance([entry])


def test_assert_provenance_rejeita_entrada_sem_campo_source(scout):
    """Req. 1.8: ausência total do campo `source` também bloqueia o relatório."""
    entry = _real_entry(scout)
    del entry["source"]

    with pytest.raises(ScoutProvenanceError):
        scout._assert_job_provenance([entry])


def test_assert_provenance_aceita_vaga_real_sem_fallback(scout):
    """Req. 1.6: vaga real com campos de fallback vazios passa na guarda."""
    entry = _real_entry(scout)

    assert entry["source"] == "real"
    assert entry["fallback_reason"] == ""
    assert entry["fallback_message"] == ""

    # Não deve levantar: invariante satisfeita.
    scout._assert_job_provenance([entry])


def test_assert_provenance_rejeita_vaga_real_com_fallback_preenchido(scout):
    """Req. 1.6: vaga real NÃO pode carregar campos de fallback preenchidos."""
    entry = _real_entry(scout)
    entry["fallback_reason"] = "firecrawl_error"
    entry["fallback_message"] = "Exibindo oportunidades simuladas."

    with pytest.raises(ScoutProvenanceError):
        scout._assert_job_provenance([entry])


def test_assert_provenance_rejeita_vaga_real_com_apenas_reason(scout):
    """Req. 1.6: basta um dos campos de fallback preenchido para bloquear."""
    entry = _real_entry(scout)
    entry["fallback_reason"] = "firecrawl_timeout"

    with pytest.raises(ScoutProvenanceError):
        scout._assert_job_provenance([entry])


def test_assert_provenance_aceita_lista_real_e_simulada_valida(scout):
    """Combinação válida: vaga real sem fallback + simulada com fallback."""
    real = _real_entry(scout)
    simuladas = scout._simulate_opportunities(
        {"Area de interesse": "dados", "Localizacao": "remoto"},
        ["Python"],
        ["Comunicacao"],
        "firecrawl_empty",
    )

    # Não deve levantar: todas as origens são válidas e coerentes.
    scout._assert_job_provenance([real, *simuladas])


# ---------------------------------------------------------------------------
# Normalização de salário/benefícios e requisitos (Tarefa 3.2)
# Requisitos 9.1 (marcador "Não informado na descrição") e 9.2 (consolidação
# dos requisitos mais recorrentes com contagens).
# ---------------------------------------------------------------------------


def test_simulate_opportunities_marca_salario_beneficios_nao_informado(scout):
    """Req. 9.1/5.1/5.2: vagas simuladas marcam salário e benefícios ausentes."""
    jobs = scout._simulate_opportunities(
        {"Area de interesse": "dados", "Localizacao": "remoto"},
        ["Python"],
        ["Comunicacao"],
        "firecrawl_empty",
    )

    assert jobs
    assert {job["salario"] for job in jobs} == {"Não informado na descrição"}
    assert {job["beneficios"] for job in jobs} == {"Não informado na descrição"}


@pytest.mark.asyncio
async def test_run_vaga_real_sem_salario_e_beneficios_usa_marcador(monkeypatch, scout):
    """Req. 9.1: no caminho real, salário/benefícios ausentes na extração do LLM
    são preenchidos com o marcador "Não informado na descrição"."""

    async def fake_search(_query: str, _tbs: str = ""):
        return [
            {
                "url": "https://jobs.example.com/vaga-1",
                "title": "Analista de Dados",
                "description": "Vaga com Python e SQL.",
            }
        ], "", False

    async def fake_scrape(_url: str):
        return "Descricao da vaga real com Python e SQL."

    async def fake_llm(_system: str, _prompt: str):
        # Extração SEM salário e SEM benefícios (linhas vazias).
        return (
            "empresa: Acme\n"
            "localizacao: Remoto\n"
            "salario: \n"
            "beneficios: \n"
            "habilidades_requeridas: Python, SQL\n"
            "soft_skills_requeridas: Comunicacao\n"
            "dica_curriculo: Destaque dados.\n"
        )

    monkeypatch.setattr(scout, "_run_firecrawl_search", fake_search)
    monkeypatch.setattr(scout, "_run_firecrawl_scrape", fake_scrape)
    monkeypatch.setattr(scout, "call_llm", fake_llm)

    output = await _collect(scout, {"profile": PROFILE})

    assert "source: real" in output
    assert "salario: Não informado na descrição" in output
    assert "beneficios: Não informado na descrição" in output


def test_recurring_requirements_consolida_com_contagens(scout):
    """Req. 9.2/5.6: requisitos mais recorrentes vêm com a contagem de ocorrências."""
    jobs = [
        {"_required_skills": ["Python", "SQL", "Docker"]},
        {"_required_skills": ["Python", "SQL"]},
        {"_required_skills": ["Python"]},
    ]

    recurring = scout._recurring_requirements(jobs)
    counts = dict(recurring)

    assert counts["Python"] == 3
    assert counts["SQL"] == 2
    assert counts["Docker"] == 1
    # Ordenado do mais recorrente para o menos recorrente.
    assert recurring[0] == ("Python", 3)
    # Cada item é uma tupla (requisito, contagem).
    assert all(isinstance(skill, str) and isinstance(count, int) for skill, count in recurring)


def test_recurring_requirements_consolida_case_insensitive(scout):
    """Variações de caixa do mesmo requisito são contadas como um só."""
    jobs = [
        {"_required_skills": ["Python", "python"]},
        {"_required_skills": ["PYTHON"]},
    ]

    recurring = scout._recurring_requirements(jobs)

    assert len(recurring) == 1
    skill, count = recurring[0]
    assert count == 3
    assert skill.lower() == "python"


def test_recurring_requirements_vazio_quando_sem_requisitos(scout):
    """Sem requisitos, a consolidação retorna lista vazia."""
    assert scout._recurring_requirements([]) == []
    assert scout._recurring_requirements([{"_required_skills": []}]) == []


def test_recurring_requirements_limita_aos_seis_mais_recorrentes(scout):
    """A consolidação retorna no máximo os 6 requisitos mais recorrentes."""
    jobs = [
        {"_required_skills": [f"Skill{i}" for i in range(10)]},
        {"_required_skills": [f"Skill{i}" for i in range(10)]},
    ]

    recurring = scout._recurring_requirements(jobs)

    assert len(recurring) == 6


def test_score_aderencia_clamp_entre_0_e_100(scout):
    """Req. 5.5: o score de aderência é sempre um inteiro em [0, 100]."""
    cenarios = [
        # (matched_tech, required_tech, matched_soft, required_soft, level, title)
        ([], [], [], [], "", ""),  # sem requisitos (limite inferior)
        (["Python", "SQL"], ["Python", "SQL"], ["Comunicação"], ["Comunicação"], "Júnior", "Analista Júnior"),  # tudo bate (limite superior)
        (["A", "B", "C", "D"], ["A", "B"], ["X", "Y"], ["X"], "Sênior", "Sênior"),  # mais matches que requisitos (não estoura 100)
    ]

    for matched_tech, required_tech, matched_soft, required_soft, level, title in cenarios:
        score = scout._score_opportunity(
            matched_tech, required_tech, matched_soft, required_soft, level, title
        )
        assert isinstance(score, int)
        assert 0 <= score <= 100


def test_build_job_entry_score_aderencia_e_inteiro_no_intervalo(scout):
    """Req. 5.5: o score embutido no job_entry respeita o intervalo [0, 100]."""
    entry = scout._build_job_entry(
        title="Analista",
        company="Acme",
        location="Remoto",
        salary="Não informado na descrição",
        benefits="Não informado na descrição",
        link="https://exemplo.com/vaga",
        required_skills=["Python", "SQL", "Docker", "AWS"],
        required_soft=["Comunicação"],
        current_skills=["python", "sql", "docker", "aws"],
        current_soft=["comunicação"],
        level="Júnior",
        area="Dados",
    )

    score = entry["score_aderencia"]
    assert isinstance(score, int)
    assert 0 <= score <= 100


def test_build_job_entry_marca_nenhuma_para_listas_vazias(scout):
    """Req. 5.4: sem requisitos, correspondentes e faltantes viram "Nenhuma"."""
    entry = scout._build_job_entry(
        title="Analista",
        company="Acme",
        location="Remoto",
        salary="Não informado na descrição",
        benefits="Não informado na descrição",
        link="https://exemplo.com/vaga",
        required_skills=[],
        required_soft=[],
        current_skills=[],
        current_soft=[],
        level="",
        area="Dados",
    )

    assert entry["habilidades_correspondentes"] == "Nenhuma"
    assert entry["habilidades_faltantes"] == "Nenhuma"
    assert entry["soft_skills_correspondentes"] == "Nenhuma"


def test_build_job_entry_faltantes_nenhuma_quando_tudo_corresponde(scout):
    """Req. 5.4: quando todas as habilidades batem, faltantes vira "Nenhuma"."""
    entry = scout._build_job_entry(
        title="Analista",
        company="Acme",
        location="Remoto",
        salary="Não informado na descrição",
        benefits="Não informado na descrição",
        link="https://exemplo.com/vaga",
        required_skills=["Python", "SQL"],
        required_soft=["Comunicação"],
        current_skills=["python", "sql"],
        current_soft=["comunicação"],
        level="Júnior",
        area="Dados",
    )

    assert entry["habilidades_faltantes"] == "Nenhuma"
    assert "Python" in entry["habilidades_correspondentes"]
    assert "SQL" in entry["habilidades_correspondentes"]
