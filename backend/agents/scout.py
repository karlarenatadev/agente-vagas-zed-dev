"""
Agente Scout — Busca de vagas de emprego via Firecrawl.

Fluxo:
1. Lê perfil do usuário
2. Executa firecrawl search para descobrir vagas
3. Executa firecrawl scrape para detalhes completos
4. Realiza correspondência de habilidades
5. Retorna até 5 vagas formatadas
"""

from __future__ import annotations

import asyncio
from collections import Counter
import os
import re
import time
from typing import AsyncGenerator

from agents.base import BaseAgent, LLMProviderError
from firecrawl_client import (
    FirecrawlCreditError,
    FirecrawlProviderError,
    firecrawl_scrape,
    firecrawl_search,
)


SCOUT_SYSTEM_PROMPT = """Você é o Scout, agente especializado em busca de vagas de emprego do sistema Recoloca IA.

Seu papel:
- Analisar o perfil do usuário
- Buscar vagas relevantes usando os dados fornecidos
- Realizar correspondência de habilidades técnicas e soft skills
- Retornar resultados formatados e úteis

Regras de formato:
- NUNCA use tabelas markdown
- Use listas numeradas com pares chave-valor
- Seja objetivo e preciso
- Se não encontrar dados, informe "Não informado"

Formato de saída obrigatório para cada vaga:
titulo: [título]
empresa: [empresa]
localizacao: [local]
salario: [salário ou "Não informado na descrição"]
beneficios: [benefícios ou "Não informado na descrição"]
link: [URL]
habilidades_correspondentes: [lista]
soft_skills_correspondentes: [lista]
habilidades_faltantes: [lista]
contagem_correspondencia: [X de Y habilidades correspondem]
dica_curriculo: [recomendação de 1 linha]"""


AREA_SKILL_MAP: dict[str, list[str]] = {
    "frontend": ["HTML", "CSS", "JavaScript", "TypeScript", "React", "Git", "Consumo de APIs"],
    "backend": ["Python", "Java", "APIs REST", "SQL", "Docker", "Git", "Testes"],
    "ciência de dados": ["Python", "SQL", "Excel", "Power BI", "Pandas", "Estatística", "Machine Learning"],
    "mobile": ["React Native", "Flutter", "Android", "iOS", "APIs REST", "Git"],
    "devops": ["Linux", "Docker", "Kubernetes", "AWS", "CI/CD", "Terraform", "Monitoramento"],
    "full stack": ["JavaScript", "TypeScript", "React", "Node.js", "SQL", "APIs REST", "Git"],
    "governança de dados": ["LGPD", "Catálogo de Dados", "Qualidade de Dados", "SQL", "Data Governance", "Compliance"],
    "design ux": ["Pesquisa com Usuários", "Figma", "Jornada do Usuário", "Prototipação", "Testes de Usabilidade"],
    "design ui": ["Figma", "Design System", "Prototipação", "Acessibilidade", "Interface Web"],
    "liderança": ["Gestão de Pessoas", "Scrum", "Comunicação", "Planejamento", "Métricas"],
    "rh": ["Recrutamento", "People Analytics", "Comunicação", "Entrevistas", "ATS"],
    "marketing de mídias sociais": ["Instagram", "Copywriting", "Calendário Editorial", "Métricas", "Canva"],
    "growth marketing": ["Google Analytics", "SEO", "CRO", "Mídia Paga", "Experimentos", "Funil"],
    "gestão de produtos": ["Discovery", "Roadmap", "Métricas de Produto", "Scrum", "Priorização"],
    "cibersegurança": ["Redes", "SIEM", "Linux", "Pentest", "Cloud Security", "Gestão de Vulnerabilidades"],
}

COMMON_SOFT_SKILLS = ["Comunicação", "Colaboração", "Resolução de problemas", "Organização"]

# Origens válidas de uma vaga. Toda job_entry precisa declarar exatamente uma
# delas antes de o relatório ser emitido (invariante de proveniência).
VALID_JOB_SOURCES: frozenset[str] = frozenset({"real", "llm", "simulated"})


class ScoutProvenanceError(RuntimeError):
    """Erro de domínio: uma vaga foi montada sem origem (`source`) válida.

    Bloqueia a emissão do relatório do Scout para impedir que dados sem
    proveniência definida cheguem ao usuário (Requisito 1.8).
    """

    public_message = (
        "Nao foi possivel montar o relatorio de vagas: origem dos dados "
        "indefinida. Tente novamente em instantes."
    )

# Filtro de recência escolhido no frontend → valor --tbs do Firecrawl.
# "all" (ou vazio) não aplica filtro e traz vagas de qualquer data.
DATE_FILTER_TBS: dict[str, str] = {
    "24h": "qdr:d",
    "7d": "qdr:w",
    "1m": "qdr:m",
}

FALLBACK_MESSAGES: dict[str, str] = {
    "firecrawl_error": "Nao conseguimos buscar vagas reais agora. Exibindo oportunidades simuladas.",
    "firecrawl_empty": "Nenhuma vaga real encontrada para esse filtro. Tente termos mais amplos. Exibindo oportunidades simuladas.",
    "firecrawl_timeout": "Nao conseguimos buscar vagas reais dentro do tempo limite. Exibindo oportunidades simuladas.",
    "firecrawl_no_credits": "Busca externa sem creditos agora. Exibindo oportunidades simuladas.",
}

# Mensagem para vagas geradas pelo LLM disponivel (ex.: MiMo) quando o Firecrawl
# nao retorna nada ou esta sem creditos. Sao SUGESTOES, nao vagas verificadas.
LLM_FALLBACK_MESSAGE = (
    "Sugestoes geradas por IA porque a busca externa nao retornou resultados ou "
    "esta sem creditos. Nao sao vagas reais verificadas — confirme antes de se candidatar."
)

# Mensagens de busca DEGRADADA: a busca específica (com nível/filtro) falhou por
# erro/timeout do Firecrawl, mas a busca ampla recuperou vagas REAIS. Diferente
# do fallback simulado — aqui as vagas existem, só não vieram da busca pedida.
# Sem isso, a falha parcial era engolida silenciosamente (search_status virava
# "real_success").
DEGRADED_MESSAGES: dict[str, str] = {
    "firecrawl_error": "A busca específica falhou no Firecrawl; estas vagas vêm de uma busca mais ampla e podem estar menos alinhadas ao seu filtro.",
    "firecrawl_timeout": "A busca específica excedeu o tempo limite; estas vagas vêm de uma busca mais ampla e podem estar menos alinhadas ao seu filtro.",
}

_SEARCH_CACHE: dict[str, tuple[float, list[dict[str, str]]]] = {}


def _env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return min(max(value, minimum), maximum)


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return min(max(value, minimum), maximum)


def _normalize_cache_key(query: str, tbs: str, limit: int) -> str:
    normalized_query = re.sub(r"\s+", " ", query.casefold()).strip()
    return f"{normalized_query}|{tbs}|{limit}"


class ScoutAgent(BaseAgent):
    """Agente de busca de vagas via Firecrawl SDK."""

    name = "Scout"

    def _firecrawl_timeout_seconds(self) -> float:
        return _env_float("FIRECRAWL_TIMEOUT_SECONDS", 15.0, 0.001, 120.0)

    def _firecrawl_max_results(self) -> int:
        return _env_int("FIRECRAWL_MAX_RESULTS", 5, 1, 20)

    def _firecrawl_cache_ttl_seconds(self) -> float:
        return _env_float("FIRECRAWL_CACHE_TTL_SECONDS", 600.0, 0.0, 3600.0)

    def _get_cached_search(self, query: str, tbs: str, limit: int) -> list[dict[str, str]] | None:
        ttl = self._firecrawl_cache_ttl_seconds()
        if ttl <= 0:
            return None

        key = _normalize_cache_key(query, tbs, limit)
        cached = _SEARCH_CACHE.get(key)
        if not cached:
            return None

        expires_at, results = cached
        if expires_at <= time.monotonic():
            _SEARCH_CACHE.pop(key, None)
            return None

        return [dict(item) for item in results]

    def _set_cached_search(self, query: str, tbs: str, limit: int, results: list[dict[str, str]]) -> None:
        ttl = self._firecrawl_cache_ttl_seconds()
        if ttl <= 0:
            return

        key = _normalize_cache_key(query, tbs, limit)
        _SEARCH_CACHE[key] = (
            time.monotonic() + ttl,
            [dict(item) for item in results[:limit]],
        )

    async def _run_firecrawl_search(self, query: str, tbs: str = "") -> tuple[list[dict[str, str]], str, bool]:
        limit = self._firecrawl_max_results()
        cached = self._get_cached_search(query, tbs, limit)
        if cached is not None:
            return cached, "" if cached else "firecrawl_empty", True

        try:
            results = await asyncio.wait_for(
                firecrawl_search(
                    query,
                    session_id=self.paths.session_id,
                    tbs=tbs,
                    limit=limit,
                ),
                timeout=self._firecrawl_timeout_seconds(),
            )
            limited_results = results[:limit]
            self._set_cached_search(query, tbs, limit, limited_results)
            return limited_results, "" if limited_results else "firecrawl_empty", False
        except asyncio.TimeoutError:
            return [], "firecrawl_timeout", False
        except FirecrawlCreditError:
            # Subclasse de FirecrawlProviderError: precisa vir antes para
            # distinguir falta de creditos de um erro generico.
            return [], "firecrawl_no_credits", False
        except FirecrawlProviderError:
            return [], "firecrawl_error", False

    async def _run_firecrawl_scrape(self, url: str) -> str:
        try:
            return await asyncio.wait_for(
                firecrawl_scrape(url, session_id=self.paths.session_id),
                timeout=self._firecrawl_timeout_seconds(),
            )
        except asyncio.TimeoutError:
            return ""
        except FirecrawlProviderError:
            return ""

    def _parse_profile(self, profile_text: str) -> dict[str, str]:
        """Extrai campos do perfil em dicionário."""
        data: dict[str, str] = {}
        for line in profile_text.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                data[key.strip()] = value.strip()
        return data

    def _match_skills(self, required: list[str], current: list[str]) -> tuple[list[str], list[str]]:
        """Compara habilidades requeridas com as do usuário (case-insensitive)."""
        current_lower = [s.lower().strip() for s in current]
        matched = []
        missing = []
        for skill in required:
            skill_lower = skill.lower().strip()
            if any(skill_lower == item or skill_lower in item or item in skill_lower for item in current_lower):
                matched.append(skill)
            else:
                missing.append(skill)
        return matched, missing

    def _area_skills(self, area: str) -> list[str]:
        area_key = area.lower().strip()
        return AREA_SKILL_MAP.get(area_key, ["Git", "Comunicação", "Resolução de problemas", "SQL", "Excel"])

    def _target_roles(self, profile: dict[str, str], area: str) -> list[str]:
        roles_raw = profile.get("Funções alvo", "")
        roles = [role.strip() for role in roles_raw.split(",") if role.strip()]
        if roles:
            return roles
        return [f"Profissional de {area}", f"Analista de {area}", f"Especialista de {area}"]

    def _score_opportunity(
        self,
        matched_tech: list[str],
        required_tech: list[str],
        matched_soft: list[str],
        required_soft: list[str],
        level: str,
        title: str,
    ) -> int:
        tech_score = (len(matched_tech) / len(required_tech)) * 70 if required_tech else 35
        soft_score = (len(matched_soft) / len(required_soft)) * 20 if required_soft else 10
        level_score = 10 if not level or level.lower() in title.lower() else 5
        return min(100, round(tech_score + soft_score + level_score))

    def _priority_from_score(self, score: int) -> str:
        if score >= 75:
            return "Alta"
        if score >= 50:
            return "Média"
        return "Baixa"

    def _resume_tip(self, matched: list[str], missing: list[str], area: str) -> str:
        if matched:
            return f"Destaque evidências práticas de {matched[0]} e conecte essa experiência a resultados."
        if missing:
            return f"Mostre projetos ou estudos recentes ligados a {missing[0]} para reduzir a lacuna principal."
        return f"Organize o currículo com projetos e resultados ligados a {area}."

    def _build_job_entry(
        self,
        *,
        title: str,
        company: str,
        location: str,
        salary: str,
        benefits: str,
        link: str,
        required_skills: list[str],
        required_soft: list[str],
        current_skills: list[str],
        current_soft: list[str],
        level: str,
        area: str,
        tip: str = "",
        source: str = "real",
        fallback_reason: str = "",
        fallback_message: str = "",
    ) -> dict[str, str | list[str] | int]:
        matched_tech, missing_tech = self._match_skills(required_skills, current_skills)
        matched_soft, _ = self._match_skills(required_soft, current_soft)
        score = self._score_opportunity(matched_tech, required_skills, matched_soft, required_soft, level, title)

        return {
            "titulo": title,
            "source": source,
            "fallback_reason": fallback_reason,
            "fallback_message": fallback_message,
            "empresa": company,
            "localizacao": location,
            "salario": salary,
            "beneficios": benefits,
            "link": link,
            "score_aderencia": score,
            "prioridade_candidatura": self._priority_from_score(score),
            "habilidades_correspondentes": ", ".join(matched_tech) or "Nenhuma",
            "soft_skills_correspondentes": ", ".join(matched_soft) or "Nenhuma",
            "habilidades_faltantes": ", ".join(missing_tech) or "Nenhuma",
            "contagem_correspondencia": f"{len(matched_tech)} de {len(required_skills)} habilidades correspondem",
            "dica_curriculo": tip or self._resume_tip(matched_tech, missing_tech, area),
            "_required_skills": required_skills,
        }

    def _simulate_opportunities(
        self,
        profile: dict[str, str],
        current_skills: list[str],
        current_soft: list[str],
        fallback_reason: str,
    ) -> list[dict[str, str | list[str] | int]]:
        area = profile.get("Área de interesse", "Tecnologia")
        location = profile.get("Localização", "Remoto")
        level = profile.get("Nível de experiência", "")
        roles = self._target_roles(profile, area)
        base_skills = self._area_skills(area)
        soft = current_soft[:2] + [skill for skill in COMMON_SOFT_SKILLS if skill not in current_soft]

        templates = [
            ("Núcleo Digital", roles[0], base_skills[:5], soft[:3], "Alta se você já tiver projetos práticos no portfólio."),
            ("DataBridge Labs", roles[min(1, len(roles) - 1)], base_skills[1:6], soft[1:4], "Média a alta; boa vaga para reforçar experiência aplicada."),
            ("Vetor Consultoria", roles[min(2, len(roles) - 1)], base_skills[2:] + base_skills[:1], soft[:3], "Média; priorize após ajustar lacunas técnicas principais."),
        ]

        opportunities = []
        for company, role, required, required_soft, priority_note in templates:
            title = f"{role} {level}".strip()
            entry = self._build_job_entry(
                title=title,
                company=company,
                location=location or "Remoto",
                salary="Não informado na descrição",
                benefits="Não informado na descrição",
                link="Oportunidade simulada a partir do perfil",
                required_skills=required,
                required_soft=required_soft,
                current_skills=current_skills,
                current_soft=current_soft,
                level=level,
                area=area,
                source="simulated",
                fallback_reason=fallback_reason,
                fallback_message=FALLBACK_MESSAGES.get(fallback_reason, ""),
            )
            entry["prioridade_candidatura"] = f"{entry['prioridade_candidatura']} - {priority_note}"
            opportunities.append(entry)
        return opportunities

    @staticmethod
    def _split_llm_blocks(raw: str) -> list[str]:
        """Quebra a resposta do LLM em blocos, um por vaga.

        Prefere o separador explicito "---"; se ausente, quebra antes de cada
        "titulo:". So mantem blocos que contenham um titulo.
        """
        text = (raw or "").strip()
        if not text:
            return []
        if re.search(r"^\s*-{3,}\s*$", text, re.MULTILINE):
            parts = re.split(r"^\s*-{3,}\s*$", text, flags=re.MULTILINE)
        else:
            parts = re.split(r"\n(?=\s*titulo\s*:)", text, flags=re.IGNORECASE)
        return [part.strip() for part in parts if "titulo" in part.lower()]

    async def _llm_opportunities(
        self,
        profile: dict[str, str],
        current_skills: list[str],
        current_soft: list[str],
        area: str,
        location: str,
        level: str,
        fallback_reason: str,
    ) -> list[dict[str, str | list[str] | int]]:
        """Fallback via LLM: usa o modelo disponivel (ex.: MiMo) para sugerir
        vagas coerentes com o perfil quando o Firecrawl nao retorna nada ou esta
        sem creditos. Retorna lista vazia se o LLM falhar ou nao for parseavel —
        nesse caso o chamador cai na simulacao deterministica.
        """
        roles_hint = ", ".join(self._target_roles(profile, area)[:3])
        skills_str = ", ".join(current_skills) or "nao informado"
        soft_str = ", ".join(current_soft) or "nao informado"

        prompt = f"""A busca externa de vagas esta indisponivel. Gere EXATAMENTE 3 oportunidades de emprego realistas e coerentes com o perfil abaixo, para orientar a estrategia de candidatura.

Estas sao SUGESTOES geradas por voce (IA), NAO vagas reais verificadas. Seja plausivel para o mercado brasileiro.

Perfil:
- Area: {area}
- Nivel: {level or "nao informado"}
- Localizacao: {location or "Remoto"}
- Funcoes alvo: {roles_hint}
- Habilidades atuais: {skills_str}
- Soft skills: {soft_str}

Para CADA oportunidade use EXATAMENTE este formato, separando cada uma com uma linha contendo apenas "---":
titulo: [cargo, coerente com o nivel]
empresa: [nome plausivel ou "Empresa de referencia"]
localizacao: [respeite a preferencia do perfil; use "Remoto" se fizer sentido]
salario: [faixa realista em R$ para o mercado brasileiro ou "Nao informado"]
beneficios: [principais beneficios ou "Nao informado"]
habilidades_requeridas: [3 a 6 habilidades tecnicas separadas por virgula]
soft_skills_requeridas: [2 a 4 soft skills separadas por virgula]
dica_curriculo: [1 frase do que destacar no curriculo para esta vaga]

Regras: sem markdown, sem numeracao, sem texto fora do formato."""

        try:
            raw = await self.call_llm(SCOUT_SYSTEM_PROMPT, prompt)
        except LLMProviderError:
            return []

        opportunities: list[dict[str, str | list[str] | int]] = []
        for block in self._split_llm_blocks(raw):
            data: dict[str, str] = {}
            for line in block.splitlines():
                if ":" in line:
                    key, _, value = line.partition(":")
                    data[key.strip().lower()] = value.strip()

            title = data.get("titulo", "").strip()
            if not title:
                continue

            req_skills = [s.strip() for s in data.get("habilidades_requeridas", "").split(",") if s.strip()]
            req_soft = [s.strip() for s in data.get("soft_skills_requeridas", "").split(",") if s.strip()]
            if not req_skills:
                req_skills = self._area_skills(area)[:5]
            if not req_soft:
                req_soft = COMMON_SOFT_SKILLS[:3]

            entry = self._build_job_entry(
                title=title,
                company=data.get("empresa") or "Nao informado",
                location=data.get("localizacao") or location or "Remoto",
                salary=data.get("salario") or "Nao informado na descricao",
                benefits=data.get("beneficios") or "Nao informado na descricao",
                # Link textual proposital: nunca uma URL, para o frontend nao
                # apresentar como vaga real clicavel (evita link alucinado).
                link="Sugestao gerada por IA (nao verificada)",
                required_skills=req_skills[:6],
                required_soft=req_soft[:4],
                current_skills=current_skills,
                current_soft=current_soft,
                level=level,
                area=area,
                tip=data.get("dica_curriculo", ""),
                source="llm",
                fallback_reason=fallback_reason,
                fallback_message=LLM_FALLBACK_MESSAGE,
            )
            opportunities.append(entry)
            if len(opportunities) >= 3:
                break

        return opportunities

    def _recurring_requirements(self, jobs: list[dict[str, str | list[str] | int]]) -> list[tuple[str, int]]:
        counter: Counter[str] = Counter()
        canonical: dict[str, str] = {}
        for job in jobs:
            for skill in job.get("_required_skills", []):
                if not isinstance(skill, str):
                    continue
                key = skill.lower().strip()
                canonical[key] = skill
                counter[key] += 1
        return [(canonical[key], count) for key, count in counter.most_common(6)]

    def _assert_job_provenance(self, jobs: list[dict[str, str | list[str] | int]]) -> None:
        """Valida a invariante de proveniência antes de emitir o relatório.

        - Toda vaga precisa de `source` em {real, llm, simulated} (Req. 1.1, 1.8).
        - `source == "real"` mantém os campos de fallback vazios (Req. 1.6).
        - `source` em {llm, simulated} preenche motivo e mensagem (Req. 1.5).

        Levanta ScoutProvenanceError (erro de domínio controlado) caso a
        invariante seja violada, bloqueando a geração do relatório.
        """
        for job in jobs:
            title = job.get("titulo", "sem titulo")
            source = job.get("source")
            if source not in VALID_JOB_SOURCES:
                raise ScoutProvenanceError(
                    f"Vaga '{title}' sem origem valida: {source!r}."
                )

            fallback_reason = job.get("fallback_reason", "")
            fallback_message = job.get("fallback_message", "")
            if source == "real":
                if fallback_reason or fallback_message:
                    raise ScoutProvenanceError(
                        f"Vaga real '{title}' nao pode ter campos de fallback preenchidos."
                    )
            elif not fallback_reason or not fallback_message:
                raise ScoutProvenanceError(
                    f"Vaga '{title}' com origem '{source}' precisa de "
                    "fallback_reason e fallback_message preenchidos."
                )

    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        """
        Executa busca de vagas.
        context: {'profile': str, 'date_filter': str}
        """
        profile_text = context.get("profile", "")
        profile = self._parse_profile(profile_text)

        area = profile.get("Área de interesse", "tecnologia")
        location = profile.get("Localização", "Brasil")
        level = profile.get("Nível de experiência", "")
        skills_raw = profile.get("Habilidades atuais", "")
        soft_skills_raw = profile.get("Soft skills", "")

        date_filter = (context.get("date_filter") or "").strip()
        tbs = DATE_FILTER_TBS.get(date_filter, "")

        current_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
        current_soft = [s.strip() for s in soft_skills_raw.split(",") if s.strip()]

        period_label = {
            "24h": " (últimas 24h)",
            "7d": " (últimos 7 dias)",
            "1m": " (último mês)",
        }.get(date_filter, "")
        yield f"🔍 Buscando vagas de **{area}** em **{location}**{period_label}...\n\n"

        yield "Buscando vagas reais...\nIsso pode levar alguns segundos.\n\n"

        # Monta query de busca
        query = f"vagas {area} {level} {location}".strip()
        max_results = self._firecrawl_max_results()
        search_results, fallback_reason, cache_hit = await self._run_firecrawl_search(query, tbs)
        search_status = "real_success" if search_results else "real_empty"
        # Motivo da 1ª query (específica), preservado antes de tentar a ampla.
        primary_reason = fallback_reason
        degraded_reason = ""

        if not search_results:
            # Tenta query mais ampla
            query_broad = f"vagas {area} {location}"
            broad_results, broad_fallback_reason, broad_cache_hit = await self._run_firecrawl_search(query_broad, tbs)
            cache_hit = cache_hit or broad_cache_hit
            if broad_results:
                search_results = broad_results
                fallback_reason = ""
                # A busca específica falhou (erro/timeout) e só a ampla retornou:
                # vagas reais, porém em modo degradado. Não silenciar a falha.
                if primary_reason in ("firecrawl_error", "firecrawl_timeout"):
                    degraded_reason = primary_reason
                    search_status = "real_degraded"
                else:
                    search_status = "real_success"
            elif "firecrawl_no_credits" in {fallback_reason, broad_fallback_reason}:
                fallback_reason = "firecrawl_no_credits"
                search_status = "no_credits"
            elif "firecrawl_error" in {fallback_reason, broad_fallback_reason}:
                fallback_reason = "firecrawl_error"
                search_status = "external_error"
            elif "firecrawl_timeout" in {fallback_reason, broad_fallback_reason}:
                fallback_reason = "firecrawl_timeout"
                search_status = "timeout"
            else:
                fallback_reason = "firecrawl_empty"
                search_status = "real_empty"

        llm_mode = False
        simulated_mode = False
        if not search_results:
            # 1) Fallback primario: usa o LLM disponivel (ex.: MiMo) como
            # "ferramenta" para sugerir oportunidades coerentes com o perfil
            # quando o Firecrawl nao retorna nada ou esta sem creditos.
            yield "🤖 Busca externa indisponível. Acionando o assistente de IA para sugerir oportunidades compatíveis com seu perfil...\n\n"
            jobs_output = await self._llm_opportunities(
                profile, current_skills, current_soft, area, location, level, fallback_reason
            )
            if jobs_output:
                llm_mode = True
            else:
                # 2) Ultimo recurso: oportunidades simuladas deterministicas.
                simulated_mode = True
                yield "⚠ O assistente de IA não retornou sugestões agora. Exibindo oportunidades simuladas a partir do seu perfil.\n\n"
                jobs_output = self._simulate_opportunities(profile, current_skills, current_soft, fallback_reason)
        else:
            jobs_output = []
            yield f"✓ {len(search_results)} vagas encontradas. Analisando detalhes...\n\n"

        # Processa até 5 vagas reais quando a busca retorna resultados. Em modo
        # de fallback (LLM/simulado) search_results está vazio, então o laço
        # naturalmente não executa.
        for i, job in enumerate(search_results[:max_results]):
            url = job.get("url", "")
            title = job.get("titulo", job.get("title", "Título não informado"))
            description = job.get("descricao", job.get("description", ""))

            yield f"  [{i+1}/5] Analisando: {title[:50]}...\n"

            # Tenta scrape para detalhes completos
            full_desc = await self._run_firecrawl_scrape(url) if url else ""
            if not full_desc:
                full_desc = description

            # Usa LLM para extrair habilidades e dados estruturados da descrição
            extraction_prompt = f"""Analise esta descrição de vaga e extraia as informações solicitadas.

Descrição da vaga:
{full_desc[:3000]}

Perfil do candidato:
- Habilidades técnicas: {skills_raw}
- Soft skills: {soft_skills_raw}

Extraia e retorne EXATAMENTE neste formato (sem markdown extra):
empresa: [nome da empresa ou "Não informado"]
localizacao: [cidade/estado ou "Remoto" ou "Não informado"]
salario: [faixa salarial ou "Não informado na descrição"]
beneficios: [lista de benefícios ou "Não informado na descrição"]
habilidades_requeridas: [lista separada por vírgulas]
soft_skills_requeridas: [lista separada por vírgulas]
dica_curriculo: [1 frase sobre o que destacar no currículo para esta vaga]"""

            try:
                extracted = await self.call_llm(SCOUT_SYSTEM_PROMPT, extraction_prompt)
            except LLMProviderError:
                extracted = ""

            # Parse do resultado extraído
            extracted_data: dict[str, str] = {}
            for line in extracted.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    extracted_data[k.strip()] = v.strip()

            req_skills = [s.strip() for s in extracted_data.get("habilidades_requeridas", "").split(",") if s.strip()]
            req_soft = [s.strip() for s in extracted_data.get("soft_skills_requeridas", "").split(",") if s.strip()]
            if not req_skills:
                req_skills = self._area_skills(area)[:5]
            if not req_soft:
                req_soft = COMMON_SOFT_SKILLS[:3]

            job_entry = self._build_job_entry(
                title=title,
                company=extracted_data.get("empresa", "Não informado"),
                location=extracted_data.get("localizacao", "Não informado"),
                salary=extracted_data.get("salario") or "Não informado na descrição",
                benefits=extracted_data.get("beneficios") or "Não informado na descrição",
                link=url or "Não informado",
                required_skills=req_skills,
                required_soft=req_soft,
                current_skills=current_skills,
                current_soft=current_soft,
                level=level,
                area=area,
                tip=extracted_data.get("dica_curriculo", ""),
            )
            jobs_output.append(job_entry)

        jobs_output = sorted(jobs_output, key=lambda item: int(item["score_aderencia"]), reverse=True)
        recurring = self._recurring_requirements(jobs_output)

        # Invariante de proveniência: nenhuma vaga pode chegar ao relatório sem
        # origem (`source`) válida e com campos de fallback coerentes. Bloqueia a
        # emissão do relatório caso contrário (Req. 1.1, 1.5, 1.6, 1.8).
        self._assert_job_provenance(jobs_output)

        # Formata saída final. Degradada (real, via busca ampla) também é "parcial".
        response_state = "parcial" if (simulated_mode or llm_mode or degraded_reason) else "sucesso"
        yield f"\n## RESPOSTA: SCOUT\n### estado\n{response_state}\n\n"
        if llm_mode:
            source_label = "sugestões geradas por IA"
        elif simulated_mode:
            source_label = "oportunidades simuladas"
        else:
            source_label = "vagas encontradas"
        yield (
            f"### resumo\nAnalisei {len(jobs_output)} {source_label} para **{area}** em **{location}**. "
            "Abaixo estão os matches com score de aderência, lacunas, requisitos recorrentes e prioridade de candidatura.\n\n"
        )
        busca_degradada = bool(degraded_reason)
        fallback_active = simulated_mode or llm_mode
        if llm_mode:
            fallback_message = LLM_FALLBACK_MESSAGE
        elif simulated_mode:
            fallback_message = FALLBACK_MESSAGES.get(fallback_reason, "")
        else:
            fallback_message = ""
        yield "### dados\n\n"
        yield f"status_busca: {search_status}\n"
        yield f"fallback_simulado: {str(simulated_mode).lower()}\n"
        yield f"fallback_llm: {str(llm_mode).lower()}\n"
        yield f"fallback_reason: {fallback_reason if fallback_active else ''}\n"
        yield f"fallback_message: {fallback_message}\n"
        yield f"busca_degradada: {str(busca_degradada).lower()}\n"
        yield f"aviso_degradacao: {DEGRADED_MESSAGES.get(degraded_reason, '') if busca_degradada else ''}\n"
        yield f"cache_hit: {str(cache_hit).lower()}\n"
        yield f"max_resultados: {max_results}\n\n"
        yield "requisitos_mais_recorrentes:\n"
        if recurring:
            for index, (skill, count) in enumerate(recurring, 1):
                yield f"{index}. requisito: {skill}\n"
                yield f"   ocorrencias: {count}\n"
        else:
            yield "1. requisito: Não informado\n"
            yield "   ocorrencias: 0\n"
        yield "\n"

        yield "vagas_compativeis:\n"

        for i, job in enumerate(jobs_output, 1):
            yield f"{i}. titulo: {job['titulo']}\n"
            yield f"   source: {job['source']}\n"
            yield f"   fallback_reason: {job['fallback_reason']}\n"
            yield f"   fallback_message: {job['fallback_message']}\n"
            yield f"   empresa: {job['empresa']}\n"
            yield f"   localizacao: {job['localizacao']}\n"
            yield f"   salario: {job['salario']}\n"
            yield f"   beneficios: {job['beneficios']}\n"
            yield f"   link: {job['link']}\n"
            yield f"   score_aderencia: {job['score_aderencia']}/100\n"
            yield f"   prioridade_candidatura: {job['prioridade_candidatura']}\n"
            yield f"   habilidades_correspondentes: {job['habilidades_correspondentes']}\n"
            yield f"   soft_skills_correspondentes: {job['soft_skills_correspondentes']}\n"
            yield f"   habilidades_faltantes: {job['habilidades_faltantes']}\n"
            yield f"   contagem_correspondencia: {job['contagem_correspondencia']}\n"
            yield f"   dica_curriculo: {job['dica_curriculo']}\n\n"
