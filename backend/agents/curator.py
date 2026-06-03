"""
Agente Curator - recomenda materiais acessiveis para lacunas de habilidades.

Fluxo:
1. Extrai habilidades faltantes dos resultados do Scout.
2. Busca cursos, videos e documentacao com Firecrawl.
3. Prioriza conteudo gratuito, acessivel e pratico.
4. Retorna um envelope com dados reais e erros parciais.
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from typing import Any, AsyncGenerator
from urllib.parse import urlparse

from agents.base import BaseAgent


LEVEL_ORDER = {"iniciante": 0, "intermediario": 1, "avancado": 2}
COST_ORDER = {"gratuito": 0, "certificado opcional": 1, "acessivel": 2, "premium": 3, "Nao informado": 4}


@dataclass
class SearchOutcome:
    results: list[dict[str, str]]
    error: str = ""


@dataclass
class LearningResource:
    name: str
    platform: str
    price: str
    duration: str
    level: str
    skill: str
    link: str
    score: int


class CuratorAgent(BaseAgent):
    """Agente de recomendacao de aprendizado baseado em resultados reais do Firecrawl."""

    name = "Curator"

    def _run_firecrawl_search(self, query: str) -> SearchOutcome:
        """Executa firecrawl search via CLI e normaliza a resposta."""
        try:
            result = subprocess.run(
                ["firecrawl", "search", query, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return SearchOutcome([], f"timeout ao buscar: {query}")
        except FileNotFoundError:
            return SearchOutcome([], "Firecrawl CLI nao encontrado")

        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip() or "erro sem detalhes"
            return SearchOutcome([], f"{query}: {error}")

        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            return SearchOutcome([], f"{query}: JSON invalido retornado pelo Firecrawl ({exc})")

        return SearchOutcome(self._normalize_search_payload(payload))

    def _normalize_search_payload(self, payload: Any) -> list[dict[str, str]]:
        """Aceita formatos comuns do Firecrawl CLI e devolve itens uniformes."""
        if isinstance(payload, dict):
            candidates = payload.get("data") or payload.get("results") or payload.get("items") or []
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

            if url and title:
                normalized.append({"url": url, "title": title, "description": description})

        return normalized

    def _parse_profile(self, profile_text: str) -> dict[str, str]:
        data: dict[str, str] = {}
        for line in profile_text.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                data[key.strip()] = value.strip()
        return data

    def _extract_missing_skills(self, job_results: str) -> list[tuple[str, int]]:
        """Extrai habilidades faltantes, priorizando recorrencia nas vagas."""
        counts: dict[str, int] = {}
        first_seen: dict[str, str] = {}

        for line in job_results.splitlines():
            if not line.strip().startswith("habilidades_faltantes:"):
                continue

            raw = line.split(":", 1)[1]
            for skill in re.split(r"[,;]", raw):
                clean = skill.strip().strip("[]")
                if not clean or clean.lower() in {"nenhuma", "nao informado", "não informado", "nÃ£o informado"}:
                    continue

                key = clean.casefold()
                counts[key] = counts.get(key, 0) + 1
                first_seen.setdefault(key, clean)

        ordered = sorted(counts, key=lambda item: (-counts[item], list(first_seen).index(item)))
        return [(first_seen[key], counts[key]) for key in ordered]

    def _platform_for_url(self, url: str) -> str:
        host = urlparse(url).netloc.lower().replace("www.", "")
        if "youtube.com" in host or "youtu.be" in host:
            return "YouTube"
        if host.endswith("alura.com.br"):
            return "Alura"
        if host.endswith("udemy.com") or "udemy.com" in host:
            return "Udemy"
        if host.endswith("coursera.org"):
            return "Coursera"
        if host.endswith("edx.org"):
            return "edX"
        if "learn.microsoft.com" in host:
            return "Microsoft Learn"
        if "developers.google.com" in host or "cloud.google.com" in host:
            return "Google"
        if "kaggle.com" in host:
            return "Kaggle Learn"
        if "freecodecamp.org" in host:
            return "FreeCodeCamp"
        if "developer.mozilla.org" in host:
            return "MDN"
        if any(term in host for term in ["docs.", "documentation", "readthedocs"]):
            return "Documentacao Oficial"
        return host or "Outra"

    def _price_for_platform(self, platform: str, title: str, description: str) -> str:
        text = f"{title} {description}".casefold()
        if platform in {"YouTube", "Documentacao Oficial", "Microsoft Learn", "Kaggle Learn", "FreeCodeCamp", "MDN"}:
            return "gratuito"
        if platform in {"Coursera", "edX"}:
            return "certificado opcional"
        if "gratis" in text or "gratuito" in text or "free" in text:
            return "gratuito"
        if platform == "Udemy":
            return "acessivel"
        if platform == "Alura":
            return "premium"
        return "Nao informado"

    def _classify_level(self, title: str, description: str, default_level: str) -> str:
        text = f"{title} {description}".casefold()
        if any(word in text for word in ["avancado", "avançado", "avanÃ§ado", "profundo", "expert", "arquitetura", "especialista", "advanced"]):
            return "avancado"
        if any(word in text for word in ["intermediario", "intermediário", "intermediÃ¡rio", "pipeline", "projeto", "pratica", "prática", "prÃ¡tica", "hands-on"]):
            return "intermediario"
        if any(word in text for word in ["introducao", "introdução", "introduÃ§Ã£o", "primeiros passos", "fundamentos", "basico", "básico", "bÃ¡sico", "iniciante", "beginner", "getting started"]):
            return "iniciante"
        return default_level

    def _extract_duration(self, title: str, description: str) -> str:
        text = f"{title} {description}"
        match = re.search(r"(\d{1,3}\s*(?:h|horas?|hours?|min|mins|minutos?))", text, re.IGNORECASE)
        return match.group(1).replace(" h", "h") if match else "Nao informado"

    def _score_result(self, item: dict[str, str], skill: str, recurrence: int, query_type: str) -> int:
        platform = self._platform_for_url(item["url"])
        price = self._price_for_platform(platform, item["title"], item["description"])
        title = item["title"].casefold()
        description = item["description"].casefold()
        url = item["url"].casefold()
        skill_terms = [part for part in re.split(r"\s+", skill.casefold()) if len(part) > 2]

        score = recurrence * 10
        if any(term in title for term in skill_terms):
            score += 24
        if any(term in description for term in skill_terms):
            score += 12
        if query_type == "gratuito" and price == "gratuito":
            score += 22
        if query_type == "acessivel" and price in {"acessivel", "premium", "certificado opcional"}:
            score += 12
        if platform in {"YouTube", "Alura", "Udemy", "Coursera", "edX", "Microsoft Learn", "Kaggle Learn", "FreeCodeCamp", "MDN"}:
            score += 12
        if "curso" in title or "course" in title or "tutorial" in title or "playlist" in title:
            score += 8
        if "projeto" in title or "project" in title or "hands-on" in title:
            score += 6
        if "youtube.com" in url and "watch" in url:
            score += 4
        return score

    def _build_resource(
        self,
        item: dict[str, str],
        skill: str,
        recurrence: int,
        query_type: str,
        default_level: str,
    ) -> LearningResource:
        platform = self._platform_for_url(item["url"])
        return LearningResource(
            name=item["title"],
            platform=platform,
            price=self._price_for_platform(platform, item["title"], item["description"]),
            duration=self._extract_duration(item["title"], item["description"]),
            level=self._classify_level(item["title"], item["description"], default_level),
            skill=skill,
            link=item["url"],
            score=self._score_result(item, skill, recurrence, query_type),
        )

    def _queries_for_skill(self, skill: str, area: str) -> list[tuple[str, str]]:
        return [
            ("gratuito", f"{skill} curso gratuito iniciante youtube portugues"),
            ("gratuito", f"{skill} tutorial gratuito projeto"),
            ("documentacao", f"{skill} documentacao oficial tutorial"),
            ("acessivel", f"{skill} curso barato alura udemy coursera {area}".strip()),
            ("fallback", f"{skill} curso tutorial projeto {area}".strip()),
        ]

    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        """
        Executa a busca de materiais.
        context: {'profile': str, 'job_results': str}
        """
        job_results = context.get("job_results", "")
        profile = self._parse_profile(context.get("profile", ""))

        if not job_results.strip():
            yield "## RESPOSTA: CURATOR\n### estado\nerro\n\n"
            yield "### resumo\nAinda nao ha resultados de vagas para analisar.\n\n"
            yield "### dados\n\n"
            yield "### erros\ndata/job-search-results.md esta vazio ou ausente. Busque vagas primeiro pela opcao A.\n"
            return

        area = profile.get("Area de interesse") or profile.get("Área de interesse") or profile.get("Ãrea de interesse") or "tecnologia"
        level = (profile.get("Nivel de experiencia") or profile.get("Nível de experiência") or profile.get("NÃ­vel de experiÃªncia") or "").casefold()
        default_level = "iniciante" if "junior" in level or "júnior" in level or "jÃºnior" in level else "intermediario"

        missing_skills = self._extract_missing_skills(job_results)
        if not missing_skills:
            yield "## RESPOSTA: CURATOR\n### estado\nerro\n\n"
            yield "### resumo\nAs vagas analisadas nao indicaram lacunas claras de habilidade.\n\n"
            yield "### dados\n\n"
            yield "### erros\nNenhuma linha habilidades_faltantes com valores acionaveis foi encontrada.\n"
            return

        prioritized = missing_skills[:5]
        yield f"Buscando materiais acessiveis para {len(prioritized)} lacunas priorizadas em {area}...\n\n"

        recommendations: list[LearningResource] = []
        errors: list[str] = []
        used_urls: set[str] = set()

        for skill, recurrence in prioritized:
            if len(recommendations) >= 8:
                break

            yield f"1. habilidade: {skill}\n   status: buscando opcoes gratuitas e acessiveis\n"

            skill_candidates: list[LearningResource] = []
            for query_type, query in self._queries_for_skill(skill, area):
                outcome = self._run_firecrawl_search(query)
                if outcome.error:
                    errors.append(f"{skill}: {outcome.error}")
                    continue

                for item in outcome.results[:5]:
                    if item["url"] in used_urls:
                        continue
                    resource = self._build_resource(item, skill, recurrence, query_type, default_level)
                    skill_candidates.append(resource)

            skill_candidates.sort(
                key=lambda item: (
                    COST_ORDER.get(item.price, 99),
                    LEVEL_ORDER.get(item.level, 99),
                    -item.score,
                    item.name.casefold(),
                )
            )

            picked_for_skill: list[LearningResource] = []
            has_free = False
            has_paid = False
            for resource in skill_candidates:
                if len(picked_for_skill) >= 2:
                    break
                if resource.price == "gratuito" and not has_free:
                    picked_for_skill.append(resource)
                    has_free = True
                elif resource.price != "gratuito" and not has_paid:
                    picked_for_skill.append(resource)
                    has_paid = True

            if not picked_for_skill and skill_candidates:
                picked_for_skill = skill_candidates[:1]

            if picked_for_skill:
                for resource in picked_for_skill:
                    recommendations.append(resource)
                    used_urls.add(resource.link)
                    yield f"   status: material encontrado\n   material: {resource.name}\n"
                yield "\n"
            else:
                errors.append(f"{skill}: nenhum material encontrado")
                yield "   status: nenhum material encontrado\n\n"

        recommendations.sort(
            key=lambda item: (
                LEVEL_ORDER.get(item.level, 99),
                COST_ORDER.get(item.price, 99),
                -item.score,
                item.name.casefold(),
            )
        )
        recommendations = recommendations[:8]

        if not recommendations:
            yield "## RESPOSTA: CURATOR\n### estado\nerro\n\n"
            yield "### resumo\nNao encontrei materiais para as lacunas identificadas.\n\n"
            yield "### dados\n\n"
            yield "### erros\n"
            yield "\n".join(f"{index}. {error}" for index, error in enumerate(errors, 1))
            yield "\n"
            return

        yield "## RESPOSTA: CURATOR\n### estado\nsucesso\n\n"
        yield "### resumo\n"
        yield f"Encontrei {len(recommendations)} material(is) para desenvolver as principais lacunas das vagas. Priorizei opcoes gratuitas, acessiveis e praticas para voce conseguir comecar sem travar por custo.\n\n"
        yield "### dados\n"

        for index, resource in enumerate(recommendations, 1):
            yield f"{index}. nome_curso: {resource.name}\n"
            yield f"   plataforma: {resource.platform}\n"
            yield f"   preco: {resource.price}\n"
            yield f"   duracao: {resource.duration}\n"
            yield f"   nivel: {resource.level}\n"
            yield f"   aborda_habilidade: {resource.skill}\n"
            yield f"   link: {resource.link}\n\n"

        yield "Ordem sugerida:\n"
        for index, resource in enumerate(recommendations, 1):
            yield f"{index}. {resource.name}\n"

        yield "\n### erros\n"
        if errors:
            for index, error in enumerate(errors, 1):
                yield f"{index}. {error}\n"
        else:
            yield "Nenhum erro parcial.\n"
