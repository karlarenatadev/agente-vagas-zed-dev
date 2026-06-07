"""
Router de perfil — endpoints REST para leitura do perfil do usuário.
Usado pelo frontend para exibir o painel de stats do personagem.
"""

from fastapi import APIRouter, Response

import config

router = APIRouter()


def _parse_md_to_dict(content: str) -> dict[str, str]:
    """Converte arquivo markdown de chave: valor em dicionário."""
    result: dict[str, str] = {}
    for line in content.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


@router.get("/")
async def get_profile(response: Response):
    """Retorna o perfil do usuário como JSON."""
    response.headers["Cache-Control"] = "no-store"
    content = ""
    try:
        content = config.PROFILE_FILE.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"exists": False, "data": {}}

    data = _parse_md_to_dict(content)
    return {"exists": True, "data": data}


@router.get("/quiz-status")
async def get_quiz_status():
    """Retorna se o quiz foi completado."""
    try:
        content = config.QUIZ_FILE.read_text(encoding="utf-8")
        data = _parse_md_to_dict(content)
        return {
            "exists": True,
            "completed": data.get("Concluído", "false").lower() == "true",
        }
    except FileNotFoundError:
        return {"exists": False, "completed": False}
