"""Análise local e determinística de descrições de vagas."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any


SKILL_PATTERNS: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "SQL": [r"\bsql\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b"],
    "React": [r"\breact(?:\.js)?\b"],
    "Node.js": [r"\bnode(?:\.js)?\b"],
    "HTML": [r"\bhtml5?\b"],
    "CSS": [r"\bcss3?\b"],
    "APIs": [r"\bapi(?:s)?\b", r"\brest(?:ful)?\b"],
    "ETL": [r"\betl\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
    "Análise de dados": [r"\ban[aá]lise de dados\b"],
    "Dashboards": [r"\bdashboard(?:s)?\b"],
    "Indicadores e KPIs": [r"\bindicador(?:es)?\b", r"\bkpis?\b"],
    "Testes automatizados": [
        r"\btestes? automatizad[oa]s?\b",
        r"\bunit tests?\b",
    ],
}

TOOL_PATTERNS: dict[str, list[str]] = {
    "Power BI": [r"\bpower\s*bi\b"],
    "Excel": [r"\bexcel\b"],
    "Git": [r"\bgit\b"],
    "GitHub": [r"\bgithub\b"],
    "Docker": [r"\bdocker\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Azure": [r"\bazure\b"],
    "Google Cloud": [r"\bgcp\b", r"\bgoogle cloud\b"],
    "Figma": [r"\bfigma\b"],
    "Tableau": [r"\btableau\b"],
    "Jira": [r"\bjira\b"],
    "Spark": [r"\bspark\b", r"\bpyspark\b"],
    "Airflow": [r"\bairflow\b"],
}

SOFT_SKILL_PATTERNS: dict[str, list[str]] = {
    "Comunicação": [r"\bcomunica[cç][aã]o\b"],
    "Liderança": [r"\blideran[cç]a\b"],
    "Trabalho em equipe": [
        r"\btrabalho em equipe\b",
        r"\bcolabora[cç][aã]o\b",
    ],
    "Resolução de problemas": [
        r"\bresolu[cç][aã]o de problemas\b",
        r"\bproblem solving\b",
    ],
    "Pensamento crítico": [r"\bpensamento cr[ií]tico\b"],
    "Organização": [r"\borganiza[cç][aã]o\b"],
    "Proatividade": [r"\bproativ[oa]\b", r"\bproatividade\b"],
    "Autonomia": [r"\bautonomia\b"],
    "Adaptabilidade": [r"\badaptabilidade\b"],
    "Gestão de stakeholders": [r"\bstakeholders?\b"],
}

SECTION_HEADINGS: dict[str, tuple[str, ...]] = {
    "responsibilities": (
        "responsabilidades",
        "atividades",
        "desafios",
        "o que voce vai fazer",
        "seu dia a dia",
        "atribuicoes",
    ),
    "required_requirements": (
        "requisitos",
        "requisitos obrigatorios",
        "o que esperamos",
        "o que buscamos",
        "qualificacoes",
        "necessario",
    ),
    "nice_to_have": (
        "diferenciais",
        "desejavel",
        "seria legal",
        "nice to have",
        "sera um diferencial",
    ),
}

RESPONSIBILITY_VERBS = (
    "analisar",
    "atuar",
    "colaborar",
    "conduzir",
    "construir",
    "criar",
    "desenvolver",
    "garantir",
    "gerenciar",
    "implementar",
    "liderar",
    "manter",
    "monitorar",
    "otimizar",
    "participar",
    "projetar",
    "realizar",
    "ser responsavel",
    "trabalhar",
)

REQUIRED_MARKERS = (
    "obrigatorio",
    "necessario",
    "requisito",
    "experiencia com",
    "dominio de",
    "conhecimento em",
    "precisa ter",
    "must have",
)

NICE_TO_HAVE_MARKERS = (
    "desejavel",
    "diferencial",
    "nice to have",
    "sera um plus",
    "seria legal",
)

GENERIC_TITLE_MARKERS = (
    "descricao da vaga",
    "sobre a vaga",
    "sobre nos",
    "quem somos",
    "responsabilidades",
    "requisitos",
    "atividades",
)

KEYWORD_STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "entre",
    "essa",
    "esta",
    "este",
    "experiencia",
    "nos",
    "nossa",
    "nosso",
    "o",
    "os",
    "ou",
    "para",
    "por",
    "que",
    "se",
    "ser",
    "sua",
    "suas",
    "um",
    "uma",
    "voce",
}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()


def _clean_line(value: str) -> str:
    value = re.sub(r"^[\s\-*•·▪◦\d.)]+", "", value)
    return re.sub(r"\s+", " ", value).strip(" \t:;-")


def _unique(items: list[str], limit: int | None = None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for item in items:
        clean = _clean_line(item)
        key = _normalize(clean)
        if not clean or key in seen:
            continue
        seen.add(key)
        result.append(clean)
        if limit and len(result) >= limit:
            break

    return result


def _find_terms(text: str, patterns: dict[str, list[str]]) -> list[str]:
    return [
        label
        for label, expressions in patterns.items()
        if any(re.search(expression, text, flags=re.IGNORECASE) for expression in expressions)
    ]


def _meaningful_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        clean = _clean_line(raw_line)
        if 3 <= len(clean) <= 320:
            lines.append(clean)
    return lines


def _detect_title(lines: list[str]) -> str:
    labelled_patterns = (
        r"^(?:titulo|cargo|posicao|oportunidade)\s*:\s*(.+)$",
        r"^vaga\s+(?:para|de)\s+(.+)$",
    )

    for line in lines[:20]:
        normalized = _normalize(line)
        for pattern in labelled_patterns:
            match = re.match(pattern, normalized, flags=re.IGNORECASE)
            if match:
                original_value = line.split(":", 1)[-1] if ":" in line else line
                return _clean_line(re.sub(r"(?i)^vaga\s+(?:para|de)\s+", "", original_value))

    role_pattern = re.compile(
        r"\b("
        r"analista|arquiteto|assistente|cientista|consultor|coordenador|"
        r"desenvolvedor|designer|developer|engenheiro|especialista|estagiario|"
        r"gerente|lider|product manager|product owner|tech lead"
        r")\b",
        flags=re.IGNORECASE,
    )

    for line in lines[:12]:
        normalized = _normalize(line)
        if (
            len(line) <= 100
            and role_pattern.search(normalized)
            and not any(marker in normalized for marker in GENERIC_TITLE_MARKERS)
        ):
            return line

    return "Não identificado"


def _detect_company(lines: list[str]) -> str:
    patterns = (
        r"^(?:empresa|company|organizacao)\s*:\s*(.+)$",
        r"^sobre\s+(?:a|o)\s+(.+)$",
    )

    for line in lines[:30]:
        normalized = _normalize(line)
        for pattern in patterns:
            match = re.match(pattern, normalized, flags=re.IGNORECASE)
            if not match:
                continue
            value = line.split(":", 1)[-1] if ":" in line else match.group(1)
            clean = _clean_line(value)
            if clean and _normalize(clean) not in {"vaga", "empresa", "time"}:
                return clean

    return "Não identificado"


def _detect_seniority(text: str) -> str:
    levels = (
        (r"\b(senior|senior|sr\.?)\b", "Sênior"),
        (r"\b(pleno|mid[- ]level)\b", "Pleno"),
        (r"\b(junior|junior|jr\.?)\b", "Júnior"),
        (r"\b(estagio|estagiari[oa]|trainee)\b", "Estágio/Trainee"),
    )
    normalized = _normalize(text)
    for pattern, label in levels:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return label
    return "Não identificada"


def _detect_modality(text: str) -> str:
    normalized = _normalize(text)
    if re.search(r"\b(hibrid[oa]|hybrid)\b", normalized):
        return "Híbrido"
    if re.search(r"\b(remot[oa]|home office|anywhere office)\b", normalized):
        return "Remoto"
    if re.search(r"\b(presencial|on[- ]site)\b", normalized):
        return "Presencial"
    return "Não identificada"


def _detect_location(lines: list[str], modality: str) -> str:
    patterns = (
        r"^(?:localizacao|local|cidade|location)\s*:\s*(.+)$",
        r"^(?:hibrido|presencial)\s+(?:em|no|na)\s+(.+)$",
    )

    for line in lines[:40]:
        normalized = _normalize(line)
        for pattern in patterns:
            match = re.match(pattern, normalized, flags=re.IGNORECASE)
            if match:
                value = line.split(":", 1)[-1] if ":" in line else match.group(1)
                return _clean_line(value)

    city_state = re.search(
        r"\b([A-ZÁ-Ú][A-Za-zÀ-ÿ' -]{2,40})\s*[-/]\s*([A-Z]{2})\b",
        "\n".join(lines[:40]),
    )
    if city_state:
        return f"{city_state.group(1).strip()} - {city_state.group(2)}"

    return "Remoto" if modality == "Remoto" else "Não identificada"


def _section_for_line(line: str) -> str | None:
    normalized = _normalize(line).rstrip(":")
    for section, headings in SECTION_HEADINGS.items():
        if any(normalized == heading or normalized.startswith(f"{heading}:") for heading in headings):
            return section
    return None


def _extract_sections(text: str) -> dict[str, list[str]]:
    result = {
        "responsibilities": [],
        "required_requirements": [],
        "nice_to_have": [],
    }
    current_section: str | None = None

    for raw_line in text.splitlines():
        clean = _clean_line(raw_line)
        if not clean:
            continue

        detected_section = _section_for_line(clean)
        if detected_section:
            current_section = detected_section
            if ":" in clean:
                inline_value = _clean_line(clean.split(":", 1)[1])
                if inline_value:
                    result[current_section].append(inline_value)
            continue

        normalized = _normalize(clean)
        if (
            current_section
            and len(clean) <= 70
            and clean.endswith(":")
        ):
            current_section = None
            continue

        if current_section and len(clean) <= 280:
            result[current_section].append(clean)
            continue

        if any(marker in normalized for marker in NICE_TO_HAVE_MARKERS):
            result["nice_to_have"].append(clean)
        elif any(marker in normalized for marker in REQUIRED_MARKERS):
            result["required_requirements"].append(clean)
        elif any(re.match(rf"^{verb}\b", normalized) for verb in RESPONSIBILITY_VERBS):
            result["responsibilities"].append(clean)

    return {key: _unique(value, 12) for key, value in result.items()}


def _extract_keywords(
    text: str,
    hard_skills: list[str],
    tools: list[str],
    soft_skills: list[str],
) -> list[str]:
    preferred = hard_skills + tools + soft_skills
    words = re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9+#.-]{2,}", text)
    normalized_words = [
        _normalize(word)
        for word in words
        if _normalize(word) not in KEYWORD_STOPWORDS and not word.isdigit()
    ]
    frequent = [
        word
        for word, count in Counter(normalized_words).most_common(20)
        if count >= 2
    ]
    return _unique(preferred + [word.title() for word in frequent], 15)


def _build_alerts(
    text: str,
    seniority: str,
    required_requirements: list[str],
    hard_skills: list[str],
    tools: list[str],
) -> list[str]:
    alerts: list[str] = []
    normalized = _normalize(text)

    if seniority == "Sênior":
        alerts.append(
            "A vaga indica senioridade alta; confirme tempo de experiência, autonomia e escopo esperados."
        )

    years = [
        int(value)
        for value in re.findall(
            r"\b(\d{1,2})\+?\s*anos?\s+de\s+experiencia\b",
            normalized,
        )
    ]
    if years and max(years) >= 4:
        alerts.append(
            f"A descrição pede até {max(years)} anos de experiência, o que pode limitar perfis júnior."
        )

    if not required_requirements:
        alerts.append(
            "Os requisitos obrigatórios não estão claramente separados na descrição."
        )

    if len(hard_skills) + len(tools) >= 10:
        alerts.append(
            "A vaga reúne muitas tecnologias; valide quais são realmente obrigatórias no processo seletivo."
        )

    if len(text.strip()) < 180:
        alerts.append(
            "A descrição é curta e pouco detalhada; confirme responsabilidades e critérios com o recrutador."
        )

    if not alerts:
        alerts.append("Nenhum alerta relevante foi identificado pela análise local.")

    return alerts


def _next_steps(analysis: dict[str, Any]) -> list[str]:
    steps = [
        "Confirme no anúncio original quais requisitos são eliminatórios e quais são diferenciais.",
        "Use as palavras-chave principais ao revisar seu currículo, sem adicionar experiências que você não possui.",
    ]
    if analysis["alerts"] and analysis["alerts"][0] != "Nenhum alerta relevante foi identificado pela análise local.":
        steps.append("Esclareça os alertas antes de priorizar a candidatura.")
    steps.append(
        "Na próxima etapa, esta análise poderá ser comparada com data/resume-analysis.md para gerar um relatório de aderência."
    )
    return steps


def analysis_to_markdown(analysis: dict[str, Any]) -> str:
    """Serializa a análise para o arquivo de estado legível pelo usuário."""

    def bullets(items: list[str]) -> str:
        return "\n".join(f"* {item}" for item in items) if items else "* Não identificado"

    return f"""# Análise da descrição da vaga

## Resumo

* Título: {analysis['title']}
* Empresa: {analysis['company']}
* Senioridade: {analysis['seniority']}
* Modalidade: {analysis['modality']}
* Localização: {analysis['location']}

## Palavras-chave principais

{bullets(analysis['keywords'])}

## Hard skills

{bullets(analysis['hard_skills'])}

## Soft skills

{bullets(analysis['soft_skills'])}

## Ferramentas

{bullets(analysis['tools'])}

## Responsabilidades

{bullets(analysis['responsibilities'])}

## Requisitos obrigatórios

{bullets(analysis['required_requirements'])}

## Requisitos desejáveis

{bullets(analysis['nice_to_have'])}

## Alertas

{bullets(analysis['alerts'])}

## Próximos passos sugeridos

{bullets(analysis['next_steps'])}
"""


class JobDescriptionAnalyzer:
    """Extrai sinais acionáveis sem depender de API externa."""

    def analyze(self, description: str) -> dict[str, Any]:
        text = description.strip()
        lines = _meaningful_lines(text)
        sections = _extract_sections(text)
        hard_skills = _find_terms(text, SKILL_PATTERNS)
        tools = _find_terms(text, TOOL_PATTERNS)
        soft_skills = _find_terms(text, SOFT_SKILL_PATTERNS)
        seniority = _detect_seniority(text)
        modality = _detect_modality(text)

        analysis: dict[str, Any] = {
            "title": _detect_title(lines),
            "company": _detect_company(lines),
            "seniority": seniority,
            "modality": modality,
            "location": _detect_location(lines, modality),
            "keywords": _extract_keywords(text, hard_skills, tools, soft_skills),
            "hard_skills": hard_skills,
            "soft_skills": soft_skills,
            "tools": tools,
            "responsibilities": sections["responsibilities"],
            "required_requirements": sections["required_requirements"],
            "nice_to_have": sections["nice_to_have"],
            "alerts": [],
            "next_steps": [],
        }
        analysis["alerts"] = _build_alerts(
            text,
            seniority,
            analysis["required_requirements"],
            hard_skills,
            tools,
        )
        analysis["next_steps"] = _next_steps(analysis)
        return analysis
