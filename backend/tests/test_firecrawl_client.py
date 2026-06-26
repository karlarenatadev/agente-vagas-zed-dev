"""Testes do cliente Firecrawl: deteccao de exaustao de creditos/cota.

A logica de rede do SDK nao e exercida aqui; testamos a heuristica pura que
decide se um erro deve virar FirecrawlCreditError (e, no Scout, acionar o
fallback de LLM em vez do erro generico)."""

import pytest

from firecrawl_client import (
    FirecrawlCreditError,
    FirecrawlProviderError,
    _is_credit_exhaustion,
)


class _Resp:
    """Stub minimo de response com status_code, como em requests/HTTP errors."""

    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def test_credit_exhaustion_por_status_402():
    exc = RuntimeError("falha generica")
    exc.response = _Resp(402)  # type: ignore[attr-defined]
    assert _is_credit_exhaustion(exc) is True


def test_status_diferente_de_402_nao_e_credito_por_si_so():
    exc = RuntimeError("erro qualquer")
    exc.response = _Resp(500)  # type: ignore[attr-defined]
    assert _is_credit_exhaustion(exc) is False


@pytest.mark.parametrize(
    "mensagem",
    [
        "Insufficient credits to perform this request",
        "Payment Required",
        "You are out of credits",
        "quota exceeded for this billing period",
        "Error: HTTP 402",
        "Please upgrade your plan to continue",
    ],
)
def test_credit_exhaustion_por_mensagem(mensagem: str):
    assert _is_credit_exhaustion(Exception(mensagem)) is True


@pytest.mark.parametrize(
    "mensagem",
    [
        "connection timed out",
        "rate limit exceeded",  # rate-limit transitorio != falta de credito
        "internal server error",
        "not found",
        "temporarily unavailable",
    ],
)
def test_nao_e_credit_exhaustion(mensagem: str):
    assert _is_credit_exhaustion(Exception(mensagem)) is False


def test_credit_error_e_subclasse_de_provider_error():
    # Garante retrocompatibilidade: quem captura o erro generico ainda pega o de credito.
    assert issubclass(FirecrawlCreditError, FirecrawlProviderError)
