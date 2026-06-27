"""Testes da fundação de isolamento por sessão.

A parte mais sensível aqui é segurança: o ID vem do cliente e vira nome de
pasta, então NÃO pode permitir path traversal. Esses testes travam isso.
"""

from pathlib import Path

from session import DEFAULT_SESSION, SessionPaths, sanitize_session_id


def test_sanitize_preserva_id_valido():
    assert sanitize_session_id("abc-123_DEF") == "abc-123_DEF"


def test_sanitize_id_vazio_ou_none_vira_default():
    assert sanitize_session_id("") == DEFAULT_SESSION
    assert sanitize_session_id(None) == DEFAULT_SESSION


def test_sanitize_neutraliza_path_traversal():
    # Tentativas de escapar da pasta de dados têm que ser higienizadas.
    assert sanitize_session_id("..") == DEFAULT_SESSION
    assert sanitize_session_id("../../etc/passwd") == "etcpasswd"
    assert sanitize_session_id("a/b\\c") == "abc"


def test_sanitize_limita_tamanho():
    assert len(sanitize_session_id("x" * 500)) <= 64


def test_default_fica_isolada_em_sessions_default(tmp_path):
    paths = SessionPaths(None, base_dir=tmp_path)
    assert paths.dir == tmp_path / "sessions" / "_default"
    assert paths.PROFILE_FILE == tmp_path / "sessions" / "_default" / "user-profile.md"


def test_sessao_real_fica_isolada_em_subpasta(tmp_path):
    paths = SessionPaths("user42", base_dir=tmp_path)
    assert paths.dir == tmp_path / "sessions" / "user42"
    assert paths.RESUME_ANALYSIS_FILE == tmp_path / "sessions" / "user42" / "resume-analysis.md"


def test_sessoes_diferentes_nao_se_misturam(tmp_path):
    a = SessionPaths("alice", base_dir=tmp_path)
    b = SessionPaths("bob", base_dir=tmp_path)
    assert a.PROFILE_FILE != b.PROFILE_FILE
    assert a.dir.parent == b.dir.parent  # ambas sob sessions/


def test_id_malicioso_nao_escapa_da_base(tmp_path):
    # Mesmo com um ID hostil, o diretório resolvido fica DENTRO da base.
    paths = SessionPaths("../../../etc", base_dir=tmp_path)
    resolved = paths.dir.resolve()
    assert Path(tmp_path).resolve() in resolved.parents or resolved == Path(tmp_path).resolve()
