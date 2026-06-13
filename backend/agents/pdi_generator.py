"""Geração heurística de PDI a partir de lacunas reais de uma vaga."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


INVALID_MARKERS = {
    "",
    "aguardando análise válida",
    "aguardando comparação",
    "não calculado",
    "não identificado",
    "não analisado",
    "não analisada",
    "nenhum item",
    "nenhuma análise realizada",
    "nenhuma comparação realizada",
    "nenhuma sugestão gerada",
}

RESOURCE_MAP: dict[str, tuple[str, str]] = {
    "AWS": ("AWS Skill Builder", "https://skillbuilder.aws/"),
    "APIs": ("MDN - Fetch API", "https://developer.mozilla.org/pt-BR/docs/Web/API/Fetch_API"),
    "Docker": ("Docker Get Started", "https://docs.docker.com/get-started/"),
    "ETL": ("Microsoft Learn - ETL", "https://learn.microsoft.com/training/"),
    "Excel": ("Microsoft Learn - Excel", "https://support.microsoft.com/excel"),
    "Git": ("GitHub Skills", "https://skills.github.com/"),
    "JavaScript": ("MDN JavaScript", "https://developer.mozilla.org/pt-BR/docs/Web/JavaScript"),
    "Power BI": ("Microsoft Learn - Power BI", "https://learn.microsoft.com/training/powerplatform/power-bi"),
    "Python": ("Python Tutorial", "https://docs.python.org/pt-br/3/tutorial/"),
    "React": ("React Learn", "https://react.dev/learn"),
    "SQL": ("PostgreSQL Tutorial", "https://www.postgresql.org/docs/current/tutorial.html"),
    "TypeScript": ("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html"),
}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", normalized.casefold()).strip()


def _unique(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        clean = re.sub(r"\s+", " ", item).strip(" \t:;,.")
        key = _normalize(clean)
        if key in INVALID_MARKERS or key in seen:
            continue
        seen.add(key)
        result.append(clean)
    return result


def _parse_markdown(content: str) -> dict[str, Any]:
    data: dict[str, Any] = {"raw": content}
    current_section = ""
    lines = content.splitlines()

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("## "):
            current_section = _normalize(line[3:]).replace(" ", "_")
            data.setdefault(current_section, [])
            continue

        plain_heading = _normalize(line.rstrip(":"))
        if line.endswith(":") and not line.startswith(("*", "-")):
            current_section = plain_heading.replace(" ", "_")
            data.setdefault(current_section, [])
            next_value = next(
                (
                    candidate.strip()
                    for candidate in lines[index + 1 :]
                    if candidate.strip()
                ),
                "",
            )
            if not next_value.startswith(("-", "*", "#")):
                data[current_section] = next_value
            continue

        if line.startswith(("* ", "- ")):
            value = line[2:].strip()
            if ":" in value and current_section in {"resumo", "resumo_da_analise"}:
                key, _, field_value = value.partition(":")
                data[_normalize(key).replace(" ", "_")] = field_value.strip()
            elif current_section:
                section = data.setdefault(current_section, [])
                if isinstance(section, list):
                    section.append(value)

    return data


def _list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    return _unique(value if isinstance(value, list) else [str(value)])


def _value(data: dict[str, Any], key: str, fallback: str) -> str:
    value = data.get(key, fallback)
    if isinstance(value, list):
        value = value[0] if value else fallback
    return str(value) if _normalize(str(value)) not in INVALID_MARKERS else fallback


def _skill_from_sentence(value: str) -> str:
    patterns = (
        r"com\s+([^;]+?)(?:;|$)",
        r"em\s+(.+?)\s+sem evid",
        r"^([^()]+?)\s+\(",
    )
    for pattern in patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" .")
    return value.strip(" .")


def validate_resume_analysis(content: str) -> bool:
    parsed = _parse_markdown(content)
    return bool(
        _list(parsed, "habilidades_tecnicas_detectadas")
        or _list(parsed, "soft_skills_detectadas")
    )


def validate_job_analysis(content: str) -> bool:
    parsed = _parse_markdown(content)
    return bool(
        _list(parsed, "hard_skills")
        or _list(parsed, "ferramentas")
        or _list(parsed, "palavras-chave_principais")
    )


def validate_match_report(content: str) -> bool:
    parsed = _parse_markdown(content)
    return bool(
        re.match(r"^\d{1,3}/100$", _value(parsed, "score_geral", ""))
        and (
            _list(parsed, "evidencias_fortes_no_curriculo")
            or _list(parsed, "evidencias_parciais")
            or _list(parsed, "requisitos_ausentes")
        )
    )


def validate_tailoring_suggestions(content: str) -> bool:
    parsed = _parse_markdown(content)
    return bool(
        re.match(r"^\d{1,3}/100$", _value(parsed, "score_de_aderencia", ""))
        and (
            _list(parsed, "pode_destacar_melhor")
            or _list(parsed, "pode_reposicionar")
            or _list(parsed, "precisa_criar_evidencia")
        )
    )


def pdi_to_markdown(result: dict[str, Any]) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"* {item}" for item in items) if items else "* Nenhum item"

    return f"""# PDI personalizado por vaga

## Resumo

* Vaga analisada: {result['target_role']}
* Score atual: {result['overall_score']}/100
* Nível de prontidão: {result['readiness_level']}
* Objetivo principal: {result['main_goal']}

## Lacunas prioritárias

{bullets(result['priority_gaps'])}

## Ganhos rápidos

{bullets(result['quick_wins'])}

## Plano de 7 dias

{bullets(result['seven_day_plan'])}

## Plano de 30 dias

{bullets(result['thirty_day_plan'])}

## Plano de 60 dias

{bullets(result['sixty_day_plan'])}

## Projetos práticos recomendados

{bullets(result['portfolio_projects'])}

## Evidências para criar no currículo

{bullets(result['resume_evidence_to_create'])}

## Estudos recomendados

{bullets(result['study_resources'])}

## Preparação para entrevista

{bullets(result['interview_preparation'])}

## Próximos passos

{bullets(result['next_steps'])}
"""


class PdiGenerator:
    """Converte lacunas em tarefas priorizadas e evidências futuras."""

    def generate(
        self,
        resume_content: str,
        job_content: str,
        match_content: str,
        tailoring_content: str,
    ) -> dict[str, Any]:
        resume = _parse_markdown(resume_content)
        job = _parse_markdown(job_content)
        match = _parse_markdown(match_content)
        tailoring = _parse_markdown(tailoring_content)

        target_role = _value(job, "titulo", "Vaga analisada")
        score_text = _value(match, "score_geral", "0/100")
        score_match = re.match(r"^(\d{1,3})/100$", score_text)
        overall_score = int(score_match.group(1)) if score_match else 0
        readiness = _value(match, "nivel_de_prontidao", "Não calculado")
        resume_level = _value(resume, "nivel_estimado", "nível atual")

        missing_required = _list(match, "requisitos_ausentes")
        partial_raw = _list(match, "evidencias_parciais")
        partial = _unique([_skill_from_sentence(item) for item in partial_raw])
        missing_keywords = _list(match, "palavras-chave_ausentes")
        nice_to_have = _list(job, "requisitos_desejaveis")
        responsibilities = _list(job, "responsabilidades")
        strong = _list(match, "evidencias_fortes_no_curriculo")
        needs_evidence_raw = _list(tailoring, "precisa_criar_evidencia")
        needs_evidence = _unique(
            [_skill_from_sentence(item) for item in needs_evidence_raw]
        )

        high = _unique(missing_required)
        medium = _unique(
            partial + [item for item in needs_evidence if item not in high]
        )
        low = _unique(
            [
                item
                for item in missing_keywords + nice_to_have
                if item not in high and item not in medium
            ]
        )

        priority_gaps = (
            [f"Alta prioridade: {item} — requisito ausente que afeta diretamente a aderência." for item in high]
            + [f"Média prioridade: {item} — evidência parcial que precisa ser fortalecida." for item in medium]
            + [f"Baixa prioridade: {item} — diferencial ou complemento para desenvolver depois." for item in low]
        )

        quick_wins = [
            f"Documentar melhor a evidência já existente de {item}, com contexto e resultado real."
            for item in strong[:4]
        ]
        quick_wins.extend(
            f"Confirmar o nível real de contato com {item} e classificar como estudo, projeto ou uso direto."
            for item in partial[:3]
        )

        seven_day_plan = [
            f"Dia 1: revisar a descrição de {target_role} e confirmar quais requisitos de alta prioridade são eliminatórios.",
            "Dia 2: organizar no currículo apenas as evidências fortes já comprovadas.",
        ]
        seven_day_plan.extend(
            f"Dias 3-5: concluir uma introdução prática de {item} e registrar aprendizados."
            for item in high[:2]
        )
        seven_day_plan.extend(
            [
                "Dia 6: preparar respostas curtas sobre pontos fortes, lacunas e plano de desenvolvimento.",
                "Dia 7: publicar ou organizar uma primeira evidência verificável sem apresentá-la como experiência profissional.",
            ]
        )

        thirty_day_plan = [
            f"Construir um mini projeto focado em {item}, com README, escopo, decisões e resultado reproduzível."
            for item in _unique(high + medium)[:3]
        ]
        thirty_day_plan.extend(
            [
                "Atualizar portfólio ou GitHub com entregáveis concluídos e linguagem factual.",
                "Revisar o currículo somente após existir evidência concreta das novas habilidades.",
                f"Realizar uma simulação de entrevista para {target_role} usando requisitos e responsabilidades reais da vaga.",
            ]
        )

        sixty_day_plan = [
            f"Evoluir o projeto de {item} para incluir teste, documentação e uma decisão técnica justificável."
            for item in _unique(high + medium)[:2]
        ]
        sixty_day_plan.extend(
            [
                "Criar uma publicação curta no LinkedIn explicando aprendizado e resultado, sem chamar estudo de experiência.",
                "Comparar novamente currículo e vaga para medir evolução do score.",
                "Priorizar uma segunda vaga semelhante para validar se as evidências criadas são reutilizáveis.",
            ]
        )

        portfolio_projects = [
            f"Projeto de evidência em {item}: problema pequeno, implementação funcional, README e demonstração do resultado."
            for item in _unique(high + medium)[:4]
        ] or [
            "Aprimorar um projeto real existente com README, decisões, métricas e demonstração."
        ]

        resume_evidence = [
            f"Após concluir e publicar, registrar {item} como projeto ou habilidade em desenvolvimento, indicando exatamente o que foi feito."
            for item in _unique(high + medium)[:5]
        ]

        study_resources = []
        for item in _unique(high + medium + low)[:8]:
            resource = RESOURCE_MAP.get(item)
            if resource:
                study_resources.append(f"{item}: {resource[0]} — {resource[1]}")
            else:
                study_resources.append(
                    f"{item}: priorizar documentação oficial ou material introdutório com exercício prático."
                )

        interview_preparation = [
            f"Preparar um exemplo verdadeiro que demonstre {item}."
            for item in strong[:3]
        ]
        interview_preparation.extend(
            f"Responder com transparência sobre {item}: explicar o que já estudou, o que ainda falta e o próximo passo prático."
            for item in _unique(high + medium)[:3]
        )
        interview_preparation.extend(
            f"Treinar uma resposta sobre a responsabilidade: {item}"
            for item in responsibilities[:2]
        )

        main_focus = ", ".join(high[:2] or medium[:2] or ["evidências da vaga"])
        main_goal = (
            f"Aumentar a aderência para {target_role} fortalecendo {main_focus}, "
            f"sem alterar artificialmente a senioridade {resume_level}."
        )

        return {
            "target_role": target_role,
            "overall_score": overall_score,
            "readiness_level": readiness,
            "main_goal": main_goal,
            "priority_gaps": priority_gaps or [
                "Nenhuma lacuna crítica foi identificada; priorize profundidade e documentação das evidências existentes."
            ],
            "quick_wins": _unique(quick_wins) or [
                "Melhorar a clareza das evidências já presentes no currículo."
            ],
            "seven_day_plan": _unique(seven_day_plan),
            "thirty_day_plan": _unique(thirty_day_plan),
            "sixty_day_plan": _unique(sixty_day_plan),
            "portfolio_projects": _unique(portfolio_projects),
            "resume_evidence_to_create": _unique(resume_evidence),
            "study_resources": _unique(study_resources),
            "interview_preparation": _unique(interview_preparation),
            "next_steps": [
                "Escolher no máximo duas lacunas de alta prioridade para começar.",
                "Executar o plano de 7 dias e registrar evidências reais.",
                "Não incluir habilidade nova como domínio antes de concluir uma entrega verificável.",
                "Usar este PDI como contexto futuro para uma entrevista simulada específica da vaga.",
            ],
        }
