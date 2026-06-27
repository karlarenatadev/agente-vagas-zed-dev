"""Testes da lógica heurística do Curator.

Como no Scout, o `run()` usa Firecrawl e fica de fora. Aqui testamos as funções
puras que classificam um recurso de aprendizado: de qual plataforma é a URL, se
é pago ou gratuito, qual o nível e a duração.
"""

import pytest

from agents.curator import CuratorAgent
from firecrawl_client import FirecrawlProviderError


@pytest.fixture
def curator():
    return CuratorAgent()


async def _collect(agent: CuratorAgent, context: dict) -> str:
    """Consome o gerador assíncrono do agente e devolve o relatório completo."""
    chunks: list[str] = []
    async for chunk in agent.run(context):
        chunks.append(chunk)
    return "".join(chunks)


def test_platform_for_url_reconhece_plataformas_conhecidas(curator):
    assert curator._platform_for_url("https://www.youtube.com/watch?v=x") == "YouTube"
    assert curator._platform_for_url("https://www.udemy.com/curso") == "Udemy"
    assert curator._platform_for_url("https://www.coursera.org/learn/py") == "Coursera"


def test_platform_for_url_desconhecida_devolve_host(curator):
    assert curator._platform_for_url("https://siteobscuro.xyz/curso") == "siteobscuro.xyz"


def test_price_for_platform(curator):
    assert curator._price_for_platform("YouTube", "", "") == "gratuito"
    assert curator._price_for_platform("Udemy", "", "") == "acessivel"
    assert curator._price_for_platform("Alura", "", "") == "premium"


def test_price_detecta_gratuito_no_texto(curator):
    # Plataforma neutra, mas o texto indica que é gratuito.
    assert curator._price_for_platform("Outra", "Free SQL course", "") == "gratuito"
    # Acento não atrapalha: "grátis" é normalizado para "gratis".
    assert curator._price_for_platform("Outra", "Curso grátis de SQL", "") == "gratuito"


def test_classify_level(curator):
    assert curator._classify_level("Curso avançado de Python", "", "iniciante") == "avancado"
    assert curator._classify_level("Projeto prático de ETL", "", "iniciante") == "intermediario"
    assert curator._classify_level("Fundamentos de SQL", "", "intermediario") == "iniciante"
    # Sem pistas no texto: mantém o nível default informado.
    assert curator._classify_level("Curso de SQL", "", "intermediario") == "intermediario"


def test_extract_duration(curator):
    # Agora a palavra completa é preservada: "10 horas", "30 minutos".
    assert curator._extract_duration("Curso de 10 horas", "") == "10 horas"
    assert curator._extract_duration("Workshop de 30 minutos", "") == "30 minutos"
    assert curator._extract_duration("Aula de 2h", "") == "2 h"
    assert curator._extract_duration("Curso de SQL", "sem informação") == "Nao informado"


# ---------------------------------------------------------------------------
# Origem dos recursos: busca real vs. recomendação interna (Requirements 9.3)
# ---------------------------------------------------------------------------


def test_build_resource_marca_origem_real(curator):
    """Recurso construído a partir de um resultado de busca é marcado como 'real'."""
    item = {
        "url": "https://www.youtube.com/watch?v=abc",
        "title": "Curso de Python de 10 horas",
        "description": "Curso gratuito iniciante",
    }
    resource = curator._build_resource(item, "Python", recurrence=2, query_type="gratuito", default_level="iniciante")
    assert resource.origin == "real"


def test_internal_resources_marca_origem_interna(curator):
    """Todos os recursos vindos da base INTERNAL_RECOMMENDATIONS são 'interna'."""
    internos = curator._internal_resources_for_skill("Python", recurrence=1)
    assert internos, "esperava recursos internos para 'python'"
    assert all(resource.origin == "interna" for resource in internos)


def test_origem_real_e_interna_sao_distinguiveis(curator):
    """A origem permite separar curso de busca real de recomendação interna."""
    item = {
        "url": "https://www.udemy.com/course/python",
        "title": "Python aplicado",
        "description": "projeto prático",
    }
    real = curator._build_resource(item, "Python", recurrence=1, query_type="acessivel", default_level="iniciante")
    internos = curator._internal_resources_for_skill("Python", recurrence=1)

    assert real.origin == "real"
    assert {resource.origin for resource in internos} == {"interna"}
    assert real.origin not in {resource.origin for resource in internos}


# ---------------------------------------------------------------------------
# Normalização completa de um recurso (plataforma, nível, preço, duração)
# ---------------------------------------------------------------------------


def test_build_resource_normaliza_todos_os_atributos(curator):
    """plataforma derivada do domínio, nível classificado, preço e duração normalizados."""
    item = {
        "url": "https://www.youtube.com/watch?v=abc",
        "title": "Fundamentos de Python em 10 horas",
        "description": "curso gratuito",
    }
    resource = curator._build_resource(item, "Python", recurrence=1, query_type="gratuito", default_level="intermediario")

    assert resource.platform == "YouTube"
    assert resource.price == "gratuito"
    assert resource.level == "iniciante"  # "Fundamentos" indica nível iniciante
    assert resource.duration == "10 horas"


def test_build_resource_duracao_ausente_marca_nao_informado(curator):
    """Quando não há duração no título/descrição, o campo recebe 'Nao informado'."""
    item = {
        "url": "https://www.udemy.com/course/sql",
        "title": "Curso de SQL",
        "description": "sem informação de carga horária",
    }
    resource = curator._build_resource(item, "SQL", recurrence=1, query_type="acessivel", default_level="iniciante")

    assert resource.platform == "Udemy"
    assert resource.price == "acessivel"
    assert resource.duration == "Nao informado"


# ---------------------------------------------------------------------------
# Distinção de origem no relatório emitido por run() (Requirements 3.4 / 9.3)
# ---------------------------------------------------------------------------

JOB_RESULTS = "## RESPOSTA: SCOUT\nhabilidades_faltantes: Python\n"


@pytest.mark.asyncio
async def test_relatorio_sinaliza_recomendacao_interna_quando_busca_externa_falha(monkeypatch, curator):
    """Busca externa indisponível -> trilha complementada pela base interna e sinalizada nos avisos."""

    async def failing_search(*_args, **_kwargs):
        raise FirecrawlProviderError("falha externa")

    monkeypatch.setattr("agents.curator.firecrawl_search", failing_search)

    output = await _collect(curator, {"profile": "", "job_results": JOB_RESULTS})

    assert "### avisos" in output
    assert "base interna" in output.casefold()


@pytest.mark.asyncio
async def test_relatorio_de_busca_real_nao_sinaliza_base_interna(monkeypatch, curator):
    """Busca externa com material suficiente -> sem aviso de base interna no relatório."""

    async def real_search(*_args, **_kwargs):
        return [
            {
                "url": "https://www.freecodecamp.org/learn/python",
                "title": "Python for Everybody tutorial",
                "description": "curso gratuito iniciante",
            }
        ]

    monkeypatch.setattr("agents.curator.firecrawl_search", real_search)

    output = await _collect(curator, {"profile": "", "job_results": JOB_RESULTS})

    assert "### estado\nsucesso" in output
    assert "base interna" not in output.casefold()
    assert "### avisos" not in output
