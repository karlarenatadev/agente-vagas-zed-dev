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

import json
import os
import shutil
import subprocess
from collections import Counter
from typing import AsyncGenerator

import config
from agents.base import BaseAgent, LLMProviderError


def _firecrawl_env() -> dict[str, str]:
    """Ambiente para o subprocess do firecrawl, garantindo a API key.

    O subprocess herda o ambiente do backend, mas se o servidor foi iniciado
    sem FIRECRAWL_API_KEY exportada, injetamos a chave lida do backend/.env
    via config para que o CLI autentique e não retorne vazio (modo simulado).
    """
    env = os.environ.copy()
    if config.FIRECRAWL_API_KEY:
        env["FIRECRAWL_API_KEY"] = config.FIRECRAWL_API_KEY
    return env


def _firecrawl_executable() -> str | None:
    """Resolve o caminho real do CLI firecrawl.

    No Windows, subprocess.run(["firecrawl", ...]) sem shell=True usa
    CreateProcess, que não resolve extensões via PATHEXT — então "firecrawl"
    (que é firecrawl.cmd) levanta FileNotFoundError e o Scout caía no modo
    simulado. shutil.which respeita PATHEXT e acha o .cmd/.exe correto.
    """
    return shutil.which("firecrawl")


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

# Filtro de recência escolhido no frontend → valor --tbs do Firecrawl.
# "all" (ou vazio) não aplica filtro e traz vagas de qualquer data.
DATE_FILTER_TBS: dict[str, str] = {
    "24h": "qdr:d",
    "7d": "qdr:w",
    "1m": "qdr:m",
}


class ScoutAgent(BaseAgent):
    """Agente de busca de vagas — usa Firecrawl CLI ou SDK."""

    name = "Scout"

    def _run_firecrawl_search(self, query: str, tbs: str = "") -> list[dict]:
        """Executa firecrawl search via CLI e retorna resultados JSON.

        tbs: filtro de recência do Google (qdr:d/w/m). Vazio = sem filtro.
        """
        executable = _firecrawl_executable()
        if not executable:
            return []
        args = [executable, "search", query, "--json"]
        if tbs:
            args += ["--tbs", tbs]
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                env=_firecrawl_env(),
            )
            if result.returncode == 0 and result.stdout:
                parsed = json.loads(result.stdout)
                
                # Firecrawl retorna {"success":true,"data":{"web":[...]}}
                if isinstance(parsed, dict):
                    # Novo formato: {"success": true, "data": {"web": [...]}}
                    if "data" in parsed and isinstance(parsed["data"], dict):
                        web_results = parsed["data"].get("web", [])
                        if isinstance(web_results, list):
                            return web_results
                    # Formato alternativo: {"data": [...]}
                    data = parsed.get("data") or parsed.get("results") or parsed.get("items")
                    if isinstance(data, list):
                        return data
                
                # Formato legado: lista direta
                if isinstance(parsed, list):
                    return parsed
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
        return []

    def _run_firecrawl_scrape(self, url: str) -> str:
        """Executa firecrawl scrape via CLI e retorna markdown."""
        executable = _firecrawl_executable()
        if not executable:
            return ""
        try:
            result = subprocess.run(
                [executable, "scrape", url, "--format", "markdown"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                env=_firecrawl_env(),
            )
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
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
    ) -> dict[str, str | list[str] | int]:
        matched_tech, missing_tech = self._match_skills(required_skills, current_skills)
        matched_soft, _ = self._match_skills(required_soft, current_soft)
        score = self._score_opportunity(matched_tech, required_skills, matched_soft, required_soft, level, title)

        return {
            "titulo": title,
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
            )
            entry["prioridade_candidatura"] = f"{entry['prioridade_candidatura']} - {priority_note}"
            opportunities.append(entry)
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

        # Monta query de busca
        query = f"vagas {area} {level} {location}".strip()
        search_results = self._run_firecrawl_search(query, tbs)

        if not search_results:
            # Tenta query mais ampla
            query_broad = f"vagas {area} {location}"
            search_results = self._run_firecrawl_search(query_broad, tbs)

        simulated_mode = False
        if not search_results:
            simulated_mode = True
            yield "⚠ Nenhum resultado real retornado pelo Firecrawl. Vou simular oportunidades compatíveis com seu perfil para orientar a estratégia.\n\n"
            jobs_output = self._simulate_opportunities(profile, current_skills, current_soft)
        else:
            jobs_output = []
            yield f"✓ {len(search_results)} vagas encontradas. Analisando detalhes...\n\n"

        # Processa até 5 vagas reais quando a busca retorna resultados.
        for i, job in enumerate(search_results[:5] if not simulated_mode else []):
            url = job.get("url", "")
            title = job.get("titulo", job.get("title", "Título não informado"))
            description = job.get("descricao", job.get("description", ""))

            yield f"  [{i+1}/5] Analisando: {title[:50]}...\n"

            # Tenta scrape para detalhes completos
            full_desc = self._run_firecrawl_scrape(url) if url else ""
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
                salary=extracted_data.get("salario", "Não informado na descrição"),
                benefits=extracted_data.get("beneficios", "Não informado na descrição"),
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

        # Formata saída final
        yield "\n## RESPOSTA: SCOUT\n### estado\nsucesso\n\n"
        source_label = "oportunidades simuladas" if simulated_mode else "vagas encontradas"
        yield (
            f"### resumo\nAnalisei {len(jobs_output)} {source_label} para **{area}** em **{location}**. "
            "Abaixo estão os matches com score de aderência, lacunas, requisitos recorrentes e prioridade de candidatura.\n\n"
        )
        yield "### dados\n\n"
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
