"""Cliente seguro para Firecrawl SDK."""

from __future__ import annotations

import asyncio
from typing import Any

import requests
from firecrawl import FirecrawlApp

import config
from logging_config import get_logger


logger = get_logger(__name__)


class FirecrawlProviderError(RuntimeError):
    """Falha controlada da integracao Firecrawl."""

    public_message = "Busca externa temporariamente indisponivel."


def _create_app() -> FirecrawlApp:
    return FirecrawlApp(api_key=config.FIRECRAWL_API_KEY)


def _normalize_search_payload(payload: Any) -> list[dict[str, str]]:
    candidates: Any
    if isinstance(payload, dict):
        data = payload.get("data", payload)
        if isinstance(data, dict):
            candidates = data.get("web") or data.get("results") or data.get("items") or []
        else:
            candidates = data
    elif isinstance(payload, list):
        candidates = payload
    else:
        candidates = []

    normalized: list[dict[str, str]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue

        url = str(item.get("url") or item.get("link") or "").strip()
        title = str(item.get("title") or item.get("titulo") or item.get("name") or "").strip()
        description = str(
            item.get("description")
            or item.get("descricao")
            or item.get("snippet")
            or item.get("markdown")
            or ""
        ).strip()
        if url:
            normalized.append(
                {
                    "url": url,
                    "title": title or url,
                    "description": description,
                }
            )

    return normalized


def _extract_markdown(payload: Any) -> str:
    if isinstance(payload, dict):
        markdown = payload.get("markdown") or payload.get("content") or ""
        return str(markdown).strip()
    if isinstance(payload, str):
        return payload.strip()
    return ""


def _search_sync(query: str, params: dict[str, Any]) -> Any:
    return _create_app().search(query, params)


def _scrape_sync(url: str) -> Any:
    return _create_app().scrape_url(url, {"formats": ["markdown"]})


async def firecrawl_search(
    query: str,
    *,
    session_id: str,
    tbs: str = "",
    limit: int = 5,
) -> list[dict[str, str]]:
    params: dict[str, Any] = {"limit": limit}
    if tbs:
        params["tbs"] = tbs

    try:
        payload = await asyncio.to_thread(_search_sync, query, params)
        results = _normalize_search_payload(payload)
        logger.info(
            "Busca Firecrawl concluida",
            extra={
                "event": "firecrawl_search_success",
                "session_id": session_id,
                "query_length": len(query),
                "result_count": len(results),
            },
        )
        return results
    except (requests.RequestException, ValueError, TimeoutError, KeyError) as exc:
        logger.exception(
            "Busca Firecrawl falhou",
            extra={
                "event": "firecrawl_search_error",
                "session_id": session_id,
                "query_length": len(query),
                "error_type": type(exc).__name__,
            },
        )
        raise FirecrawlProviderError(FirecrawlProviderError.public_message) from exc
    except Exception as exc:
        logger.exception(
            "Busca Firecrawl falhou no SDK",
            extra={
                "event": "firecrawl_search_sdk_error",
                "session_id": session_id,
                "query_length": len(query),
                "error_type": type(exc).__name__,
            },
        )
        raise FirecrawlProviderError(FirecrawlProviderError.public_message) from exc


async def firecrawl_scrape(
    url: str,
    *,
    session_id: str,
) -> str:
    try:
        payload = await asyncio.to_thread(_scrape_sync, url)
        markdown = _extract_markdown(payload)
        logger.info(
            "Scrape Firecrawl concluido",
            extra={
                "event": "firecrawl_scrape_success",
                "session_id": session_id,
                "url": url,
                "content_length": len(markdown),
            },
        )
        return markdown
    except (requests.RequestException, ValueError, TimeoutError, KeyError) as exc:
        logger.exception(
            "Scrape Firecrawl falhou",
            extra={
                "event": "firecrawl_scrape_error",
                "session_id": session_id,
                "url": url,
                "error_type": type(exc).__name__,
            },
        )
        raise FirecrawlProviderError(FirecrawlProviderError.public_message) from exc
    except Exception as exc:
        logger.exception(
            "Scrape Firecrawl falhou no SDK",
            extra={
                "event": "firecrawl_scrape_sdk_error",
                "session_id": session_id,
                "url": url,
                "error_type": type(exc).__name__,
            },
        )
        raise FirecrawlProviderError(FirecrawlProviderError.public_message) from exc
