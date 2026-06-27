from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

import config
from routers.common import read_required
from session import (
    SessionPaths,
    get_session_lock,
    get_session_paths,
    write_text_atomic_async,
)

router = APIRouter()

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}
PDF_MAGIC = b"%PDF-"
DOCX_MAGIC = b"PK\x03\x04"
TEXT_SAMPLE_BYTES = 4096
ALLOWED_CONTENT_TYPES_BY_EXTENSION: dict[str, set[str]] = {
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
    ".txt": {"text/plain", "application/octet-stream"},
}

TECHNICAL_SKILLS: dict[str, list[str]] = {
    "Python": [r"\bpython\b"],
    "SQL": [r"\bsql\b"],
    "Power BI": [r"\bpower\s*bi\b"],
    "Excel": [r"\bexcel\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b"],
    "TypeScript": [r"\btypescript\b", r"\bts\b"],
    "React": [r"\breact\b", r"\breact\.js\b"],
    "Node": [r"\bnode\b", r"\bnode\.js\b"],
    "FastAPI": [r"\bfastapi\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "Git": [r"\bgit\b"],
    "GitHub": [r"\bgithub\b"],
    "Docker": [r"\bdocker\b"],
    "AWS": [r"\baws\b", r"\bamazon web services\b"],
    "Azure": [r"\bazure\b"],
    "Figma": [r"\bfigma\b"],
    "HTML": [r"\bhtml\b", r"\bhtml5\b"],
    "CSS": [r"\bcss\b", r"\bcss3\b"],
    "Tailwind": [r"\btailwind\b", r"\btailwind css\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "Machine Learning": [r"\bmachine learning\b", r"\bml\b"],
}

SOFT_SKILLS: dict[str, list[str]] = {
    "comunicação": [r"\bcomunica[cç][aã]o\b"],
    "trabalho em equipe": [r"\btrabalho em equipe\b", r"\bcolabora[cç][aã]o\b"],
    "liderança": [r"\blideran[cç]a\b"],
    "resolução de problemas": [
        r"\bresolu[cç][aã]o de problemas\b",
        r"\bproblem solving\b",
    ],
    "proatividade": [r"\bproatividade\b", r"\bproativo\b", r"\bproativa\b"],
    "pensamento crítico": [r"\bpensamento cr[ií]tico\b"],
    "organização": [r"\borganiza[cç][aã]o\b"],
    "adaptabilidade": [r"\badaptabilidade\b"],
    "empatia": [r"\bempatia\b"],
}

AREA_SKILLS: dict[str, set[str]] = {
    "Ciência de Dados": {
        "Python",
        "SQL",
        "Power BI",
        "Excel",
        "Pandas",
        "NumPy",
        "Machine Learning",
    },
    "Frontend": {
        "JavaScript",
        "TypeScript",
        "React",
        "HTML",
        "CSS",
        "Tailwind",
        "Figma",
    },
    "Backend": {
        "Python",
        "Node",
        "FastAPI",
        "Django",
        "Flask",
        "SQL",
        "Docker",
    },
    "Full Stack": {
        "JavaScript",
        "TypeScript",
        "React",
        "Node",
        "Python",
        "SQL",
        "Docker",
    },
    "DevOps": {"Docker", "AWS", "Azure", "GitHub"},
    "Design UI": {"Figma", "HTML", "CSS"},
    "Cibersegurança": {"Python", "Docker", "AWS", "Azure"},
}

AREA_TERMS: dict[str, list[str]] = {
    "Ciência de Dados": [
        r"\bdados\b",
        r"\bdata\b",
        r"\bbi\b",
        r"\banalista de dados\b",
    ],
    "Frontend": [r"\bfrontend\b", r"\bfront-end\b"],
    "Backend": [r"\bbackend\b", r"\bback-end\b"],
    "Full Stack": [r"\bfull stack\b", r"\bfullstack\b"],
    "DevOps": [r"\bdevops\b", r"\bsre\b", r"\bcloud\b"],
    "Design UI": [r"\bui\b", r"\bux\b", r"\bproduto digital\b"],
    "Gestão de Produtos": [
        r"\bproduct manager\b",
        r"\bproduto\b",
        r"\bproduct owner\b",
    ],
    "Marketing de Mídias Sociais": [
        r"\bmarketing digital\b",
        r"\bsocial media\b",
    ],
    "Cibersegurança": [
        r"\bseguran[cç]a\b",
        r"\bcybersecurity\b",
        r"\bciberseguran[cç]a\b",
    ],
}

TARGET_ROLES: dict[str, list[str]] = {
    "Ciência de Dados": [
        "Analista de Dados Júnior",
        "Estagiária em Dados",
        "Assistente de BI",
    ],
    "Frontend": [
        "Desenvolvedor Frontend Júnior",
        "Desenvolvedor React Júnior",
        "Desenvolvedor Web",
    ],
    "Backend": [
        "Desenvolvedor Backend Júnior",
        "Desenvolvedor API Júnior",
        "Desenvolvedor Python",
    ],
    "Full Stack": [
        "Desenvolvedor Full Stack Júnior",
        "Desenvolvedor Web",
        "Desenvolvedor de Aplicações",
    ],
    "DevOps": [
        "Analista DevOps Júnior",
        "Suporte Cloud",
        "SysAdmin Júnior",
    ],
    "Design UI": [
        "Designer UI Júnior",
        "Designer UX/UI",
        "Assistente de Design System",
    ],
    "Gestão de Produtos": [
        "Analista de Produto",
        "Product Owner Júnior",
        "Assistente de Produto",
    ],
    "Marketing de Mídias Sociais": [
        "Assistente de Marketing Digital",
        "Social Media Júnior",
        "Analista de Marketing Júnior",
    ],
    "Cibersegurança": [
        "Analista de Segurança Júnior",
        "Analista SOC",
        "Assistente de Segurança da Informação",
    ],
}


def _error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
        },
    )


def _invalidate_downstream_artifacts(paths: SessionPaths) -> None:
    for path in (
        paths.RESUME_MATCH_REPORT_FILE,
        paths.RESUME_TAILORING_SUGGESTIONS_FILE,
        paths.PDI_PLAN_FILE,
    ):
        path.unlink(missing_ok=True)


def _validate_upload_signature(
    content: bytes,
    extension: str,
    content_type: str | None,
) -> str | None:
    normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
    allowed_content_types = ALLOWED_CONTENT_TYPES_BY_EXTENSION.get(extension, set())

    if normalized_content_type and normalized_content_type not in allowed_content_types:
        return "Tipo de arquivo incompativel com o formato enviado."

    if extension == ".pdf" and not content.startswith(PDF_MAGIC):
        return "O arquivo PDF enviado nao possui uma assinatura valida."

    if extension == ".docx" and not content.startswith(DOCX_MAGIC):
        return "O arquivo DOCX enviado nao possui uma assinatura valida."

    if extension == ".txt":
        try:
            content[:TEXT_SAMPLE_BYTES].decode("utf-8-sig")
        except UnicodeDecodeError:
            return "O arquivo TXT enviado nao esta em UTF-8 valido."

    return None


def _find_terms(text: str, terms: dict[str, list[str]]) -> list[str]:
    found: list[str] = []

    for label, patterns in terms.items():
        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            found.append(label)

    return found


def _extract_txt(content: bytes) -> str:
    return content.decode("utf-8", errors="ignore").strip()


def _extract_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError(
            "A dependência pypdf não está instalada. Adicione pypdf ao requirements.txt."
        )

    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]

    return "\n".join(pages).strip()


def _extract_docx(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError(
            "A dependência python-docx não está instalada. Adicione python-docx ao requirements.txt."
        )

    document = Document(BytesIO(content))
    paragraphs = [
        paragraph.text
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    return "\n".join(paragraphs).strip()


def _extract_text(content: bytes, extension: str) -> str:
    if extension == ".txt":
        return _extract_txt(content)

    if extension == ".pdf":
        return _extract_pdf(content)

    if extension == ".docx":
        return _extract_docx(content)

    return ""


def _detect_name(text: str) -> str:
    match = re.search(r"(?im)^\s*nome\s*:\s*(.+)$", text)

    if match:
        return match.group(1).strip()[:80]

    for raw_line in text.splitlines()[:8]:
        line = raw_line.strip()

        if not line or len(line) > 80:
            continue

        if re.search(
            r"@|https?://|\d{4,}|curr[ií]culo|resume|linkedin|github",
            line,
            flags=re.IGNORECASE,
        ):
            continue

        words = [word for word in re.split(r"\s+", line) if word]

        if 2 <= len(words) <= 5 and all(
            re.match(r"^[A-Za-zÀ-ÿ'-]+$", word) for word in words
        ):
            return line

    return "não identificado"


def _estimate_level(text: str) -> str:
    checks = [
        (r"\b(s[eê]nior|senior|sr\.?)\b", "Sênior"),
        (r"\b(pleno|mid[- ]level)\b", "Pleno"),
        (r"\b(j[uú]nior|junior|jr\.?)\b", "Júnior"),
        (
            r"\b(est[aá]gio|estagi[aá]ri[oa]|trainee|primeiro emprego|estudante)\b",
            "Estágio/Júnior",
        ),
    ]

    for pattern, level in checks:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return level

    return "Precisa confirmar no quiz"


def _probable_areas(text: str, skills: list[str]) -> list[str]:
    scores: dict[str, int] = {area: 0 for area in AREA_SKILLS}
    skill_set = set(skills)

    for area, area_skills in AREA_SKILLS.items():
        scores[area] += len(skill_set & area_skills)

    for area, patterns in AREA_TERMS.items():
        scores.setdefault(area, 0)

        if any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns):
            scores[area] += 2

    ranked = [
        area
        for area, score in sorted(
            scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )
        if score > 0
    ]

    return ranked[:3]


def _collect_section_summary(
    text: str,
    patterns: list[str],
    fallback: str = "não identificado",
) -> str:
    lines: list[str] = []

    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())

        if len(line) < 8 or len(line) > 220:
            continue

        if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in patterns):
            lines.append(line)

        if len(lines) >= 4:
            break

    return " ".join(lines) if lines else fallback


def _professional_summary(
    areas: list[str],
    level: str,
    skills: list[str],
) -> str:
    if not areas and not skills:
        return "Não foi possível identificar um resumo profissional confiável a partir do currículo."

    area_text = areas[0] if areas else "área a confirmar"
    skill_text = ", ".join(skills[:6]) if skills else "habilidades a confirmar"

    return (
        f"Perfil com indícios de atuação em {area_text}, "
        f"nível {level}, com habilidades detectadas em {skill_text}."
    )


def _fields_to_confirm(analysis: dict[str, Any]) -> list[str]:
    fields = [
        "Localização",
        "Preferência de trabalho",
        "Objetivo de carreira",
    ]

    if not analysis["probable_areas"]:
        fields.append("Área de interesse")

    if analysis["estimated_level"] == "Precisa confirmar no quiz":
        fields.append("Nível de experiência")

    if not analysis["technical_skills"]:
        fields.append("Habilidades técnicas")

    if not analysis["soft_skills"]:
        fields.append("Soft skills")

    return fields


def _analyze_resume(text: str) -> dict[str, Any]:
    technical_skills = _find_terms(text, TECHNICAL_SKILLS)
    soft_skills = _find_terms(text, SOFT_SKILLS)
    probable_areas = _probable_areas(text, technical_skills)
    estimated_level = _estimate_level(text)
    suggested_roles = TARGET_ROLES.get(probable_areas[0], []) if probable_areas else []

    analysis: dict[str, Any] = {
        "detected_name": _detect_name(text),
        "professional_summary": "",
        "probable_areas": probable_areas,
        "estimated_level": estimated_level,
        "technical_skills": technical_skills,
        "soft_skills": soft_skills,
        "experience_summary": _collect_section_summary(
            text,
            [
                r"\bexperi[eê]ncia\b",
                r"\bempresa\b",
                r"\bprojeto\b",
                r"\banalista\b",
                r"\bdesenvolvedor",
            ],
        ),
        "education_summary": _collect_section_summary(
            text,
            [
                r"\bforma[cç][aã]o\b",
                r"\bgradua[cç][aã]o\b",
                r"\bfaculdade\b",
                r"\buniversidade\b",
                r"\bcurso\b",
                r"\bensino\b",
            ],
        ),
        "suggested_target_roles": suggested_roles,
        "strengths": [],
        "improvement_points": [],
        "fields_to_confirm": [],
    }

    analysis["professional_summary"] = _professional_summary(
        probable_areas,
        estimated_level,
        technical_skills,
    )

    strengths: list[str] = []

    if technical_skills:
        strengths.append(
            f"Habilidades técnicas detectadas: {', '.join(technical_skills[:8])}"
        )

    if soft_skills:
        strengths.append(
            f"Soft skills mencionadas: {', '.join(soft_skills[:5])}"
        )

    if probable_areas:
        strengths.append(f"Área provável identificada: {probable_areas[0]}")

    analysis["strengths"] = strengths or [
        "Poucas evidências objetivas foram identificadas no currículo."
    ]

    improvements: list[str] = []

    if not technical_skills:
        improvements.append("Listar habilidades técnicas de forma mais explícita.")

    if analysis["experience_summary"] == "não identificado":
        improvements.append("Detalhar experiências, projetos ou responsabilidades recentes.")

    if analysis["education_summary"] == "não identificado":
        improvements.append("Informar formação, cursos ou certificações relevantes.")

    if estimated_level == "Precisa confirmar no quiz":
        improvements.append("Confirmar nível de experiência no quiz.")

    analysis["improvement_points"] = improvements or [
        "Confirmar no quiz se as informações detectadas estão corretas."
    ]

    analysis["fields_to_confirm"] = _fields_to_confirm(analysis)

    return analysis


def _as_list(items: list[str]) -> str:
    if not items:
        return "- não identificado"

    return "\n".join(f"- {item}" for item in items)


def _analysis_to_markdown(analysis: dict[str, Any]) -> str:
    return f"""Nome detectado: {analysis['detected_name']}

Resumo profissional:
{analysis['professional_summary']}

Áreas prováveis:
{_as_list(analysis['probable_areas'])}

Nível estimado:
{analysis['estimated_level']}

Habilidades técnicas detectadas:
{_as_list(analysis['technical_skills'])}

Soft skills detectadas:
{_as_list(analysis['soft_skills'])}

Experiências detectadas:
{analysis['experience_summary']}

Formação detectada:
{analysis['education_summary']}

Funções alvo sugeridas:
{_as_list(analysis['suggested_target_roles'])}

Pontos fortes:
{_as_list(analysis['strengths'])}

Pontos de melhoria:
{_as_list(analysis['improvement_points'])}

Campos que precisam de confirmação no quiz:
{_as_list(analysis['fields_to_confirm'])}

Concluído: true
"""


def _analysis_from_markdown(content: str) -> dict[str, Any] | None:
    scalar_fields = {
        "Nome detectado": "detected_name",
        "Nível estimado": "estimated_level",
        "Experiências detectadas": "experience_summary",
        "Formação detectada": "education_summary",
    }
    list_fields = {
        "Áreas prováveis": "probable_areas",
        "Habilidades técnicas detectadas": "technical_skills",
        "Soft skills detectadas": "soft_skills",
        "Funções alvo sugeridas": "suggested_target_roles",
        "Pontos fortes": "strengths",
        "Pontos de melhoria": "improvement_points",
        "Campos que precisam de confirmação no quiz": "fields_to_confirm",
    }
    result: dict[str, Any] = {
        "detected_name": "",
        "professional_summary": "",
        "probable_areas": [],
        "estimated_level": "",
        "technical_skills": [],
        "soft_skills": [],
        "experience_summary": "",
        "education_summary": "",
        "suggested_target_roles": [],
        "strengths": [],
        "improvement_points": [],
        "fields_to_confirm": [],
    }
    lines = content.splitlines()
    current_list = ""

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            continue

        if line == "Resumo profissional:":
            result["professional_summary"] = next(
                (
                    candidate.strip()
                    for candidate in lines[index + 1 :]
                    if candidate.strip()
                ),
                "",
            )
            current_list = ""
            continue

        heading = line.rstrip(":")
        if line.endswith(":") and heading in list_fields:
            current_list = list_fields[heading]
            continue

        if line.endswith(":") and heading in scalar_fields:
            result[scalar_fields[heading]] = next(
                (
                    candidate.strip()
                    for candidate in lines[index + 1 :]
                    if candidate.strip()
                ),
                "",
            )
            current_list = ""
            continue

        if line.startswith(("- ", "* ")) and current_list:
            value = line[2:].strip()
            if value.casefold() != "não identificado":
                result[current_list].append(value)
            continue

        if ":" in line and not line.startswith(("-", "*")):
            key, _, value = line.partition(":")
            field = scalar_fields.get(key.strip())
            if field:
                result[field] = value.strip()

    if not result["technical_skills"] and not result["soft_skills"]:
        return None

    return result


def _parse_profile(content: str) -> dict[str, str]:
    profile: dict[str, str] = {}

    for line in content.splitlines():
        if ":" not in line:
            continue

        key, _, value = line.partition(":")
        profile[key.strip()] = value.strip()

    return profile


def _profile_to_markdown(profile: dict[str, str]) -> str:
    ordered_fields = [
        "Área de interesse",
        "Nível de experiência",
        "Preferências de trabalho",
        "Localização",
        "Soft skills",
        "Objetivo de carreira",
        "Habilidades atuais",
        "Funções alvo",
        "Concluído",
    ]

    return "\n".join(f"{field}: {profile.get(field, '')}" for field in ordered_fields)


def _is_empty(value: str | None) -> bool:
    if value is None:
        return True

    normalized = value.strip().lower()

    return normalized in {
        "",
        "não identificado",
        "precisa confirmar no quiz",
        "false",
    }


def _profile_suggestions(analysis: dict[str, Any]) -> dict[str, str]:
    """Mapeia a análise do currículo para sugestões de campos do perfil.

    Função pura: não lê nem grava nada. Campos sem evidência confiável saem
    como string vazia (e são ignorados pelos chamadores).
    """
    return {
        "Área de interesse": (
            analysis["probable_areas"][0] if analysis["probable_areas"] else ""
        ),
        "Nível de experiência": (
            analysis["estimated_level"]
            if analysis["estimated_level"] != "Precisa confirmar no quiz"
            else ""
        ),
        "Soft skills": ", ".join(analysis["soft_skills"]),
        "Habilidades atuais": ", ".join(analysis["technical_skills"]),
        "Funções alvo": ", ".join(analysis["suggested_target_roles"]),
    }


def _profile_suggestions_preview(
    analysis: dict[str, Any],
    existing_profile: str,
) -> list[dict[str, Any]]:
    """Monta um preview NÃO destrutivo das sugestões (não grava o perfil).

    Cada item traz o valor atual, o sugerido, se é aplicável (campo vazio) e se
    há conflito (campo preenchido com valor diferente do sugerido).
    """
    profile = _parse_profile(existing_profile)
    preview: list[dict[str, Any]] = []
    for field, suggested in _profile_suggestions(analysis).items():
        if not suggested:
            continue
        current = profile.get(field, "")
        preview.append(
            {
                "field": field,
                "source": "curriculo",
                "current_value": current,
                "suggested_value": suggested,
                "applicable": _is_empty(current),
                "conflict": (not _is_empty(current))
                and current.strip() != suggested.strip(),
            }
        )
    return preview


@router.get("/latest")
async def get_latest_resume_analysis(paths: SessionPaths = Depends(get_session_paths)):
    try:
        content = paths.RESUME_ANALYSIS_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"detail": "Nenhum currículo foi analisado ainda."},
        )

    analysis = _analysis_from_markdown(content)
    if analysis is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Nenhuma análise de currículo válida foi encontrada."},
        )

    return analysis


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    paths: SessionPaths = Depends(get_session_paths),
):
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        return _error("Formato inválido. Envie um arquivo PDF, DOCX ou TXT.")

    content = await file.read(config.MAX_RESUME_UPLOAD_SIZE + 1)

    if len(content) > config.MAX_RESUME_UPLOAD_SIZE:
        return _error("Arquivo grande demais. O limite e de 5 MB.", status_code=413)

    if not content:
        return _error("O arquivo está vazio. Envie um currículo com texto legível.")

    signature_error = _validate_upload_signature(
        content,
        extension,
        file.content_type,
    )
    if signature_error:
        return _error(signature_error)

    try:
        extracted_text = _extract_text(content, extension)
    except RuntimeError as exc:
        return _error(str(exc), status_code=500)
    except Exception:
        return _error(
            "Não foi possível ler o arquivo. Envie um PDF, DOCX ou TXT com texto legível."
        )

    if len(extracted_text.strip()) < 20:
        return _error("Não foi possível extrair texto suficiente do currículo.")

    analysis = _analyze_resume(extracted_text)

    async with get_session_lock(paths.session_id):
        await write_text_atomic_async(
            paths.RESUME_ANALYSIS_FILE,
            _analysis_to_markdown(analysis),
        )
        _invalidate_downstream_artifacts(paths)

        try:
            existing_profile = paths.PROFILE_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            existing_profile = ""

    suggestions_preview = _profile_suggestions_preview(analysis, existing_profile)

    return {
        "success": True,
        "message": "Currículo analisado com sucesso.",
        "analysis": analysis,
        "profile_updated": False,
        "profile_confirmation_required": any(
            item["applicable"] for item in suggestions_preview
        ),
        "profile_suggestions": suggestions_preview,
    }


class ApplyProfileRequest(BaseModel):
    confirm: bool = False
    fields: list[str] | None = None


@router.post("/apply-profile")
async def apply_profile_from_resume(
    body: ApplyProfileRequest | None = None,
    paths: SessionPaths = Depends(get_session_paths),
):
    request = body or ApplyProfileRequest()
    if not request.confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmação explícita necessária para atualizar o perfil com dados do currículo.",
        )
    content = read_required(
        paths.RESUME_ANALYSIS_FILE,
        "Envie e analise um currículo primeiro.",
        "A análise do currículo está vazia ou inválida. Envie o currículo novamente.",
    )
    analysis = _analysis_from_markdown(content)
    if analysis is None:
        raise HTTPException(
            status_code=409,
            detail="A análise do currículo está inválida ou corrompida. Envie o currículo novamente.",
        )
    suggestions = _profile_suggestions(analysis)
    approved = (
        request.fields
        if request.fields is not None
        else [field for field, value in suggestions.items() if value]
    )
    async with get_session_lock(paths.session_id):
        try:
            existing = paths.PROFILE_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            existing = ""
        profile = _parse_profile(existing)
        updated_fields: list[str] = []
        for field in approved:
            suggested = suggestions.get(field, "")
            if suggested and profile.get(field, "") != suggested:
                profile[field] = suggested
                updated_fields.append(field)
        required_fields = [
            "Área de interesse",
            "Nível de experiência",
            "Preferências de trabalho",
            "Localização",
            "Soft skills",
            "Objetivo de carreira",
            "Habilidades atuais",
        ]
        profile["Concluído"] = (
            "true"
            if all(not _is_empty(profile.get(field)) for field in required_fields)
            else "false"
        )
        await write_text_atomic_async(
            paths.PROFILE_FILE,
            _profile_to_markdown(profile),
        )
    return {"success": True, "updated_fields": updated_fields, "profile": profile}
