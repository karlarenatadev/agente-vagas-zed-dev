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
import subprocess
from typing import AsyncGenerator

import config
from agents.base import BaseAgent


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


class ScoutAgent(BaseAgent):
    """Agente de busca de vagas — usa Firecrawl CLI ou SDK."""

    name = "Scout"

    def _run_firecrawl_search(self, query: str) -> list[dict]:
        """Executa firecrawl search via CLI e retorna resultados JSON."""
        try:
            result = subprocess.run(
                ["firecrawl", "search", query, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout:
                return json.loads(result.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
        return []

    def _run_firecrawl_scrape(self, url: str) -> str:
        """Executa firecrawl scrape via CLI e retorna markdown."""
        try:
            result = subprocess.run(
                ["firecrawl", "scrape", url, "--format", "markdown"],
                capture_output=True,
                text=True,
                timeout=30,
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
            if skill.lower().strip() in current_lower:
                matched.append(skill)
            else:
                missing.append(skill)
        return matched, missing

    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        """
        Executa busca de vagas.
        context: {'profile': str}
        """
        profile_text = context.get("profile", "")
        profile = self._parse_profile(profile_text)

        area = profile.get("Área de interesse", "tecnologia")
        location = profile.get("Localização", "Brasil")
        level = profile.get("Nível de experiência", "")
        skills_raw = profile.get("Habilidades atuais", "")
        soft_skills_raw = profile.get("Soft skills", "")

        current_skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
        current_soft = [s.strip() for s in soft_skills_raw.split(",") if s.strip()]

        yield f"🔍 Buscando vagas de **{area}** em **{location}**...\n\n"

        # Monta query de busca
        query = f"vagas {area} {level} {location}".strip()
        search_results = self._run_firecrawl_search(query)

        if not search_results:
            # Tenta query mais ampla
            query_broad = f"vagas {area} {location}"
            search_results = self._run_firecrawl_search(query_broad)

        if not search_results:
            yield "⚠ Nenhuma vaga encontrada. Tente ampliar os termos de busca.\n"
            yield "\n## RESPOSTA: SCOUT\n### estado\nerro\n### erros\nNenhum resultado retornado pelo Firecrawl para a query fornecida.\n"
            return

        yield f"✓ {len(search_results)} vagas encontradas. Analisando detalhes...\n\n"

        # Processa até 5 vagas
        jobs_output = []
        for i, job in enumerate(search_results[:5]):
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

            extracted = await self.call_llm(SCOUT_SYSTEM_PROMPT, extraction_prompt)

            # Parse do resultado extraído
            extracted_data: dict[str, str] = {}
            for line in extracted.splitlines():
                if ":" in line:
                    k, _, v = line.partition(":")
                    extracted_data[k.strip()] = v.strip()

            req_skills = [s.strip() for s in extracted_data.get("habilidades_requeridas", "").split(",") if s.strip()]
            req_soft = [s.strip() for s in extracted_data.get("soft_skills_requeridas", "").split(",") if s.strip()]

            matched_tech, missing_tech = self._match_skills(req_skills, current_skills)
            matched_soft, _ = self._match_skills(req_soft, current_soft)

            total = len(req_skills)
            match_count = len(matched_tech)

            job_entry = {
                "titulo": title,
                "empresa": extracted_data.get("empresa", "Não informado"),
                "localizacao": extracted_data.get("localizacao", "Não informado"),
                "salario": extracted_data.get("salario", "Não informado na descrição"),
                "beneficios": extracted_data.get("beneficios", "Não informado na descrição"),
                "link": url,
                "habilidades_correspondentes": ", ".join(matched_tech) or "Nenhuma",
                "soft_skills_correspondentes": ", ".join(matched_soft) or "Nenhuma",
                "habilidades_faltantes": ", ".join(missing_tech) or "Nenhuma",
                "contagem_correspondencia": f"{match_count} de {total} habilidades correspondem",
                "dica_curriculo": extracted_data.get("dica_curriculo", "Destaque suas habilidades mais relevantes"),
            }
            jobs_output.append(job_entry)

        # Formata saída final
        yield "\n## RESPOSTA: SCOUT\n### estado\nsucesso\n\n"
        yield f"### resumo\nEncontrei {len(jobs_output)} vagas para **{area}** em **{location}**. Aqui estão os resultados com análise de correspondência de habilidades.\n\n"
        yield "### dados\n\n"

        for i, job in enumerate(jobs_output, 1):
            yield f"{i}. titulo: {job['titulo']}\n"
            yield f"   empresa: {job['empresa']}\n"
            yield f"   localizacao: {job['localizacao']}\n"
            yield f"   salario: {job['salario']}\n"
            yield f"   beneficios: {job['beneficios']}\n"
            yield f"   link: {job['link']}\n"
            yield f"   habilidades_correspondentes: {job['habilidades_correspondentes']}\n"
            yield f"   soft_skills_correspondentes: {job['soft_skills_correspondentes']}\n"
            yield f"   habilidades_faltantes: {job['habilidades_faltantes']}\n"
            yield f"   contagem_correspondencia: {job['contagem_correspondencia']}\n"
            yield f"   dica_curriculo: {job['dica_curriculo']}\n\n"
