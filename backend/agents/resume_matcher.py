"""Match heurístico e explicável entre análise de vaga e currículo."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any


ALIASES: dict[str, str] = {
    "api": "APIs",
    "apis": "APIs",
    "api rest": "APIs",
    "rest": "APIs",
    "business intelligence": "Business Intelligence",
    "bi": "Business Intelligence",
    "css3": "CSS",
    "git": "Git",
    "github": "Git",
    "html5": "HTML",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "power bi": "Power BI",
    "powerbi": "Power BI",
    "react.js": "React",
    "ts": "TypeScript",
    "typescript": "TypeScript",
}

RELATED_EVIDENCE: dict[str, tuple[str, ...]] = {
    "APIs": ("automação", "integração", "serviços"),
    "AWS": ("cloud", "nuvem"),
    "Business Intelligence": ("Power BI", "dashboards", "indicadores"),
    "Dashboards": ("Power BI", "Tableau", "indicadores"),
    "ETL": ("automação de relatórios", "tratamento de dados", "pipeline"),
    "Indicadores e KPIs": ("dashboards", "Power BI", "análise de dados"),
    "Gestão de stakeholders": ("comunicação", "trabalho em equipe"),
    "Git": ("GitHub", "controle de versão"),
}

SECTION_ALIASES: dict[str, str] = {
    "hard skills": "hard_skills",
    "soft skills": "soft_skills",
    "ferramentas": "tools",
    "palavras-chave principais": "keywords",
    "requisitos obrigatorios": "required_requirements",
    "requisitos desejaveis": "nice_to_have",
    "responsabilidades": "responsibilities",
    "areas provaveis": "probable_areas",
    "habilidades tecnicas detectadas": "technical_skills",
    "soft skills detectadas": "resume_soft_skills",
    "funcoes alvo sugeridas": "target_roles",
    "pontos fortes": "resume_strengths",
}

SENIORITY_ORDER = {
    "estagio/trainee": 0,
    "estagio/junior": 0,
    "junior": 1,
    "pleno": 2,
    "senior": 3,
}

IGNORED_VALUES = {
    "",
    "não analisada",
    "não analisado",
    "não identificado",
    "não identificada",
    "nenhuma análise realizada",
}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", normalized.casefold()).strip()


def _canonical(value: str) -> str:
    clean = re.sub(r"\s+", " ", value).strip(" \t:;,.")
    return ALIASES.get(_normalize(clean), clean)


def _unique(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        canonical = _canonical(item)
        key = _normalize(canonical)
        if key in IGNORED_VALUES or key in seen:
            continue
        seen.add(key)
        result.append(canonical)
    return result


def _parse_markdown(content: str) -> dict[str, Any]:
    data: dict[str, Any] = {"raw": content}
    current_section: str | None = None
    lines = content.splitlines()

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("## "):
            heading = _normalize(line[3:])
            current_section = SECTION_ALIASES.get(heading)
            if current_section:
                data.setdefault(current_section, [])
            continue

        plain_heading = _normalize(line.rstrip(":"))
        if line.endswith(":") and plain_heading in SECTION_ALIASES:
            current_section = SECTION_ALIASES[plain_heading]
            data.setdefault(current_section, [])
            continue

        if line.endswith(":") and plain_heading in {
            "resumo profissional",
            "nivel estimado",
        }:
            current_section = None
            next_value = next(
                (
                    candidate.strip()
                    for candidate in lines[index + 1 :]
                    if candidate.strip()
                ),
                "",
            )
            data[plain_heading.replace(" ", "_")] = next_value
            continue

        if line.startswith(("* ", "- ")):
            value = line[2:].strip()
            if current_section and ":" not in value:
                data[current_section].append(value)
                continue

            if ":" in value:
                key, _, field_value = value.partition(":")
                data[_normalize(key).replace(" ", "_")] = field_value.strip()
                continue

            if current_section:
                data[current_section].append(value)
            continue

        if ":" in line and not line.startswith("#"):
            key, _, value = line.partition(":")
            normalized_key = _normalize(key).replace(" ", "_")
            if normalized_key in {
                "nome_detectado",
                "nivel_estimado",
                "concluido",
            }:
                data[normalized_key] = value.strip()

    return data


def _contains(text: str, term: str) -> bool:
    normalized_text = f" {_normalize(text)} "
    normalized_term = _normalize(term)
    if not normalized_term:
        return False
    return f" {normalized_term} " in normalized_text or normalized_term in normalized_text


def _related_evidence(term: str, resume_text: str) -> str | None:
    for related in RELATED_EVIDENCE.get(_canonical(term), ()):
        if _contains(resume_text, related):
            return related
    return None


@dataclass
class EvidenceResult:
    strong: list[str]
    partial: list[str]
    missing: list[str]
    partial_reasons: dict[str, str]


def _classify(
    required: list[str],
    explicit_resume_items: list[str],
    resume_text: str,
) -> EvidenceResult:
    explicit_keys = {_normalize(_canonical(item)) for item in explicit_resume_items}
    strong: list[str] = []
    partial: list[str] = []
    missing: list[str] = []
    partial_reasons: dict[str, str] = {}

    for item in _unique(required):
        canonical = _canonical(item)
        key = _normalize(canonical)
        if key in explicit_keys:
            strong.append(canonical)
            continue

        if _contains(resume_text, canonical):
            partial.append(canonical)
            partial_reasons[canonical] = "mencionado fora da lista explícita de habilidades"
            continue

        related = _related_evidence(canonical, resume_text)
        if related:
            partial.append(canonical)
            partial_reasons[canonical] = f"indício relacionado: {related}"
            continue

        missing.append(canonical)

    return EvidenceResult(strong, partial, missing, partial_reasons)


def _category_score(result: EvidenceResult) -> float:
    total = len(result.strong) + len(result.partial) + len(result.missing)
    if total == 0:
        return 1.0
    return (len(result.strong) + 0.5 * len(result.partial)) / total


def _seniority_score(job_level: str, resume_level: str) -> float:
    job_rank = SENIORITY_ORDER.get(_normalize(job_level))
    resume_rank = SENIORITY_ORDER.get(_normalize(resume_level))
    if job_rank is None or resume_rank is None:
        return 0.5
    if resume_rank >= job_rank:
        return 1.0
    distance = job_rank - resume_rank
    return 0.5 if distance == 1 else 0.15


def _area_score(job_title: str, probable_areas: list[str], target_roles: list[str]) -> float:
    title = _normalize(job_title)
    evidence = probable_areas + target_roles
    if not title or _normalize(job_title) in IGNORED_VALUES:
        return 0.5

    title_tokens = {
        token
        for token in re.findall(r"[a-zà-ÿ]{3,}", title)
        if token not in {"analista", "assistente", "desenvolvedor", "engenheiro"}
    }
    evidence_text = _normalize(" ".join(evidence))
    if title_tokens and any(token in evidence_text for token in title_tokens):
        return 1.0
    return 0.25 if evidence else 0.5


def _readiness(score: int) -> str:
    if score >= 80:
        return "fortemente aderente"
    if score >= 60:
        return "parcialmente aderente"
    if score >= 40:
        return "aderência em desenvolvimento"
    return "baixa aderência atual"


def _safe_suggestions(
    strong: list[str],
    partial: list[str],
    missing: list[str],
    matched_keywords: list[str],
) -> list[str]:
    suggestions: list[str] = []
    if strong:
        suggestions.append(
            f"Destaque as evidências reais de {', '.join(strong[:4])} nas experiências ou projetos em que foram usadas."
        )
    if matched_keywords:
        suggestions.append(
            f"Use termos já comprovados no currículo, como {', '.join(matched_keywords[:4])}, de forma consistente no resumo e nas realizações."
        )
    if partial:
        suggestions.append(
            f"Detalhe o contexto das menções a {', '.join(partial[:3])}; mantenha-as como conhecimento ou prática, sem afirmar domínio."
        )
    if missing:
        suggestions.append(
            f"Para {', '.join(missing[:3])}, considere estudo ou projeto prático e descreva a habilidade como 'em desenvolvimento' até existir evidência."
        )
    return suggestions or [
        "Revise o currículo para tornar resultados e responsabilidades reais mais específicos."
    ]


def _do_not_claim(missing: list[str], partial: list[str], job_level: str, resume_level: str) -> list[str]:
    warnings = [
        f"Não afirmar domínio ou experiência profissional em {item} sem evidência no currículo."
        for item in missing[:6]
    ]
    if partial:
        warnings.append(
            f"Não apresentar {', '.join(partial[:4])} como domínio avançado; há apenas evidência parcial."
        )
    if (
        _normalize(job_level) not in IGNORED_VALUES
        and _normalize(resume_level) not in IGNORED_VALUES
        and _seniority_score(job_level, resume_level) < 1
    ):
        warnings.append(
            f"Não elevar a senioridade do currículo de {resume_level} para {job_level} sem experiência comprovada."
        )
    return warnings or [
        "Não adicionar tecnologias, resultados ou experiências que não estejam comprovados no currículo."
    ]


def match_report_to_markdown(report: dict[str, Any]) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"* {item}" for item in items) if items else "* Nenhum item"

    breakdown = report["score_breakdown"]
    return f"""# Relatório de aderência entre vaga e currículo

## Resumo

* Score geral: {report['overall_score']}/100
* Nível de prontidão: {report['readiness_level']}
* Vaga analisada: {report['job_title']}
* Currículo analisado: {report['resume_summary']}

## Composição do score

* Hard skills: {breakdown['hard_skills']}/45
* Ferramentas: {breakdown['tools']}/20
* Soft skills: {breakdown['soft_skills']}/15
* Palavras-chave: {breakdown['keywords']}/10
* Senioridade e área: {breakdown['seniority_area']}/10

## Evidências fortes no currículo

{bullets(report['strong_evidence'])}

## Evidências parciais

{bullets(report['partial_evidence'])}

## Hard skills encontradas

{bullets(report['hard_skills_found'])}

## Hard skills ausentes

{bullets(report['hard_skills_missing'])}

## Soft skills encontradas

{bullets(report['soft_skills_found'])}

## Soft skills ausentes

{bullets(report['soft_skills_missing'])}

## Ferramentas encontradas

{bullets(report['tools_found'])}

## Ferramentas ausentes

{bullets(report['tools_missing'])}

## Requisitos ausentes

{bullets(report['missing_requirements'])}

## Palavras-chave encontradas

{bullets(report['matched_keywords'])}

## Palavras-chave ausentes

{bullets(report['missing_keywords'])}

## Pontos fortes para essa vaga

{bullets(report['strengths'])}

## Lacunas críticas

{bullets(report['critical_gaps'])}

## Sugestões seguras para melhorar o currículo

{bullets(report['safe_resume_suggestions'])}

## Não afirmar ainda

{bullets(report['do_not_claim'])}

## Próximos passos recomendados

{bullets(report['next_steps'])}
"""


def match_report_from_markdown(content: str) -> dict[str, Any] | None:
    """Restaura um relatório persistido pelo ``match_report_to_markdown``."""
    parsed = _parse_markdown(content)
    score_match = re.match(
        r"^(\d{1,3})/100$",
        str(parsed.get("score_geral", "")),
    )
    if not score_match:
        return None

    def items(key: str) -> list[str]:
        value = parsed.get(key, [])
        return _unique(value if isinstance(value, list) else [str(value)])

    def score(key: str) -> int:
        value = str(parsed.get(key, "0"))
        match = re.match(r"^(\d{1,3})/", value)
        return int(match.group(1)) if match else 0

    return {
        "overall_score": int(score_match.group(1)),
        "readiness_level": str(
            parsed.get("nivel_de_prontidao", "Não calculado")
        ),
        "job_title": str(parsed.get("vaga_analisada", "Vaga analisada")),
        "resume_summary": str(
            parsed.get("curriculo_analisado", "Currículo analisado")
        ),
        "score_breakdown": {
            "hard_skills": score("hard_skills"),
            "tools": score("ferramentas"),
            "soft_skills": score("soft_skills"),
            "keywords": score("palavras-chave"),
            "seniority_area": score("senioridade_e_area"),
        },
        "strong_evidence": items("evidencias_fortes_no_curriculo"),
        "partial_evidence": items("evidencias_parciais"),
        "missing_requirements": items("requisitos_ausentes"),
        "hard_skills_found": items("hard_skills_encontradas"),
        "hard_skills_missing": items("hard_skills_ausentes"),
        "soft_skills_found": items("soft_skills_encontradas"),
        "soft_skills_missing": items("soft_skills_ausentes"),
        "tools_found": items("ferramentas_encontradas"),
        "tools_missing": items("ferramentas_ausentes"),
        "matched_keywords": items("palavras-chave_encontradas"),
        "missing_keywords": items("palavras-chave_ausentes"),
        "strengths": items("pontos_fortes_para_essa_vaga"),
        "critical_gaps": items("lacunas_criticas"),
        "safe_resume_suggestions": items(
            "sugestoes_seguras_para_melhorar_o_curriculo"
        ),
        "do_not_claim": items("nao_afirmar_ainda"),
        "next_steps": items("proximos_passos_recomendados"),
    }


def _focus_match_step(focus: str, missing_requirements: list[str], strong_evidence: list[str]) -> str:
    """Próximo passo do match calibrado pelo foco da candidatura."""
    if focus == "curriculo":
        destaques = ", ".join(strong_evidence[:3]) or "suas evidências já comprovadas"
        return (
            f"Como o foco é o currículo, destaque {destaques} e trate os requisitos "
            "ausentes da vaga como diferenciais opcionais, não como prioridade."
        )
    if focus == "perfil":
        return (
            "Como o foco é o seu perfil declarado, alinhe currículo e vaga ao seu "
            "objetivo de carreira; use as lacunas da vaga apenas como referência."
        )
    lacunas = ", ".join(missing_requirements[:3]) or "os requisitos obrigatórios"
    return f"Como o foco é a vaga, priorize fechar {lacunas} antes de se candidatar."


class ResumeMatcher:
    """Compara os dois artefatos Markdown sem inventar dados."""

    def match(self, job_content: str, resume_content: str, focus: str = "vaga") -> dict[str, Any]:
        job = _parse_markdown(job_content)
        resume = _parse_markdown(resume_content)

        job_hard = _unique(job.get("hard_skills", []))
        job_tools = _unique(job.get("tools", []))
        job_soft = _unique(job.get("soft_skills", []))
        job_keywords = _unique(job.get("keywords", []))

        resume_technical = _unique(resume.get("technical_skills", []))
        resume_soft = _unique(resume.get("resume_soft_skills", []))
        resume_text = resume.get("raw", "")

        hard = _classify(job_hard, resume_technical, resume_text)
        tools = _classify(job_tools, resume_technical, resume_text)
        soft = _classify(job_soft, resume_soft, resume_text)
        keywords = _classify(job_keywords, resume_technical + resume_soft, resume_text)

        job_level = job.get("senioridade", "Não identificada")
        resume_level = resume.get("nivel_estimado", "Não identificado")
        seniority_area = (
            _seniority_score(job_level, resume_level)
            + _area_score(
                job.get("titulo", "Não identificado"),
                resume.get("probable_areas", []),
                resume.get("target_roles", []),
            )
        ) / 2

        score_breakdown = {
            "hard_skills": round(_category_score(hard) * 45),
            "tools": round(_category_score(tools) * 20),
            "soft_skills": round(_category_score(soft) * 15),
            "keywords": round(_category_score(keywords) * 10),
            "seniority_area": round(seniority_area * 10),
        }
        overall_score = sum(score_breakdown.values())

        all_strong = _unique(hard.strong + tools.strong + soft.strong)
        partial_labels = []
        for result in (hard, tools, soft, keywords):
            partial_labels.extend(
                f"{item} ({result.partial_reasons.get(item, 'evidência indireta')})"
                for item in result.partial
            )
        all_partial = _unique(partial_labels)
        required_text = " ".join(job.get("required_requirements", []))
        required_items = [
            item
            for item in _unique(job_hard + job_tools + job_soft)
            if _contains(required_text, item)
        ]
        all_missing = _unique(hard.missing + tools.missing + soft.missing)
        missing_requirements = [
            item
            for item in all_missing
            if _normalize(item) in {_normalize(value) for value in required_items}
        ]

        strengths = []
        if all_strong:
            strengths.append(
                f"O currículo apresenta evidência explícita de {', '.join(all_strong[:5])}."
            )
        if keywords.strong or keywords.partial:
            strengths.append(
                "Há vocabulário relevante da vaga já presente no currículo."
            )
        if _area_score(
            job.get("titulo", ""),
            resume.get("probable_areas", []),
            resume.get("target_roles", []),
        ) == 1:
            strengths.append("A área provável do currículo está alinhada ao cargo analisado.")

        critical_gaps = [
            f"{item} não aparece no currículo e foi identificado como requisito obrigatório da vaga."
            for item in missing_requirements[:6]
        ]
        if _seniority_score(job_level, resume_level) < 0.5:
            critical_gaps.append(
                f"A vaga indica nível {job_level}, enquanto o currículo foi estimado como {resume_level}."
            )

        suggestions = _safe_suggestions(
            all_strong,
            _unique(hard.partial + tools.partial + soft.partial),
            all_missing,
            _unique(keywords.strong + keywords.partial),
        )
        do_not_claim = _do_not_claim(
            all_missing,
            _unique(hard.partial + tools.partial + soft.partial),
            job_level,
            resume_level,
        )

        return {
            "overall_score": overall_score,
            "readiness_level": _readiness(overall_score),
            "job_title": job.get("titulo", "Não identificado"),
            "resume_summary": (
                resume.get("resumo_profissional")
                or "Currículo analisado em data/resume-analysis.md"
            ),
            "score_breakdown": score_breakdown,
            "strong_evidence": all_strong,
            "partial_evidence": all_partial,
            "missing_requirements": missing_requirements,
            "hard_skills_found": _unique(hard.strong + hard.partial),
            "hard_skills_missing": hard.missing,
            "soft_skills_found": _unique(soft.strong + soft.partial),
            "soft_skills_missing": soft.missing,
            "tools_found": _unique(tools.strong + tools.partial),
            "tools_missing": tools.missing,
            "matched_keywords": _unique(keywords.strong + keywords.partial),
            "missing_keywords": keywords.missing,
            "strengths": strengths or [
                "O currículo precisa explicitar melhor evidências relacionadas a esta vaga."
            ],
            "critical_gaps": critical_gaps or [
                "Nenhuma lacuna técnica crítica foi identificada pela comparação local."
            ],
            "safe_resume_suggestions": suggestions,
            "do_not_claim": do_not_claim,
            "next_steps": [
                _focus_match_step(focus, missing_requirements, all_strong),
                "Confirmar se as evidências parciais representam experiências ou apenas estudos.",
                "Revisar o currículo usando somente resultados, projetos e responsabilidades reais.",
                "Usar este relatório como entrada futura para sugestões de adaptação do currículo.",
                "Usar data/resume-match-report.md como base da próxima etapa de PDI personalizado.",
            ],
        }


def validate_job_analysis(content: str) -> bool:
    parsed = _parse_markdown(content)
    return bool(
        _unique(parsed.get("hard_skills", []))
        or _unique(parsed.get("tools", []))
        or _unique(parsed.get("keywords", []))
    )


def validate_resume_analysis(content: str) -> bool:
    parsed = _parse_markdown(content)
    return bool(
        _unique(parsed.get("technical_skills", []))
        or _unique(parsed.get("resume_soft_skills", []))
    )
