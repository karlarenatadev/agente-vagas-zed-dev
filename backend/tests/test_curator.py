"""Testes da lógica heurística do Curator.

Como no Scout, o `run()` usa Firecrawl e fica de fora. Aqui testamos as funções
puras que classificam um recurso de aprendizado: de qual plataforma é a URL, se
é pago ou gratuito, qual o nível e a duração.
"""

import pytest

from agents.curator import CuratorAgent


@pytest.fixture
def curator():
    return CuratorAgent()


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
