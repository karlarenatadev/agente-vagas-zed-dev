"""Testes do foco da candidatura.

Cobrem: persistência do foco no perfil (`upsert_focus_line` + `PUT
/api/reconciliation/focus`), a resolução por precedência (`resolve_focus`) e a
leitura do foco pelos agentes match/tailor/PDI (varia o `next_steps`).

Todos os artefatos vão para `tmp_path`; nenhum teste toca o `data/` real nem
depende de OpenAI/Firecrawl (os agentes de match/tailor/PDI são heurísticos).
"""

import pytest
from fastapi.testclient import TestClient

import config
from main import app
from agents.reconciliation import parse_focus, upsert_focus_line
from agents.resume_matcher import ResumeMatcher
from agents.resume_tailor import ResumeTailor, tailoring_to_markdown
from agents.pdi_generator import PdiGenerator
from routers.common import resolve_focus


PROFILE_COMPLETO = (
    "Área de interesse: Dados\n"
    "Nível de experiência: Júnior\n"
    "Habilidades atuais: Python, SQL\n"
    "Soft skills: Comunicação\n"
)


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    return TestClient(app)


def _default_dir(tmp_path):
    """Diretório resolvido pela sessão default (sem header X-Session-Id)."""
    d = tmp_path / "sessions" / "_default"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── upsert_focus_line (puro) ──────────────────────────────────────────────────

def test_upsert_focus_line_adiciona_quando_ausente():
    out = upsert_focus_line(PROFILE_COMPLETO, "vaga")
    assert parse_focus(out) == "vaga"
    # Preserva as linhas originais do perfil.
    assert "Habilidades atuais: Python, SQL" in out


def test_upsert_focus_line_substitui_sem_duplicar():
    base = PROFILE_COMPLETO + "Foco da candidatura: vaga\n"
    out = upsert_focus_line(base, "currículo")  # com acento → normaliza
    assert parse_focus(out) == "curriculo"
    assert out.count("Foco da candidatura:") == 1


def test_upsert_focus_line_rejeita_invalido():
    with pytest.raises(ValueError):
        upsert_focus_line(PROFILE_COMPLETO, "qualquer")


# ── resolve_focus (precedência explícito > perfil > "vaga") ───────────────────

def test_resolve_focus_explicito_vence_perfil():
    perfil = PROFILE_COMPLETO + "Foco da candidatura: vaga\n"
    assert resolve_focus(perfil, "perfil") == "perfil"


def test_resolve_focus_cai_no_perfil_sem_explicito():
    perfil = PROFILE_COMPLETO + "Foco da candidatura: curriculo\n"
    assert resolve_focus(perfil, None) == "curriculo"


def test_resolve_focus_default_vaga():
    assert resolve_focus(None, None) == "vaga"
    # Explícito inválido é ignorado; perfil sem linha de foco → default.
    assert resolve_focus(PROFILE_COMPLETO, "invalido") == "vaga"


# ── PUT /api/reconciliation/focus ─────────────────────────────────────────────

def test_put_focus_persiste_no_perfil(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    profile_path = _default_dir(tmp_path) / "user-profile.md"
    profile_path.write_text(PROFILE_COMPLETO, encoding="utf-8")

    resp = client.put("/api/reconciliation/focus", json={"focus": "currículo"})

    assert resp.status_code == 200
    assert resp.json()["focus"] == "curriculo"
    saved = profile_path.read_text(encoding="utf-8")
    assert parse_focus(saved) == "curriculo"


def test_put_focus_invalido_retorna_422(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)
    (_default_dir(tmp_path) / "user-profile.md").write_text(PROFILE_COMPLETO, encoding="utf-8")

    resp = client.put("/api/reconciliation/focus", json={"focus": "banana"})

    assert resp.status_code == 422


def test_put_focus_sem_perfil_retorna_400(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    resp = client.put("/api/reconciliation/focus", json={"focus": "vaga"})

    assert resp.status_code == 400


# ── Agentes leem o foco e variam o next_steps ─────────────────────────────────

def test_match_varia_next_step_por_foco(job_markdown, resume_markdown):
    matcher = ResumeMatcher()
    vaga = matcher.match(job_markdown, resume_markdown, focus="vaga")["next_steps"][0]
    curr = matcher.match(job_markdown, resume_markdown, focus="curriculo")["next_steps"][0]
    perfil = matcher.match(job_markdown, resume_markdown, focus="perfil")["next_steps"][0]

    assert len({vaga, curr, perfil}) == 3
    assert "vaga" in vaga.casefold()
    assert "currículo" in curr.casefold() or "curriculo" in curr.casefold()
    assert "perfil" in perfil.casefold()


def test_tailor_varia_next_step_por_foco(job_markdown, resume_markdown, match_markdown):
    tailor = ResumeTailor()
    vaga = tailor.generate(resume_markdown, job_markdown, match_markdown, focus="vaga")["next_steps"][0]
    curr = tailor.generate(resume_markdown, job_markdown, match_markdown, focus="curriculo")["next_steps"][0]

    assert vaga != curr
    assert "vaga" in vaga.casefold()


def test_pdi_varia_next_step_por_foco(job_markdown, resume_markdown, match_markdown):
    tailoring_md = tailoring_to_markdown(
        ResumeTailor().generate(resume_markdown, job_markdown, match_markdown)
    )
    gen = PdiGenerator()
    vaga = gen.generate(resume_markdown, job_markdown, match_markdown, tailoring_md, focus="vaga")["next_steps"][0]
    perfil = gen.generate(resume_markdown, job_markdown, match_markdown, tailoring_md, focus="perfil")["next_steps"][0]

    assert vaga != perfil
    assert "perfil" in perfil.casefold()


def test_match_route_aceita_foco_no_corpo(tmp_path, monkeypatch, job_markdown, resume_markdown):
    client = _client(tmp_path, monkeypatch)
    base = _default_dir(tmp_path)
    (base / "job-description-analysis.md").write_text(job_markdown, encoding="utf-8")
    (base / "resume-analysis.md").write_text(resume_markdown, encoding="utf-8")

    resp = client.post("/api/resume-match/analyze", json={"focus": "curriculo"})

    assert resp.status_code == 200
    first_step = resp.json()["next_steps"][0]
    assert "currículo" in first_step.casefold() or "curriculo" in first_step.casefold()
