"""Reconciliação heurística entre perfil, currículo e vaga.

Detecta conflitos entre os três artefatos que o usuário mantém ao longo da
jornada (perfil declarado no quiz, currículo analisado e vaga analisada) e
indica qual fonte deve prevalecer conforme o "foco da candidatura".

É puramente heurístico (mesma filosofia do ``resume_matcher``): sem LLM, sem
IO, sem dependência de rede. Tudo opera sobre strings Markdown já geradas.
O par currículo×vaga não é recalculado aqui — ele já existe em
``ResumeMatcher.match`` e é reusado para compor o resumo e o score.
"""

from __future__ import annotations

import re
from typing import Any

# Reaproveita os helpers canônicos do matcher para manter consistência de
# normalização/aliasing e evitar falsos conflitos (ex.: "powerbi" vs "Power BI").
from agents.resume_matcher import (
    SENIORITY_ORDER,
    ResumeMatcher,
    _canonical,
    _normalize,
    _parse_markdown,
    _unique,
    match_report_from_markdown,
    validate_job_analysis,
    validate_resume_analysis,
)

# Alias para deixar explícito que currículo/vaga são parseados pelo _parse_markdown
# do matcher (que entende bullets e seções, ao contrário do perfil plano).
_parse_artifact = _parse_markdown


# Valores considerados "ausentes"/não-informativos nas linhas do perfil.
INVALID_MARKERS = {
    "",
    "nao informado",
    "não informado",
    "nao identificado",
    "não identificado",
    "nao analisada",
    "não analisada",
    "nenhuma",
    "nenhum",
    "nenhum item",
}

# Opções válidas para o foco da candidatura. Chaves normalizadas (sem acento,
# casefold) para tolerar variação de digitação no user-profile.md.
FOCUS_OPTIONS = {"perfil", "curriculo", "vaga"}

# Chaves do perfil consideradas obrigatórias para que a reconciliação faça
# sentido (espelha o que o quiz produz em user-profile.md).
_PROFILE_REQUIRED_KEYS = (
    "Área de interesse",
    "Nível de experiência",
    "Habilidades atuais",
)

# Tipos de campo para rotear a comparação dentro de _compare_field.
_FIELD_LEVEL = "level"
_FIELD_AREA = "area"
_FIELD_SKILLS = "skills"
_FIELD_SCALAR = "scalar"

# Mapeamento de campos comparáveis perfil↔currículo.
# (rótulo, chave_perfil, chave_artefato, tipo)
_PROFILE_RESUME_FIELDS = (
    ("Área", "Área de interesse", "probable_areas", _FIELD_AREA),
    ("Nível", "Nível de experiência", "nivel_estimado", _FIELD_LEVEL),
    ("Habilidades técnicas", "Habilidades atuais", "technical_skills", _FIELD_SKILLS),
    ("Soft skills", "Soft skills", "resume_soft_skills", _FIELD_SKILLS),
    ("Funções alvo", "Funções alvo", "target_roles", _FIELD_AREA),
)

# Mapeamento de campos comparáveis perfil↔vaga.
# As chaves do artefato são as geradas pelo _parse_markdown do matcher ao
# ler os bullets PT da vaga (analysis_to_markdown usa "Senioridade:",
# "Modalidade:", "Localização:"), normalizadas para snake_case sem acento.
_PROFILE_JOB_FIELDS = (
    ("Nível", "Nível de experiência", "senioridade", _FIELD_LEVEL),
    ("Habilidades técnicas", "Habilidades atuais", "hard_skills", _FIELD_SKILLS),
    ("Ferramentas", "Habilidades atuais", "tools", _FIELD_SKILLS),
    ("Soft skills", "Soft skills", "soft_skills", _FIELD_SKILLS),
    ("Modalidade", "Preferências de trabalho", "modalidade", _FIELD_SCALAR),
    ("Localização", "Localização", "localizacao", _FIELD_SCALAR),
)


# ── Perfil (user-profile.md é chave:valor, formato diferente dos outros) ─────


def _parse_profile(content: str) -> dict[str, str]:
    """Converte o user-profile.md (linhas `chave: valor`) em dict.

    Diferente do _parse_markdown do matcher, o perfil não tem seções nem
    bullets — é plano. Mantém as chaves com acento/case originais, igual ao
    ``routers/profile.py::_parse_md_to_dict``, para casar com as constantes acima.
    """
    result: dict[str, str] = {}
    for line in content.splitlines():
        if ":" in line and not line.startswith("#"):
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def _profile_value(profile: dict[str, str], key: str) -> str:
    """Valor do perfil normalizado; '' se ausente ou marcado como inválido."""
    raw = profile.get(key, "").strip()
    if _normalize(raw) in INVALID_MARKERS:
        return ""
    return raw


def _split_csv(value: str) -> list[str]:
    """Quebra uma string CSV (skills/funções) numa lista canônica e dedup."""
    if not value:
        return []
    parts = [part.strip() for part in re.split(r"[,;]", value) if part.strip()]
    return _known_values(parts)


def _known_values(items: list[str]) -> list[str]:
    """Remove placeholders como 'Não identificado' antes de comparar listas."""
    return [
        item
        for item in _unique(items)
        if _normalize(item) not in INVALID_MARKERS
    ]


def _list_field(data: dict[str, Any], key: str) -> list[str]:
    """Extrai uma lista de um dict do _parse_markdown (robusto a escalar/lista)."""
    value = data.get(key, [])
    if isinstance(value, list):
        return _known_values([str(item) for item in value])
    return _split_csv(str(value)) if value else []


def _scalar_field(data: dict[str, Any], key: str) -> str:
    """Extrai um valor escalar de um dict do _parse_markdown."""
    value = data.get(key, "")
    if isinstance(value, list):
        return ", ".join(str(v) for v in value).strip()
    raw = str(value).strip()
    return "" if _normalize(raw) in INVALID_MARKERS else raw


# ── Comparações elementares ──────────────────────────────────────────────────


def _seniority_rank(level: str) -> int | None:
    return SENIORITY_ORDER.get(_normalize(level))


def _levels_match(a: str, b: str) -> bool:
    """True se dois níveis são compatíveis (mesmo rank ordinal)."""
    ra, rb = _seniority_rank(a), _seniority_rank(b)
    if ra is None or rb is None:
        # Se algum for não-mapeável, só há conflito se ambos forem
        # não-vazios e diferentes em texto normalizado.
        return not a or not b or _normalize(a) == _normalize(b)
    return ra == rb


def _set_overlap(a: list[str], b: list[str]) -> tuple[list[str], list[str], list[str]]:
    """Retorna (comuns, só_em_a, só_em_b) entre duas listas, via canonical."""
    keys_a = {_normalize(_canonical(x)): x for x in a}
    keys_b = {_normalize(_canonical(x)): x for x in b}
    common = [keys_a[k] for k in keys_a.keys() & keys_b.keys()]
    only_a = [keys_a[k] for k in keys_a.keys() - keys_b.keys()]
    only_b = [keys_b[k] for k in keys_b.keys() - keys_a.keys()]
    return _unique(common), _unique(only_a), _unique(only_b)


def _area_matches(profile_area: str, areas: list[str]) -> bool:
    """Checa se a área/função do perfil aparece (normalizada) entre as opções."""
    if not profile_area:
        return False
    target = _normalize(profile_area)
    return any(
        target in _normalize(area) or _normalize(area) in target
        for area in areas
        if area
    )


def _compare_field(
    profile: dict[str, str],
    artifact: dict[str, Any],
    field: tuple[str, str, str, str],
) -> tuple[dict[str, str] | None, str | None]:
    """Compara UM campo do perfil contra o artefato.

    Retorna (conflito_ou_None, alinhamento_ou_None).
    """
    label, profile_key, artifact_key, kind = field
    profile_raw = _profile_value(profile, profile_key)

    if kind == _FIELD_LEVEL:
        other_raw = _scalar_field(artifact, artifact_key)
        if not profile_raw or not other_raw:
            return None, None
        if _levels_match(profile_raw, other_raw):
            return None, f"Nível alinhado ({profile_raw} ≈ {other_raw})"
        return ({
 "field": label, "profile_value": profile_raw, "other_value": other_raw, "severity": "alta"}), None

    if kind == _FIELD_AREA:
        other_list = _list_field(artifact, artifact_key)
        if not profile_raw and not other_list:
            return None, None
        if _area_matches(profile_raw, other_list):
            return None, f"{label} alinhada entre perfil e artefato"
        if profile_raw and other_list:
            return ({
 "field": label, "profile_value": profile_raw, "other_value": ", ".join(other_list[:4]), "severity": "media"}), None
        return None, None

    if kind == _FIELD_SKILLS:
        other_list = _list_field(artifact, artifact_key)
        profile_skills = _split_csv(profile_raw)
        if not profile_skills and not other_list:
            return None, None
        common, _, _ = _set_overlap(profile_skills, other_list)
        if profile_skills and other_list and not common:
            return ({
 "field": label, "profile_value": ", ".join(profile_skills[:4]), "other_value": ", ".join(other_list[:4]), "severity": "alta"}), None
        if common:
            return None, f"{label} com interseção em {', '.join(common[:3])}"
        return None, None

    # _FIELD_SCALAR (modality / location)
    other_raw = _scalar_field(artifact, artifact_key)
    if not profile_raw or not other_raw:
        return None, None
    if _normalize(profile_raw) != _normalize(other_raw):
        return ({"field": label, "profile_value": profile_raw, "other_value": other_raw, "severity": "baixa"}), None
    return None, f"{label} alinhada"


def _detect_pair_conflicts(
    profile: dict[str, str],
    artifact: dict[str, Any],
    fields: tuple[tuple[str, str, str, str], ...],
) -> tuple[list[dict[str, str]], list[str]]:
    """Compara o perfil contra um artefato (currículo ou vaga)."""
    conflicts: list[dict[str, str]] = []
    aligned: list[str] = []
    for field in fields:
        conflict, alignment = _compare_field(profile, artifact, field)
        if conflict:
            conflicts.append(conflict)
        if alignment:
            aligned.append(alignment)
    return conflicts, aligned


# ── Foco da candidatura ──────────────────────────────────────────────────────


def parse_focus(profile_content: str) -> str | None:
    """Lê a linha `Foco da candidatura: {perfil|currículo|vaga}` do perfil.

    Retorna o foco normalizado (sem acento, casefold) ou ``None`` se
    ausente/inválido. Aceita "currículo" (com acento) ou "curriculo".
    """
    profile = _parse_profile(profile_content)
    return normalize_focus(profile.get("Foco da candidatura", ""))


def normalize_focus(value: str | None) -> str | None:
    """Normaliza foco informado pelo perfil/API; None se ausente ou inválido."""
    raw = _normalize(value or "").strip()
    return raw if raw in FOCUS_OPTIONS else None


# ── Recomendações conforme o foco ────────────────────────────────────────────


def _focus_recommendations(
    focus: str,
    profile_resume_conflicts: list[dict[str, str]],
    profile_job_conflicts: list[dict[str, str]],
) -> list[str]:
    """Traduz conflitos em ações conforme o foco escolhido."""
    recs: list[str] = []

    if focus == "curriculo":
        if profile_resume_conflicts:
            campos = ", ".join({c["field"] for c in profile_resume_conflicts})
            recs.append(
                f"Atualize o perfil (quiz) para refletir o currículo — divergências em: {campos}."
            )
        if profile_job_conflicts:
            campos = ", ".join({c["field"] for c in profile_job_conflicts})
            recs.append(
                f"A vaga difere do currículo em {campos}; mantenha o currículo como "
                "verdade e trate a diferença como lacuna a desenvolver."
            )
    elif focus == "vaga":
        if profile_job_conflicts:
            campos = ", ".join({c["field"] for c in profile_job_conflicts})
            recs.append(
                f"Alinhe perfil e currículo ao que a vaga pede: {campos}. "
                "Ajuste o que for declaração (perfil) e planeje o que for lacuna real."
            )
        if profile_resume_conflicts:
            recs.append(
                "Antes de ajustar o perfil, confirme se o currículo está atualizado; "
                "conflitos perfil↔currículo podem indicar currículo desatualizado."
            )
    else:  # focus == "perfil"
        if profile_resume_conflicts or profile_job_conflicts:
            recs.append(
                "Mantenha o perfil como referência. Revise o currículo para reforçar a "
                "narrativa declarada e use a vaga apenas para identificar lacunas reais."
            )

    return recs or [
        "Nenhuma ação obrigatória: perfil, currículo e vaga estão coerentes "
        "com o foco escolhido."
    ]


# ── Score, levels e próximos passos ──────────────────────────────────────────


def _consistency_score(
    conflicts: list[dict[str, str]],
    aligned: list[str],
    match_score: int,
) -> int:
    """Agrega conflitos + alinhamentos + match num score 0–100.

    Pesos: 50% match currículo×vaga, 30% ausência de conflitos, 20% alinhamentos.
    """
    severity_weight = {"alta": 3, "media": 2, "baixa": 1}
    conflict_penalty = sum(
        severity_weight.get(c.get("severity", "media"), 2) for c in conflicts
    )
    penalty = min(conflict_penalty * 3, 30)  # limitado a 30 pontos
    aligned_bonus = min(len(aligned) * 2, 20)
    raw = (match_score * 0.5) + (70 - penalty) * 0.3 + aligned_bonus * 0.2
    return max(0, min(100, round(raw)))


def _consistency_level(score: int) -> str:
    if score >= 80:
        return "coerente"
    if score >= 60:
        return "pequenas divergências"
    if score >= 40:
        return "divergências relevantes"
    return "inconsistente"


def _resume_job_summary(match_report: dict[str, Any]) -> str:
    if not match_report:
        return "Sem relatório de aderência currículo×vaga disponível."
    score = match_report.get("overall_score", 0)
    level = match_report.get("readiness_level", "não calculado")
    return f"Aderência currículo×vaga: {score}/100 ({level})."


def _next_steps(focus: str, conflicts: list[dict[str, str]], match_score: int) -> list[str]:
    steps: list[str] = []
    if conflicts:
        fields = ", ".join(sorted({c["field"] for c in conflicts}))
        steps.append(
            f"Resolver divergências em: {fields}, priorizando o foco em '{focus}'."
        )
    if match_score < 60:
        steps.append(
            "A aderência currículo×vaga está baixa; considere revisar o currículo "
            "ou buscar uma vaga mais alinhada antes de avançar."
        )
    steps.append(
        "Revisar user-profile.md para refletir a fonte de verdade escolhida como foco."
    )
    return steps


# ── Classe principal ─────────────────────────────────────────────────────────


class Reconciler:
    """Compara os três artefatos e devolve um diagnóstico de consistência."""

    def __init__(self) -> None:
        # Reusa o matcher para o par currículo×vaga (não recalcula).
        self._matcher = ResumeMatcher()

    def reconcile(
        self,
        profile_content: str,
        resume_content: str,
        job_content: str,
        match_content: str | None = None,
        focus: str | None = None,
    ) -> dict[str, Any]:
        profile = _parse_profile(profile_content)
        resume = _parse_artifact(resume_content)
        job = _parse_artifact(job_content)

        # Foco: parâmetro explícito > linha no perfil > default "vaga".
        explicit_focus = normalize_focus(focus)
        if focus is not None and explicit_focus is None:
            raise ValueError("Foco da candidatura inválido.")
        resolved_focus = explicit_focus or parse_focus(profile_content) or "vaga"

        # Conflitos perfil↔currículo e perfil↔vaga.
        pr_conflicts, pr_aligned = _detect_pair_conflicts(
            profile, resume, _PROFILE_RESUME_FIELDS
        )
        pj_conflicts, pj_aligned = _detect_pair_conflicts(
            profile, job, _PROFILE_JOB_FIELDS
        )

        # Reusa o match currículo×vaga (já existe em ResumeMatcher, não duplica).
        match_report: dict[str, Any] = {}
        if match_content:
            match_report = match_report_from_markdown(match_content) or {}
        if not match_report:
            match_report = self._matcher.match(job_content, resume_content)
        match_score = match_report.get("overall_score", 0)

        all_conflicts = pr_conflicts + pj_conflicts
        all_aligned = pr_aligned + pj_aligned
        consistency_score = _consistency_score(all_conflicts, all_aligned, match_score)

        return {
            "focus": resolved_focus,
            "consistency_score": consistency_score,
            "consistency_level": _consistency_level(consistency_score),
            "profile_resume_conflicts": pr_conflicts,
            "profile_job_conflicts": pj_conflicts,
            "resume_job_summary": _resume_job_summary(match_report),
            "match_score": match_score,
            "aligned_fields": all_aligned,
            "focus_recommendations": _focus_recommendations(
                resolved_focus, pr_conflicts, pj_conflicts
            ),
            "next_steps": _next_steps(resolved_focus, all_conflicts, match_score),
        }


# ── Serialização Markdown ────────────────────────────────────────────────────


def _conflict_lines(conflicts: list[dict[str, str]]) -> list[str]:
    if not conflicts:
        return ["* Nenhum conflito detectado"]
    lines: list[str] = []
    for c in conflicts:
        # Sem ":" no bullet — o _parse_markdown do matcher trata bullets com ":"
        # como chave-valor e não os adiciona à seção, o que quebraria o
        # round-trip. Aspas delimitam os valores para o regex de restauração.
        lines.append(
            f"* {c['field']} — perfil \"{c['profile_value']}\" "
            f"| outro \"{c['other_value']}\" | severidade \"{c['severity']}\""
        )
    return lines


def reconciliation_to_markdown(result: dict[str, Any]) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"* {item}" for item in items) if items else "* Nenhum item"

    return f"""# Reconciliação entre perfil, currículo e vaga

## Resumo

* Score de consistência: {result['consistency_score']}/100
* Nível de consistência: {result['consistency_level']}
* Foco da candidatura: {result['focus']}
* Aderência currículo x vaga: {result['match_score']}/100

## Visão geral currículo x vaga

* {result['resume_job_summary']}

## Conflitos perfil e currículo

{bullets(_conflict_lines(result['profile_resume_conflicts']))}

## Conflitos perfil e vaga

{bullets(_conflict_lines(result['profile_job_conflicts']))}

## Campos alinhados

{bullets(result['aligned_fields'])}

## Recomendações conforme o foco

{bullets(result['focus_recommendations'])}

## Próximos passos recomendados

{bullets(result['next_steps'])}
"""


def _restore_conflicts(lines: list[str]) -> list[dict[str, str]]:
    """Reconstrói a lista de conflitos a partir das linhas do Markdown.

    Aceita o formato "* Campo — perfil \"X\" | outro \"Y\" | severidade \"Z\"".
    """
    conflicts: list[dict[str, str]] = []
    for line in lines:
        if "nenhum conflito" in _normalize(line):
            continue
        match = re.match(
            r"^(.*?)\s*[—-]\s*perfil\s*\"(.*?)\"\s*\|\s*outro\s*\"(.*?)\"\s*"
            r"\|\s*severidade\s*\"(.*?)\"\s*$",
            line,
        )
        if match:
            conflicts.append({
                "field": match.group(1).strip(),
                "profile_value": match.group(2).strip(),
                "other_value": match.group(3).strip(),
                "severity": match.group(4).strip(),
            })
    return conflicts


def _parse_reconciliation_sections(content: str) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Parser dedicado para o relatório de reconciliação.

    O ``_parse_markdown`` do matcher ignora seções fora de SECTION_ALIASES,
    então não serve para reparsar este Markdown. Aqui capturamos:
      - escalares da seção "## Resumo" (linhas "* chave: valor")
      - listas por seção (qualquer "## Heading" → lista de bullets)
    Retorna (escalares, {heading_normalizado: [bullets]}).
    """
    scalars: dict[str, str] = {}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## "):
            current = _normalize(line[3:]).replace(" ", "_")
            sections.setdefault(current, [])
            continue
        if line.startswith("* "):
            value = line[2:].strip()
            if current == "resumo" and ":" in value:
                key, _, val = value.partition(":")
                scalars[_normalize(key).replace(" ", "_")] = val.strip()
            elif current:
                sections[current].append(value)
    return scalars, sections


def reconciliation_from_markdown(content: str) -> dict[str, Any] | None:
    """Restaura um relatório persistido por ``reconciliation_to_markdown``."""
    scalars, sections = _parse_reconciliation_sections(content)

    score_match = re.match(
        r"^(\d{1,3})/100$",
        str(scalars.get("score_de_consistencia", "")),
    )
    if not score_match:
        return None

    def score_from(label: str) -> int:
        value = str(scalars.get(label, "0"))
        match = re.match(r"^(\d{1,3})/", value)
        return int(match.group(1)) if match else 0

    return {
        "focus": str(scalars.get("foco_da_candidatura", "vaga")),
        "consistency_score": int(score_match.group(1)),
        "consistency_level": str(scalars.get("nivel_de_consistencia", "não calculado")),
        "profile_resume_conflicts": _restore_conflicts(
            sections.get("conflitos_perfil_e_curriculo", [])
        ),
        "profile_job_conflicts": _restore_conflicts(
            sections.get("conflitos_perfil_e_vaga", [])
        ),
        "resume_job_summary": " ".join(
            sections.get("visao_geral_curriculo_x_vaga", [])
        ),
        "match_score": score_from("aderencia_curriculo_x_vaga"),
        "aligned_fields": sections.get("campos_alinhados", []),
        "focus_recommendations": sections.get("recomendacoes_conforme_o_foco", []),
        "next_steps": sections.get("proximos_passos_recomendados", []),
    }


# ── Validadores ──────────────────────────────────────────────────────────────


def validate_profile(content: str) -> bool:
    """Valida um user-profile.md: concluído + chaves obrigatórias preenchidas."""
    profile = _parse_profile(content)
    if _normalize(profile.get("Concluído", "")) != "true":
        return False
    for key in _PROFILE_REQUIRED_KEYS:
        if not _profile_value(profile, key):
            return False
    return True
