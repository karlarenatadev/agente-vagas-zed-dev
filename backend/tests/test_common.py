"""Testes do helper `read_required` (routers/common.py).

Aqui o ponto é testar comportamento de ERRO: a função tem que levantar
HTTPException 400 quando o arquivo não existe ou está vazio. Usamos
`tmp_path` (pasta temporária que o pytest cria e apaga sozinho) pra não
tocar em nada do projeto real.
"""

import pytest
from fastapi import HTTPException

from routers.common import read_required


def test_read_required_le_arquivo_existente(tmp_path):
    arquivo = tmp_path / "ok.md"
    arquivo.write_text("  conteúdo real  ", encoding="utf-8")

    # Lê e já devolve sem espaços nas pontas.
    assert read_required(arquivo, "faltou", "inválido") == "conteúdo real"


def test_read_required_levanta_400_quando_nao_existe(tmp_path):
    arquivo = tmp_path / "nao-existe.md"

    # pytest.raises afirma "este bloco TEM que estourar esta exceção".
    # Se não estourar, o teste falha.
    with pytest.raises(HTTPException) as exc:
        read_required(arquivo, "faltou o arquivo", "inválido")

    assert exc.value.status_code == 400
    assert exc.value.detail == "faltou o arquivo"


def test_read_required_levanta_400_quando_vazio(tmp_path):
    arquivo = tmp_path / "vazio.md"
    arquivo.write_text("   \n  ", encoding="utf-8")  # só espaços = vazio

    with pytest.raises(HTTPException) as exc:
        read_required(arquivo, "faltou", "arquivo inválido")

    assert exc.value.status_code == 400
    assert exc.value.detail == "arquivo inválido"
