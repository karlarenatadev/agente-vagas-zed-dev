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
        # Casos representativos: sinal explicito de credito, "payment required"
        # e o sinal numerico "402" embutido no texto.
        "Insufficient credits to perform this request",
        "Payment Required",
        "Error: HTTP 402",
    ],
)
def test_credit_exhaustion_por_mensagem(mensagem: str):
    assert _is_credit_exhaustion(Exception(mensagem)) is True


@pytest.mark.parametrize(
    "mensagem",
    [
        "rate limit exceeded",  # rate-limit transitorio != falta de credito
        "internal server error",  # erro generico do servidor
    ],
)
def test_nao_e_credit_exhaustion(mensagem: str):
    assert _is_credit_exhaustion(Exception(mensagem)) is False


def test_credit_error_e_subclasse_de_provider_error():
    # Garante retrocompatibilidade: quem captura o erro generico ainda pega o de credito.
    assert issubclass(FirecrawlCreditError, FirecrawlProviderError)


# ---------------------------------------------------------------------------
# Logging estruturado + conversao tipada de erros (firecrawl_search)
#
# Aqui exercitamos o fluxo real de `firecrawl_search`, mas com o SDK mockado
# via monkeypatch de `_search_sync` (a funcao chamada por asyncio.to_thread).
# Capturamos os logs com `caplog` para conferir que `session_id` e os campos
# estruturados aparecem, e verificamos a conversao da falha no tipo de excecao
# correto conforme a heuristica `_is_credit_exhaustion`.
# _Requirements: 8.3 (e 4.1, 4.2, 4.3, 4.4)_
# ---------------------------------------------------------------------------

import logging

import firecrawl_client


def _records_with_event(caplog: pytest.LogCaptureFixture, event: str):
    """Retorna os LogRecords cujo campo estruturado `event` casa com `event`."""
    return [rec for rec in caplog.records if getattr(rec, "event", None) == event]


@pytest.mark.asyncio
async def test_search_sucesso_emite_log_com_session_id_e_result_count(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    payload = [
        {"url": "https://jobs.example.com/1", "title": "Vaga 1", "description": "desc"},
        {"url": "https://jobs.example.com/2", "title": "Vaga 2", "description": ""},
    ]

    def fake_search_sync(_query: str, _params: dict) -> list[dict]:
        return payload

    monkeypatch.setattr(firecrawl_client, "_search_sync", fake_search_sync)

    with caplog.at_level(logging.INFO, logger="firecrawl_client"):
        results = await firecrawl_client.firecrawl_search(
            "engenheiro de dados", session_id="sess-success"
        )

    assert len(results) == 2

    success_logs = _records_with_event(caplog, "firecrawl_search_success")
    assert len(success_logs) == 1
    record = success_logs[0]
    assert record.session_id == "sess-success"
    assert record.result_count == 2


@pytest.mark.asyncio
async def test_search_erro_emite_log_com_session_id_e_error_type(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    def boom(_query: str, _params: dict):
        raise ValueError("internal server error")

    monkeypatch.setattr(firecrawl_client, "_search_sync", boom)

    with caplog.at_level(logging.ERROR, logger="firecrawl_client"):
        with pytest.raises(FirecrawlProviderError):
            await firecrawl_client.firecrawl_search("qualquer", session_id="sess-erro")

    error_logs = _records_with_event(caplog, "firecrawl_search_error")
    assert len(error_logs) == 1
    record = error_logs[0]
    assert record.session_id == "sess-erro"
    assert record.error_type == "ValueError"


@pytest.mark.asyncio
async def test_search_falha_sem_credito_converte_em_provider_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def boom(_query: str, _params: dict):
        raise ValueError("temporarily unavailable")

    monkeypatch.setattr(firecrawl_client, "_search_sync", boom)

    # Sinal generico (nao de credito) -> erro generico do provider.
    with pytest.raises(FirecrawlProviderError) as exc_info:
        await firecrawl_client.firecrawl_search("qualquer", session_id="sess-prov")

    assert not isinstance(exc_info.value, FirecrawlCreditError)


@pytest.mark.asyncio
async def test_search_falha_com_sinal_de_credito_converte_em_credit_error(
    monkeypatch: pytest.MonkeyPatch,
):
    def boom(_query: str, _params: dict):
        raise ValueError("Insufficient credits to perform this request")

    monkeypatch.setattr(firecrawl_client, "_search_sync", boom)

    # Mensagem com sinal de credito -> FirecrawlCreditError (subclasse).
    with pytest.raises(FirecrawlCreditError):
        await firecrawl_client.firecrawl_search("qualquer", session_id="sess-credit")


@pytest.mark.asyncio
async def test_search_falha_http_402_converte_em_credit_error(
    monkeypatch: pytest.MonkeyPatch,
):
    class _Http402(RuntimeError):
        def __init__(self) -> None:
            super().__init__("request failed")
            self.response = _Resp(402)

    def boom(_query: str, _params: dict):
        raise _Http402()

    monkeypatch.setattr(firecrawl_client, "_search_sync", boom)

    # HTTP 402 (status_code) -> tratado como exaustao de credito.
    with pytest.raises(FirecrawlCreditError):
        await firecrawl_client.firecrawl_search("qualquer", session_id="sess-402")
