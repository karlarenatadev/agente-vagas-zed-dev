"""Sugestões heurísticas e seguras para adaptar um currículo a uma vaga."""

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
}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", normalized.casefold()).strip()


def _clean_evidence(value: str) -> str:
    return re.sub(r"\s*\([^)]*(?:evidência|indício|mencionado)[^)]*\)\s*$", "", value).strip()


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
            if ":" in value and current_section == "resumo":
                key, _, field_value = value.partition(":")
                data[_normalize(key).replace(" ", "_")] = field_value.strip()
            elif current_section:
                section = data.setdefault(current_section, [])
                if isinstance(section, list):
                    section.append(value)

    return data


def _list(data: dict[str, Any], key: str) -> list[str]:
    value = data.get(key, [])
    return _unique(value if isinstance(value, list) else [value])


def _value(data: dict[str, Any], key: str, fallback: str) -> str:
    value = data.get(key, fallback)
    if isinstance(value, list):
        value = value[0] if value else fallback
    return value if _normalize(str(value)) not in INVALID_MARKERS else fallback


def _valid_score(value: str) -> bool:
    match = re.fullmatch(r"(\d{1,3})/100", value)
    return bool(match and 0 <= int(match.group(1)) <= 100)


def validate_resume_analysis(content: str) -> bool:
    data = _parse_markdown(content)
    return bool(
        _list(data, "habilidades_tecnicas_detectadas")
        or _list(data, "soft_skills_detectadas")
    )


def validate_job_analysis(content: str) -> bool:
    data = _parse_markdown(content)
    return bool(
        _list(data, "hard_skills")
        or _list(data, "ferramentas")
        or _list(data, "palavras-chave_principais")
    )


def validate_match_report(content: str) -> bool:
    data = _parse_markdown(content)
    score = _value(data, "score_geral", "")
    return bool(
        _valid_score(score)
        and (
            _list(data, "evidencias_fortes_no_curriculo")
            or _list(data, "evidencias_parciais")
            or _list(data, "requisitos_ausentes")
        )
    )


def tailoring_to_markdown(result: dict[str, Any]) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"* {item}" for item in items) if items else "* Nenhum item"

    return f"""# Sugestões seguras de currículo

## Resumo da análise

* Vaga analisada: {result['job_title']}
* Score de aderência: {result['match_score']}/100
* Nível de prontidão: {result['readiness_level']}

## Pode destacar melhor

{bullets(result['can_highlight_better'])}

## Pode reposicionar

{bullets(result['can_reposition'])}

## Precisa criar evidência

{bullets(result['needs_evidence'])}

## Não afirmar ainda

{bullets(result['do_not_claim'])}

## Sugestão para resumo profissional

{bullets(result['summary_suggestions'])}

## Sugestões para seção de habilidades

{bullets(result['skills_suggestions'])}

## Sugestões para projetos

{bullets(result['project_suggestions'])}

## Sugestões para experiências

{bullets(result['experience_suggestions'])}

## Palavras-chave que podem entrar com segurança

{bullets(result['keywords_to_include'])}

## Palavras-chave que exigem cuidado

{bullets(result['keywords_to_avoid_claiming'])}

## Alertas de segurança

{bullets(result['safety_alerts'])}

## Próximos passos

{bullets(result['next_steps'])}
"""


def tailoring_from_markdown(content: str) -> dict[str, Any] | None:
    """Restaura sugestões persistidas pelo ``tailoring_to_markdown``."""
    parsed = _parse_markdown(content)
    score_match = re.match(
        r"^(\d{1,3})/100$",
        _value(parsed, "score_de_aderencia", ""),
    )
    if not score_match:
        return None

    return {
        "job_title": _value(parsed, "vaga_analisada", "Vaga analisada"),
        "match_score": int(score_match.group(1)),
        "readiness_level": _value(
            parsed,
            "nivel_de_prontidao",
            "Não calculado",
        ),
        "summary_suggestions": _list(
            parsed,
            "sugestao_para_resumo_profissional",
        ),
        "skills_suggestions": _list(
            parsed,
            "sugestoes_para_secao_de_habilidades",
        ),
        "project_suggestions": _list(parsed, "sugestoes_para_projetos"),
        "experience_suggestions": _list(
            parsed,
            "sugestoes_para_experiencias",
        ),
        "keywords_to_include": _list(
            parsed,
            "palavras-chave_que_podem_entrar_com_seguranca",
        ),
        "keywords_to_avoid_claiming": _list(
            parsed,
            "palavras-chave_que_exigem_cuidado",
        ),
        "can_highlight_better": _list(parsed, "pode_destacar_melhor"),
        "can_reposition": _list(parsed, "pode_reposicionar"),
        "needs_evidence": _list(parsed, "precisa_criar_evidencia"),
        "do_not_claim": _list(parsed, "nao_afirmar_ainda"),
        "safety_alerts": _list(parsed, "alertas_de_seguranca"),
        "next_steps": _list(parsed, "proximos_passos"),
    }


def _focus_tailor_step(focus: str, absent: list[str], strong: list[str]) -> str:
    """Próximo passo do tailoring calibrado pelo foco da candidatura."""
    if focus == "curriculo":
        return (
            "Como o foco é o currículo, mantenha a narrativa atual e aplique só os "
            "ajustes de clareza; evite reescrever o currículo inteiro para a vaga."
        )
    if focus == "perfil":
        return (
            "Como o foco é o perfil declarado, ajuste o currículo para reforçar seu "
            "objetivo de carreira antes de mirar requisitos específicos da vaga."
        )
    alvo = ", ".join(absent[:3]) or "as palavras-chave da vaga"
    return (
        "Como o foco é a vaga, priorize as sugestões que aproximam o currículo de "
        f"{alvo}, sempre sem inventar evidências."
    )


class ResumeTailor:
    """Transforma o match em orientações, sem escrever experiências fictícias."""

    def generate(
        self,
        resume_content: str,
        job_content: str,
        match_content: str,
        focus: str = "vaga",
    ) -> dict[str, Any]:
        resume = _parse_markdown(resume_content)
        job = _parse_markdown(job_content)
        match = _parse_markdown(match_content)

        job_title = _value(job, "titulo", "Vaga analisada")
        score_text = _value(match, "score_geral", "0/100")
        score_match = re.match(r"^(\d{1,3})/100$", score_text)
        match_score = int(score_match.group(1)) if score_match else 0
        readiness = _value(match, "nivel_de_prontidao", "Não calculado")

        strong = _list(match, "evidencias_fortes_no_curriculo")
        partial_raw = _list(match, "evidencias_parciais")
        partial = _unique([_clean_evidence(item) for item in partial_raw])
        missing = _list(match, "requisitos_ausentes")
        missing_keywords = _list(match, "palavras-chave_ausentes")
        matched_keywords = _list(match, "palavras-chave_encontradas")
        do_not_claim = _list(match, "nao_afirmar_ainda")

        resume_strengths = _list(resume, "pontos_fortes")
        resume_experience = _value(
            resume,
            "experiencias_detectadas",
            "Experiências ou projetos já descritos no currículo",
        )
        resume_level = _value(resume, "nivel_estimado", "nível atual informado")
        probable_areas = _list(resume, "areas_provaveis")

        can_highlight = [
            f"Dar mais clareza à evidência de {item}, indicando contexto e resultado real quando existirem."
            for item in strong[:6]
        ]
        can_highlight.extend(
            f"Preservar e tornar mais específico este ponto forte já identificado: {item}"
            for item in resume_strengths[:3]
        )

        can_reposition = [
            f"Conectar {item} às responsabilidades da vaga apenas no contexto real em que aparece no currículo."
            for item in partial[:5]
        ]
        if probable_areas:
            can_reposition.append(
                f"Aproximar o resumo da área {probable_areas[0]} do cargo {job_title}, sem alterar a senioridade {resume_level}."
            )

        absent = _unique(missing + missing_keywords)
        needs_evidence = [
            f"Criar estudo, projeto prático ou entrega verificável com {item}; até lá, usar no máximo 'em desenvolvimento'."
            for item in absent[:8]
        ]

        safe_do_not_claim = do_not_claim or [
            f"Não afirmar domínio ou experiência profissional em {item} sem evidência."
            for item in absent[:6]
        ]

        summary_suggestions = [
            f"Reescrever o resumo para enfatizar o foco real em {probable_areas[0] if probable_areas else job_title} e as evidências comprovadas de {', '.join(strong[:4]) or 'habilidades já documentadas'}.",
            f"Manter a senioridade como {resume_level}; não adaptar o título profissional apenas para reproduzir o nível pedido pela vaga.",
        ]

        skills_suggestions = []
        if strong:
            skills_suggestions.append(
                f"Priorizar no início da seção as habilidades comprovadas mais alinhadas: {', '.join(strong[:6])}."
            )
        if partial:
            skills_suggestions.append(
                f"Separar como conhecimento ou prática parcial, quando verdadeiro: {', '.join(partial[:5])}."
            )
        if absent:
            skills_suggestions.append(
                f"Não listar como habilidade consolidada antes de criar evidência: {', '.join(absent[:6])}."
            )

        project_suggestions = [
            f"Criar um projeto pequeno e publicável que demonstre {item}, com README, decisões e resultado observável."
            for item in absent[:4]
        ] or [
            "Aprimorar a documentação dos projetos reais já citados, incluindo problema, ação e resultado."
        ]

        experience_suggestions = [
            f"Revisar o trecho existente sobre '{resume_experience}' para separar contexto, ação e resultado mensurável, sem criar novas responsabilidades.",
        ]
        if strong:
            experience_suggestions.append(
                f"Nas experiências ou projetos onde for verdadeiro, associar {', '.join(strong[:4])} às entregas realizadas."
            )
        if partial:
            experience_suggestions.append(
                f"Confirmar antes de mencionar {', '.join(partial[:4])} se houve uso direto, estudo ou apenas contato indireto."
            )

        strong_keys = {_normalize(item) for item in strong}
        keywords_to_include = _unique(
            strong
            + [
                item
                for item in matched_keywords
                if _normalize(item) in strong_keys
            ]
        )
        keywords_to_avoid = _unique(absent + partial)

        safety_alerts = [
            "Não inventar empresa, cargo, certificação, projeto, responsabilidade ou resultado.",
            "Não transformar estudo, curso ou projeto pessoal em experiência profissional.",
            "Não declarar domínio de tecnologia classificada como parcial ou ausente.",
            f"Não inflar a senioridade além de {resume_level} sem evidência profissional.",
            "Toda palavra-chave inserida deve estar ligada a uma evidência real do currículo.",
        ]

        return {
            "job_title": job_title,
            "match_score": match_score,
            "readiness_level": readiness,
            "summary_suggestions": _unique(summary_suggestions),
            "skills_suggestions": _unique(skills_suggestions),
            "project_suggestions": _unique(project_suggestions),
            "experience_suggestions": _unique(experience_suggestions),
            "keywords_to_include": keywords_to_include,
            "keywords_to_avoid_claiming": keywords_to_avoid,
            "can_highlight_better": _unique(can_highlight),
            "can_reposition": _unique(can_reposition),
            "needs_evidence": _unique(needs_evidence),
            "do_not_claim": _unique(safe_do_not_claim),
            "safety_alerts": safety_alerts,
            "next_steps": [
                _focus_tailor_step(focus, absent, strong),
                "Confirmar quais sugestões correspondem a experiências reais antes de editar o currículo.",
                "Aplicar primeiro as melhorias de clareza e organização que usam evidências fortes.",
                "Criar evidências práticas para lacunas prioritárias antes de adicioná-las como habilidades.",
                "Usar este artefato com o relatório de match na futura geração do PDI personalizado.",
            ],
        }
