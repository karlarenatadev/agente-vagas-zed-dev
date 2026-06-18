"""
Agente Curator - recomenda materiais acessiveis para lacunas de habilidades.

Fluxo:
1. Extrai habilidades faltantes dos resultados do Scout.
2. Busca cursos, videos e documentacao com Firecrawl.
3. Prioriza conteudo gratuito, acessivel e pratico.
4. Retorna um envelope com dados reais e erros parciais.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncGenerator
from urllib.parse import urlparse

from agents.base import BaseAgent
from firecrawl_client import FirecrawlProviderError, firecrawl_search


LEVEL_ORDER = {"iniciante": 0, "intermediario": 1, "avancado": 2}
COST_ORDER = {
    "gratuito": 0,
    "certificado opcional": 1,
    "acessivel": 2,
    "Consultar plataforma": 2,
    "premium": 3,
    "Nao informado": 4,
}

INTERNAL_RECOMMENDATIONS: dict[str, dict[str, tuple[str, str, str, str, str]]] = {
    "html": {
        "free": ("MDN Learn HTML", "MDN", "https://developer.mozilla.org/pt-BR/docs/Learn/HTML", "Nao informado", "iniciante"),
        "reference": ("HTML: HyperText Markup Language", "MDN", "https://developer.mozilla.org/pt-BR/docs/Web/HTML", "Nao informado", "iniciante"),
        "quick": ("HTML Tutorial", "W3Schools", "https://www.w3schools.com/html/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de HTML em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=HTML", "Consultar plataforma", "iniciante"),
    },
    "css": {
        "free": ("MDN Learn CSS", "MDN", "https://developer.mozilla.org/pt-BR/docs/Learn/CSS", "Nao informado", "iniciante"),
        "reference": ("CSS: Cascading Style Sheets", "MDN", "https://developer.mozilla.org/pt-BR/docs/Web/CSS", "Nao informado", "iniciante"),
        "quick": ("CSS Tutorial", "W3Schools", "https://www.w3schools.com/css/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de CSS responsivo em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=CSS", "Consultar plataforma", "iniciante"),
    },
    "javascript": {
        "free": ("JavaScript Algorithms and Data Structures", "FreeCodeCamp", "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/", "Nao informado", "iniciante"),
        "reference": ("JavaScript", "MDN", "https://developer.mozilla.org/pt-BR/docs/Web/JavaScript", "Nao informado", "intermediario"),
        "quick": ("JavaScript Tutorial", "W3Schools", "https://www.w3schools.com/js/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de JavaScript moderno em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=JavaScript", "Consultar plataforma", "intermediario"),
    },
    "typescript": {
        "free": ("TypeScript for JavaScript Programmers", "TypeScript Docs", "https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html", "Nao informado", "iniciante"),
        "reference": ("TypeScript Handbook", "TypeScript Docs", "https://www.typescriptlang.org/docs/handbook/intro.html", "Nao informado", "intermediario"),
        "quick": ("TypeScript Tutorial", "W3Schools", "https://www.w3schools.com/typescript/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de TypeScript aplicado em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=TypeScript", "Consultar plataforma", "intermediario"),
    },
    "react": {
        "free": ("Learn React", "React Docs", "https://react.dev/learn", "Nao informado", "iniciante"),
        "reference": ("React Reference", "React Docs", "https://react.dev/reference/react", "Nao informado", "intermediario"),
        "quick": ("React Quick Start", "React Docs", "https://react.dev/learn", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de React com projetos em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=React", "Consultar plataforma", "intermediario"),
    },
    "git": {
        "free": ("GitHub Skills", "GitHub Skills", "https://skills.github.com/", "Nao informado", "iniciante"),
        "reference": ("Git Documentation", "Git", "https://git-scm.com/doc", "Nao informado", "intermediario"),
        "quick": ("Git Handbook", "GitHub Docs", "https://guides.github.com/introduction/git-handbook/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de Git e GitHub em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=Git%20GitHub", "Consultar plataforma", "iniciante"),
    },
    "consumo de apis": {
        "free": ("Client-side web APIs", "MDN", "https://developer.mozilla.org/pt-BR/docs/Learn/JavaScript/Client-side_web_APIs", "Nao informado", "intermediario"),
        "reference": ("Fetch API", "MDN", "https://developer.mozilla.org/pt-BR/docs/Web/API/Fetch_API", "Nao informado", "intermediario"),
        "quick": ("Using the Fetch API", "MDN", "https://developer.mozilla.org/pt-BR/docs/Web/API/Fetch_API/Using_Fetch", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de consumo de APIs REST em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=API%20REST", "Consultar plataforma", "intermediario"),
    },
    "python": {
        "free": ("Python for Everybody", "FreeCodeCamp", "https://www.freecodecamp.org/learn/scientific-computing-with-python/", "Nao informado", "iniciante"),
        "reference": ("The Python Tutorial", "Python Docs", "https://docs.python.org/3/tutorial/", "Nao informado", "intermediario"),
        "quick": ("Python Tutorial", "W3Schools", "https://www.w3schools.com/python/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de Python aplicado em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=Python", "Consultar plataforma", "intermediario"),
    },
    "sql": {
        "free": ("Intro to SQL", "Kaggle Learn", "https://www.kaggle.com/learn/intro-to-sql", "Nao informado", "iniciante"),
        "reference": ("SQL Tutorial", "W3Schools", "https://www.w3schools.com/sql/", "Nao informado", "iniciante"),
        "quick": ("Advanced SQL", "Kaggle Learn", "https://www.kaggle.com/learn/advanced-sql", "Nao informado", "intermediario"),
        "paid": ("Curso estruturado de SQL para analise de dados em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=SQL", "Consultar plataforma", "intermediario"),
    },
    "power bi": {
        "free": ("Get started with Microsoft Power BI", "Microsoft Learn", "https://learn.microsoft.com/pt-br/training/powerplatform/power-bi", "Nao informado", "iniciante"),
        "reference": ("Power BI documentation", "Microsoft Learn", "https://learn.microsoft.com/pt-br/power-bi/", "Nao informado", "intermediario"),
        "quick": ("Guided learning for Power BI", "Microsoft Learn", "https://learn.microsoft.com/pt-br/power-bi/guided-learning/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de Power BI com projetos em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=Power%20BI", "Consultar plataforma", "intermediario"),
    },
    "excel": {
        "free": ("Treinamento em Excel", "Microsoft Support", "https://support.microsoft.com/pt-br/office/treinamento-em-excel-9bc05390-e94c-46af-a5b3-d7c22f6990bb", "Nao informado", "iniciante"),
        "reference": ("Ajuda e aprendizado do Excel", "Microsoft Support", "https://support.microsoft.com/pt-br/excel", "Nao informado", "iniciante"),
        "quick": ("Excel formulas and functions", "Microsoft Support", "https://support.microsoft.com/pt-br/office/f%C3%B3rmulas-e-fun%C3%A7%C3%B5es-294d9486-b332-48ed-b489-abe7d0f9eda9", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de Excel para analise de dados em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=Excel", "Consultar plataforma", "intermediario"),
    },
    "pandas": {
        "free": ("Pandas", "Kaggle Learn", "https://www.kaggle.com/learn/pandas", "Nao informado", "iniciante"),
        "reference": ("Getting started with pandas", "Pandas Docs", "https://pandas.pydata.org/docs/getting_started/index.html", "Nao informado", "intermediario"),
        "quick": ("10 minutes to pandas", "Pandas Docs", "https://pandas.pydata.org/docs/user_guide/10min.html", "Nao informado", "intermediario"),
        "paid": ("Curso estruturado de pandas e analise de dados em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=pandas", "Consultar plataforma", "intermediario"),
    },
    "estatistica": {
        "free": ("Statistics and probability", "Khan Academy", "https://www.khanacademy.org/math/statistics-probability", "Nao informado", "iniciante"),
        "reference": ("Intro to Machine Learning", "Kaggle Learn", "https://www.kaggle.com/learn/intro-to-machine-learning", "Nao informado", "intermediario"),
        "quick": ("Statistics Tutorial", "W3Schools", "https://www.w3schools.com/statistics/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de estatistica aplicada em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=estatistica", "Consultar plataforma", "intermediario"),
    },
    "storytelling com dados": {
        "free": ("Storytelling with Data Blog", "Storytelling with Data", "https://www.storytellingwithdata.com/blog", "Nao informado", "intermediario"),
        "reference": ("Storytelling with Data Resources", "Storytelling with Data", "https://www.storytellingwithdata.com/resources", "Nao informado", "intermediario"),
        "quick": ("Data visualization catalogue", "Data Viz Catalogue", "https://datavizcatalogue.com/", "Nao informado", "iniciante"),
        "paid": ("Curso estruturado de visualizacao e narrativa de dados em marketplace de cursos", "Udemy/Coursera/Alura", "https://www.udemy.com/courses/search/?q=data%20storytelling", "Consultar plataforma", "intermediario"),
    },
}

SKILL_ALIASES = {
    "api": "consumo de apis",
    "apis": "consumo de apis",
    "api rest": "consumo de apis",
    "rest": "consumo de apis",
    "consumo de api": "consumo de apis",
    "consumo de apis": "consumo de apis",
    "powerbi": "power bi",
    "power-bi": "power bi",
    "js": "javascript",
    "ts": "typescript",
    "react.js": "react",
    "reactjs": "react",
    "github": "git",
    "estatistica": "estatistica",
    "estatisticas": "estatistica",
    "statistics": "estatistica",
    "storytelling": "storytelling com dados",
    "data storytelling": "storytelling com dados",
    "narrativa de dados": "storytelling com dados",
}


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


@dataclass
class SkillPriority:
    name: str
    missing_count: int
    recurring_count: int
    related_jobs: list[str]

    @property
    def impact(self) -> int:
        return self.missing_count * 3 + self.recurring_count * 2 + len(self.related_jobs)


@dataclass
class LearningPlanItem:
    skill: str
    priority: str
    recommended_level: str
    why_it_matters: str
    free_resource: LearningResource | None
    paid_resource: LearningResource | None
    trusted_reference: LearningResource | None
    quick_content: LearningResource | None
    project: str
    study_time: str
    relation_to_jobs: str
    profile_alignment: str
    expected_impact: str
    bucket: str
    impact: int


class CuratorAgent(BaseAgent):
    """Agente de recomendacao de aprendizado baseado em resultados reais do Firecrawl."""

    name = "Curator"

    def _read_data_file(self, filename: str) -> str:
        # Lê da pasta da sessão atual (não mais de um "data/" global), para
        # respeitar o isolamento por sessão.
        path = self.paths.dir / filename
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    async def _run_firecrawl_search(self, query: str) -> SearchOutcome:
        """Executa Firecrawl pelo SDK sem bloquear o event loop."""
        try:
            results = await firecrawl_search(
                query,
                session_id=self.paths.session_id,
                limit=6,
            )
        except FirecrawlProviderError as exc:
            return SearchOutcome([], f"{query}: {exc.public_message}")

        return SearchOutcome(results)

    def _parse_profile(self, profile_text: str) -> dict[str, str]:
        data: dict[str, str] = {}
        for line in profile_text.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                data[key.strip()] = value.strip()
        return data

    def _profile_value(self, profile: dict[str, str], *keys: str, default: str = "") -> str:
        normalized = {key.casefold(): value for key, value in profile.items()}
        for key in keys:
            value = normalized.get(key.casefold())
            if value:
                return value
        return default

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

    def _extract_recurring_requirements(self, job_results: str) -> dict[str, tuple[str, int]]:
        """Extrai requisitos_mais_recorrentes do Scout novo, mantendo compatibilidade com texto simples."""
        requirements: dict[str, tuple[str, int]] = {}
        current_requirement = ""

        for line in job_results.splitlines():
            stripped = line.strip()
            if "requisito:" in stripped:
                current_requirement = stripped.split("requisito:", 1)[1].strip()
                if current_requirement:
                    requirements[current_requirement.casefold()] = (current_requirement, 1)
                continue

            if current_requirement and "ocorrencias:" in stripped:
                raw_count = stripped.split("ocorrencias:", 1)[1].strip()
                try:
                    count = int(raw_count)
                except ValueError:
                    count = 1
                requirements[current_requirement.casefold()] = (current_requirement, count)
                current_requirement = ""

        return requirements

    def _extract_skill_job_relations(self, job_results: str) -> dict[str, list[str]]:
        """Mapeia habilidade faltante para vagas onde ela aparece."""
        relations: dict[str, list[str]] = {}
        current_title = ""

        for line in job_results.splitlines():
            stripped = line.strip()
            if "titulo:" in stripped:
                current_title = stripped.split(":", 1)[1].strip()
                continue

            if not stripped.startswith("habilidades_faltantes:"):
                continue

            raw = stripped.split(":", 1)[1]
            for skill in re.split(r"[,;]", raw):
                clean = skill.strip().strip("[]")
                if not clean or clean.casefold() in {"nenhuma", "nao informado", "não informado"}:
                    continue
                relations.setdefault(clean.casefold(), [])
                if current_title and current_title not in relations[clean.casefold()]:
                    relations[clean.casefold()].append(current_title)

        return relations

    def _prioritize_skills(self, job_results: str) -> list[SkillPriority]:
        missing = self._extract_missing_skills(job_results)
        recurring = self._extract_recurring_requirements(job_results)
        relations = self._extract_skill_job_relations(job_results)

        priorities: dict[str, SkillPriority] = {}
        for skill, count in missing:
            key = skill.casefold()
            recurring_count = recurring.get(key, (skill, 0))[1]
            priorities[key] = SkillPriority(
                name=skill,
                missing_count=count,
                recurring_count=recurring_count,
                related_jobs=relations.get(key, []),
            )

        for key, (skill, count) in recurring.items():
            if key in priorities:
                continue
            priorities[key] = SkillPriority(
                name=skill,
                missing_count=0,
                recurring_count=count,
                related_jobs=relations.get(key, []),
            )

        return sorted(priorities.values(), key=lambda item: (-item.impact, item.name.casefold()))

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
        if "react.dev" in host:
            return "React Docs"
        if "typescriptlang.org" in host:
            return "TypeScript Docs"
        if "git-scm.com" in host:
            return "Git"
        if "github.com" in host:
            return "GitHub Docs"
        if "python.org" in host:
            return "Python Docs"
        if "pandas.pydata.org" in host:
            return "Pandas Docs"
        if "support.microsoft.com" in host:
            return "Microsoft Support"
        if "w3schools.com" in host:
            return "W3Schools"
        if "khanacademy.org" in host:
            return "Khan Academy"
        if any(term in host for term in ["docs.", "documentation", "readthedocs"]):
            return "Documentacao Oficial"
        return host or "Outra"

    def _price_for_platform(self, platform: str, title: str, description: str) -> str:
        # Remove acentos para que "grátis"/"gratuíto" casem com "gratis"/"gratuito".
        text = unicodedata.normalize("NFKD", f"{title} {description}".casefold())
        text = text.encode("ascii", "ignore").decode("ascii")
        if platform in {
            "YouTube",
            "Documentacao Oficial",
            "Microsoft Learn",
            "Kaggle Learn",
            "FreeCodeCamp",
            "MDN",
            "React Docs",
            "TypeScript Docs",
            "Git",
            "GitHub Docs",
            "Python Docs",
            "Pandas Docs",
            "Microsoft Support",
            "W3Schools",
            "Khan Academy",
        }:
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
        # Unidades longas vêm antes de "h" na alternância para preservar a
        # palavra completa ("10 horas" em vez de "10h"). Número e unidade são
        # capturados separados e reunidos com um único espaço.
        match = re.search(
            r"(\d{1,3})\s*(horas?|hours?|minutos?|mins?|min|h)\b",
            text,
            re.IGNORECASE,
        )
        return f"{match.group(1)} {match.group(2)}" if match else "Nao informado"

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
        if platform in {
            "YouTube",
            "Alura",
            "Udemy",
            "Coursera",
            "edX",
            "Microsoft Learn",
            "Kaggle Learn",
            "FreeCodeCamp",
            "MDN",
            "React Docs",
            "TypeScript Docs",
            "Git",
            "GitHub Docs",
            "Python Docs",
            "Pandas Docs",
            "Microsoft Support",
            "W3Schools",
            "Khan Academy",
        }:
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

    def _skill_catalog_key(self, skill: str) -> str:
        normalized = unicodedata.normalize("NFKD", skill.casefold())
        ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
        clean = re.sub(r"[^a-z0-9+#.\s-]", " ", ascii_text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return SKILL_ALIASES.get(clean, clean)

    def _catalog_resource(
        self,
        skill: str,
        recurrence: int,
        kind: str,
        data: tuple[str, str, str, str, str],
    ) -> LearningResource:
        name, platform, link, duration, level = data
        price = "Consultar plataforma" if kind == "paid" else "gratuito"
        score_bonus = {"free": 34, "reference": 30, "quick": 24, "paid": 18}[kind]
        return LearningResource(
            name=name,
            platform=platform,
            price=price,
            duration=duration,
            level=level,
            skill=skill,
            link=link,
            score=recurrence * 10 + score_bonus,
        )

    def _internal_resources_for_skill(self, skill: str, recurrence: int) -> list[LearningResource]:
        catalog_key = self._skill_catalog_key(skill)
        catalog = INTERNAL_RECOMMENDATIONS.get(catalog_key)
        if not catalog:
            return []
        return [
            self._catalog_resource(skill, recurrence, kind, data)
            for kind, data in catalog.items()
        ]

    def _needs_internal_support(self, candidates: list[LearningResource]) -> bool:
        if not candidates:
            return True
        has_free = any(item.price == "gratuito" for item in candidates)
        has_reference = any(self._is_trusted_reference(item) for item in candidates)
        has_quick = any(self._is_quick_content(item) for item in candidates)
        return not (has_free and has_reference and has_quick)

    def _queries_for_skill(self, skill: str, area: str) -> list[tuple[str, str]]:
        return [
            ("gratuito", f"{skill} curso gratuito iniciante youtube portugues"),
            ("gratuito", f"{skill} tutorial gratuito projeto"),
            ("documentacao", f"{skill} documentacao oficial tutorial"),
            ("acessivel", f"{skill} curso barato alura udemy coursera {area}".strip()),
            ("fallback", f"{skill} curso tutorial projeto {area}".strip()),
        ]

    def _priority_label(self, skill: SkillPriority) -> str:
        if skill.impact >= 7:
            return "Alta"
        if skill.impact >= 4:
            return "Média"
        return "Baixa"

    def _bucket_for_skill(self, index: int, skill: SkillPriority) -> str:
        priority = self._priority_label(skill)
        if index < 2 or priority == "Alta":
            return "estudar agora"
        if index < 5 or priority == "Média":
            return "estudar depois"
        return "opcional"

    def _why_skill_matters(self, skill: SkillPriority, area: str) -> str:
        if skill.related_jobs:
            return (
                f"Aparece como lacuna em {len(skill.related_jobs)} oportunidade(s) analisada(s) "
                f"e influencia diretamente seu match em {area}."
            )
        if skill.recurring_count:
            return f"Foi um requisito recorrente nas oportunidades mapeadas para {area}."
        return f"Complementa sua base atual e pode aumentar sua competitividade em {area}."

    def _relation_to_jobs(self, skill: SkillPriority) -> str:
        if skill.related_jobs:
            jobs = ", ".join(skill.related_jobs[:3])
            suffix = "..." if len(skill.related_jobs) > 3 else ""
            return f"Relacionada às vagas: {jobs}{suffix}"
        if skill.recurring_count:
            return f"Requisito citado {skill.recurring_count} vez(es) no mapeamento do Scout."
        return "Relação indireta com as oportunidades; útil como reforço de base."

    def _project_suggestion(self, skill: str, area: str) -> str:
        area_text = area.casefold()
        skill_text = skill.casefold()
        if "dados" in area_text or any(term in skill_text for term in ["sql", "python", "power bi", "pandas"]):
            return f"Monte uma análise curta usando {skill}: colete um dataset público, gere 3 insights e publique um dashboard ou notebook."
        if "frontend" in area_text or any(term in skill_text for term in ["react", "javascript", "typescript", "html", "css"]):
            return f"Crie uma tela pequena usando {skill}, consumindo uma API pública e documentando decisões no README."
        if "backend" in area_text or any(term in skill_text for term in ["api", "docker", "java", "node", "python"]):
            return f"Construa uma API simples com {skill}, incluindo autenticação básica, testes e instruções de execução."
        if "devops" in area_text or any(term in skill_text for term in ["aws", "docker", "kubernetes", "terraform"]):
            return f"Publique um serviço de exemplo usando {skill}, com pipeline simples e registro dos comandos usados."
        if "design" in area_text or "figma" in skill_text:
            return f"Desenhe um fluxo completo no Figma aplicando {skill}, com tela inicial, estado vazio e versão mobile."
        return f"Crie um mini-projeto demonstrando {skill} em um problema realista da área de {area}."

    def _study_time(self, priority: str, level: str) -> str:
        if priority == "Alta":
            return "1 a 2 semanas, com 4 a 6 horas de prática"
        if "iniciante" in level:
            return "3 a 5 dias, com 2 a 4 horas de prática"
        return "1 semana, com 3 a 5 horas de prática"

    def _recommended_level(self, skill: SkillPriority, user_level: str) -> str:
        user_level_text = user_level.casefold()
        if any(term in user_level_text for term in ["senior", "sênior", "pleno", "avancado", "avançado"]):
            return "avancado" if skill.impact >= 8 else "intermediario"
        if any(term in user_level_text for term in ["junior", "júnior", "iniciante", "estagio", "estágio"]):
            return "intermediario" if skill.impact >= 7 else "iniciante"
        return "intermediario" if skill.impact >= 5 else "iniciante"

    def _profile_alignment(
        self,
        skill: SkillPriority,
        area: str,
        target_roles: str,
        career_goal: str,
        current_skills: str,
    ) -> str:
        parts = [f"Alinhada a {area}"]
        if target_roles:
            parts.append(f"funcoes alvo: {target_roles}")
        if career_goal:
            parts.append(f"objetivo: {career_goal}")
        if current_skills and skill.name.casefold() in current_skills.casefold():
            parts.append("tambem reforca uma habilidade que ja aparece no perfil")
        return "; ".join(parts) + "."

    def _expected_impact(self, skill: SkillPriority) -> str:
        if skill.impact >= 7:
            return "Alto: tende a aumentar a aderencia em vagas onde esta lacuna aparece diretamente."
        if skill.impact >= 4:
            return "Medio: melhora a leitura do curriculo e reduz lacunas recorrentes nas oportunidades."
        return "Baixo a medio: reforca base tecnica e pode diferenciar candidaturas especificas."

    def _is_trusted_reference(self, resource: LearningResource) -> bool:
        trusted_platforms = {
            "Documentacao Oficial",
            "Microsoft Learn",
            "Google",
            "Kaggle Learn",
            "FreeCodeCamp",
            "MDN",
            "GitHub Skills",
            "GitHub Docs",
            "Git",
            "React Docs",
            "TypeScript Docs",
            "Python Docs",
            "Pandas Docs",
            "Khan Academy",
            "Microsoft Support",
            "Storytelling with Data",
            "Data Viz Catalogue",
            "W3Schools",
            "Coursera",
            "edX",
        }
        return resource.platform in trusted_platforms or "docs" in resource.link.casefold()

    def _is_quick_content(self, resource: LearningResource) -> bool:
        text = f"{resource.name} {resource.duration} {resource.platform}".casefold()
        quick_terms = ["tutorial", "guia", "quickstart", "fundamentos", "playlist", "video", "aula"]
        return resource.price == "gratuito" and (
            resource.platform in {
                "YouTube",
                "FreeCodeCamp",
                "MDN",
                "Microsoft Learn",
                "Kaggle Learn",
                "W3Schools",
                "GitHub Docs",
                "React Docs",
                "Pandas Docs",
                "Data Viz Catalogue",
            }
            or any(term in text for term in quick_terms)
            or "min" in resource.duration.casefold()
        )

    def _select_plan_resources(
        self,
        candidates: list[LearningResource],
    ) -> tuple[
        LearningResource | None,
        LearningResource | None,
        LearningResource | None,
        LearningResource | None,
    ]:
        free_options = [item for item in candidates if item.price == "gratuito"]
        paid_options = [item for item in candidates if item.price in {"acessivel", "certificado opcional", "Consultar plataforma"}]
        trusted_options = [item for item in candidates if self._is_trusted_reference(item)]
        quick_options = [item for item in candidates if self._is_quick_content(item)]

        free_options.sort(key=lambda item: (-item.score, LEVEL_ORDER.get(item.level, 99), item.name.casefold()))
        paid_options.sort(key=lambda item: (-item.score, COST_ORDER.get(item.price, 99), item.name.casefold()))
        trusted_options.sort(key=lambda item: (-item.score, LEVEL_ORDER.get(item.level, 99), item.name.casefold()))
        quick_options.sort(key=lambda item: (-item.score, LEVEL_ORDER.get(item.level, 99), item.name.casefold()))
        candidates.sort(key=lambda item: (-item.score, COST_ORDER.get(item.price, 99), item.name.casefold()))

        free_resource = free_options[0] if free_options else (candidates[0] if candidates else None)
        paid_resource = paid_options[0] if paid_options else None
        trusted_reference = trusted_options[0] if trusted_options else None
        quick_content = quick_options[0] if quick_options else None
        if trusted_reference and free_resource and trusted_reference.link == free_resource.link:
            trusted_reference = trusted_options[1] if len(trusted_options) > 1 else trusted_reference
        if quick_content and free_resource and quick_content.link == free_resource.link:
            quick_content = quick_options[1] if len(quick_options) > 1 else quick_content
        if paid_resource and free_resource and paid_resource.link == free_resource.link:
            paid_resource = paid_options[1] if len(paid_options) > 1 else None

        return free_resource, paid_resource, trusted_reference, quick_content

    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        """
        Executa a busca de materiais.
        context: {'profile': str, 'job_results': str}
        """
        job_results = context.get("job_results", "") or self._read_data_file("job-search-results.md")
        profile_text = context.get("profile", "") or self._read_data_file("user-profile.md")
        profile = self._parse_profile(profile_text)

        if not job_results.strip():
            yield "## RESPOSTA: CURATOR\n### estado\nerro\n\n"
            yield "### resumo\nAinda nao ha resultados de vagas para analisar.\n\n"
            yield "### dados\n\n"
            yield "### erros\ndata/job-search-results.md esta vazio ou ausente. Busque vagas primeiro pela opcao A.\n"
            return

        area = self._profile_value(
            profile,
            "Area de interesse",
            "Área de interesse",
            "Area",
            "Área",
            default="tecnologia",
        )
        raw_level = self._profile_value(
            profile,
            "Nivel de experiencia",
            "Nível de experiência",
            "Experiencia",
            "Experiência",
            default="",
        )
        level = raw_level.casefold()
        target_roles = self._profile_value(
            profile,
            "Funcoes alvo",
            "Funções alvo",
            "Cargo alvo",
            "Cargos alvo",
            "Funcao alvo",
            "Função alvo",
            default="",
        )
        career_goal = self._profile_value(
            profile,
            "Objetivo de carreira",
            "Objetivo",
            "Meta profissional",
            default="",
        )
        current_skills = self._profile_value(
            profile,
            "Habilidades atuais",
            "Skills atuais",
            "Competencias",
            "Competências",
            default="",
        )
        default_level = "iniciante" if "junior" in level or "júnior" in level or "jÃºnior" in level else "intermediario"

        prioritized_skills = self._prioritize_skills(job_results)
        if not prioritized_skills:
            yield "## RESPOSTA: CURATOR\n### estado\nerro\n\n"
            yield "### resumo\nAs vagas analisadas nao indicaram lacunas claras de habilidade.\n\n"
            yield "### dados\n\n"
            yield "### erros\nNenhuma linha habilidades_faltantes ou requisitos_mais_recorrentes com valores acionaveis foi encontrada. Rode a opcao A primeiro para gerar data/job-search-results.md atualizado.\n"
            return

        prioritized = prioritized_skills[:7]
        yield f"Montando trilha de evolucao para {len(prioritized)} habilidade(s) priorizada(s) a partir do Scout...\n\n"

        plan_items: list[LearningPlanItem] = []
        errors: list[str] = []
        error_keys: set[str] = set()
        notices: list[str] = []
        notice_keys: set[str] = set()
        used_urls: set[str] = set()
        firecrawl_available = True

        def add_error(message: str) -> None:
            if message not in error_keys:
                errors.append(message)
                error_keys.add(message)

        def add_notice(message: str) -> None:
            if message not in notice_keys:
                notices.append(message)
                notice_keys.add(message)

        for index, skill_priority in enumerate(prioritized):
            skill = skill_priority.name
            recurrence = max(skill_priority.missing_count, skill_priority.recurring_count, 1)
            priority = self._priority_label(skill_priority)
            bucket = self._bucket_for_skill(index, skill_priority)

            recommended_level = self._recommended_level(skill_priority, raw_level)
            yield f"1. habilidade: {skill}\n   prioridade: {priority}\n   status: buscando curso gratuito, referencia confiavel e apoio pratico\n"

            skill_candidates: list[LearningResource] = []
            if firecrawl_available:
                for query_type, query in self._queries_for_skill(skill, area):
                    outcome = await self._run_firecrawl_search(query)
                    if outcome.error:
                        firecrawl_available = False
                        add_notice("Busca externa temporariamente indisponivel; trilha complementada com base interna confiavel.")
                        break

                    for item in outcome.results[:5]:
                        if item["url"] in used_urls:
                            continue
                        resource = self._build_resource(item, skill, recurrence, query_type, default_level)
                        skill_candidates.append(resource)

            if self._needs_internal_support(skill_candidates):
                internal_candidates = self._internal_resources_for_skill(skill, recurrence)
                if internal_candidates:
                    existing_links = {item.link for item in skill_candidates}
                    skill_candidates.extend(item for item in internal_candidates if item.link not in existing_links)
                    add_notice("Algumas recomendacoes foram montadas com base interna quando a busca externa nao retornou material suficiente.")

            free_resource, paid_resource, trusted_reference, quick_content = self._select_plan_resources(skill_candidates)
            if free_resource:
                used_urls.add(free_resource.link)
            if paid_resource:
                used_urls.add(paid_resource.link)
            if trusted_reference:
                used_urls.add(trusted_reference.link)
            if quick_content:
                used_urls.add(quick_content.link)

            if free_resource or trusted_reference:
                plan_items.append(
                    LearningPlanItem(
                        skill=skill,
                        priority=priority,
                        recommended_level=recommended_level,
                        why_it_matters=self._why_skill_matters(skill_priority, area),
                        free_resource=free_resource,
                        paid_resource=paid_resource,
                        trusted_reference=trusted_reference,
                        quick_content=quick_content,
                        project=self._project_suggestion(skill, area),
                        study_time=self._study_time(priority, recommended_level),
                        relation_to_jobs=self._relation_to_jobs(skill_priority),
                        profile_alignment=self._profile_alignment(
                            skill_priority,
                            area,
                            target_roles,
                            career_goal,
                            current_skills,
                        ),
                        expected_impact=self._expected_impact(skill_priority),
                        bucket=bucket,
                        impact=skill_priority.impact,
                    )
                )
                yield "   status: trilha definida\n\n"
            else:
                add_error(f"{skill}: nenhum material encontrado em busca externa nem na base interna")
                yield "   status: nenhum material encontrado\n\n"

        plan_items.sort(key=lambda item: ({"estudar agora": 0, "estudar depois": 1, "opcional": 2}[item.bucket], -item.impact, item.skill.casefold()))

        if not plan_items:
            yield "## RESPOSTA: CURATOR\n### estado\nerro\n\n"
            yield "### resumo\nNao encontrei materiais para as lacunas identificadas.\n\n"
            yield "### dados\n\n"
            yield "### erros\n"
            yield "\n".join(f"{index}. {error}" for index, error in enumerate(errors, 1))
            yield "\n"
            return

        yield "## RESPOSTA: CURATOR\n### estado\nsucesso\n\n"
        yield "### resumo\n"
        yield f"Transformei as lacunas do Scout em uma trilha pratica com {len(plan_items)} habilidade(s). A ordem considera recorrencia nas vagas, impacto no match e facilidade para gerar evidencia pratica no curriculo.\n"
        yield f"Contexto usado: area={area}; nivel={raw_level or 'nao informado'}; funcoes_alvo={target_roles or 'nao informado'}; objetivo={career_goal or 'nao informado'}.\n\n"
        if notices:
            yield "### avisos\n"
            for notice in notices:
                yield f"- {notice}\n"
            yield "\n"
        yield "### dados\n"

        for bucket in ["estudar agora", "estudar depois", "opcional"]:
            bucket_items = [item for item in plan_items if item.bucket == bucket]
            if not bucket_items:
                continue

            yield f"{bucket}:\n"
            for index, item in enumerate(bucket_items, 1):
                yield f"{index}. habilidade: {item.skill}\n"
                yield f"   prioridade: {item.priority}\n"
                yield f"   nivel_recomendado: {item.recommended_level}\n"
                yield f"   por_que_importa: {item.why_it_matters}\n"
                yield f"   alinhamento_com_perfil: {item.profile_alignment}\n"
                if item.free_resource:
                    yield f"   curso_gratuito_recomendado: {item.free_resource.name}\n"
                    yield f"   plataforma_gratuita: {item.free_resource.platform}\n"
                    yield f"   link_gratuito: {item.free_resource.link}\n"
                else:
                    yield "   curso_gratuito_recomendado: Nao encontrado automaticamente\n"
                    yield "   plataforma_gratuita: Nao informado\n"
                    yield "   link_gratuito: Nao informado\n"

                if item.paid_resource:
                    yield f"   curso_pago_acessivel_recomendado: {item.paid_resource.name}\n"
                    yield f"   plataforma_paga: {item.paid_resource.platform}\n"
                    yield "   preco_estimado: Consultar plataforma\n"
                    yield f"   link_pago: {item.paid_resource.link}\n"
                else:
                    yield "   curso_pago_acessivel_recomendado: Nao recomendado agora; alternativa gratuita suficiente ou nenhum curso acessivel confiavel encontrado\n"
                    yield "   plataforma_paga: Nao informado\n"
                    yield "   preco_estimado: Nao informado\n"
                    yield "   link_pago: Nao informado\n"

                if item.trusted_reference:
                    yield f"   documentacao_ou_referencia: {item.trusted_reference.name}\n"
                    yield f"   plataforma_referencia: {item.trusted_reference.platform}\n"
                    yield f"   link_referencia: {item.trusted_reference.link}\n"
                else:
                    yield "   documentacao_ou_referencia: Nao encontrada automaticamente\n"
                    yield "   plataforma_referencia: Nao informado\n"
                    yield "   link_referencia: Nao informado\n"

                if item.quick_content:
                    yield f"   conteudo_complementar_rapido: {item.quick_content.name}\n"
                    yield f"   plataforma_conteudo_rapido: {item.quick_content.platform}\n"
                    yield f"   link_conteudo_rapido: {item.quick_content.link}\n"
                else:
                    yield "   conteudo_complementar_rapido: Nao encontrado automaticamente\n"
                    yield "   plataforma_conteudo_rapido: Nao informado\n"
                    yield "   link_conteudo_rapido: Nao informado\n"

                yield f"   projeto_pratico: {item.project}\n"
                yield f"   tempo_estimado_estudo: {item.study_time}\n"
                yield f"   relacao_com_vagas: {item.relation_to_jobs}\n"
                yield f"   impacto_esperado_aderencia: {item.expected_impact}\n\n"

        yield "\n### erros\n"
        if errors:
            for index, error in enumerate(errors, 1):
                yield f"{index}. {error}\n"
        else:
            yield "Nenhum erro parcial.\n"
