"""Testes do replay_current_prompt do Maestro (recuperação visual de sessão).

O replay re-emite o prompt atual da sessão restaurada (quiz/menu/coach/await)
para repintar a tela no primeiro load. Deve ser SEM efeito colateral: não emite
tokens __STATE__, não grava arquivos e não avança passos.
"""

import asyncio

from agents.maestro import MaestroAgent
from session import SessionPaths


def _collect(gen) -> str:
    return "".join(asyncio.run(_adrain(gen)))


async def _adrain(gen):
    return [token async for token in gen]


def test_replay_quiz_reemite_pergunta_atual_sem_state(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)

    out = _collect(agent.replay_current_prompt({"mode": "quiz", "quiz_step": 3}))

    assert "Pergunta 4/7" in out
    assert "__STATE__" not in out
    # Sem efeito colateral: não grava o quiz nem cria o perfil.
    assert not paths.QUIZ_FILE.exists()
    assert not paths.PROFILE_FILE.exists()


def test_replay_quiz_step_fora_do_range_nao_estoura(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)

    out = _collect(agent.replay_current_prompt({"mode": "quiz", "quiz_step": 99}))

    # Clampa para a última pergunta (7/7) em vez de estourar índice.
    assert "Pergunta 7/7" in out
    assert "__STATE__" not in out


def test_replay_menu_mostra_o_menu(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)

    out = _collect(agent.replay_current_prompt({"mode": "menu"}))

    assert "ESTEIRA" in out
    assert "[A]" in out
    assert "__STATE__" not in out


def test_replay_coach_reemite_pergunta_atual(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    paths.INTERVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    paths.INTERVIEW_FILE.write_text(
        "P1: Fale sobre voce.\n"
        "R1: Sou dev.\n"
        "P2: Qual seu maior desafio tecnico recente?\n",
        encoding="utf-8",
    )
    agent = MaestroAgent(paths)

    out = _collect(
        agent.replay_current_prompt(
            {"mode": "coach", "coach_step": 2, "interview_context": "Vaga X"}
        )
    )

    assert "Qual seu maior desafio tecnico recente?" in out
    assert "entrevista" in out.lower()
    assert "__STATE__" not in out
    # Não altera a sessão de entrevista.
    assert "P2: Qual seu maior desafio tecnico recente?" in paths.INTERVIEW_FILE.read_text(
        encoding="utf-8"
    )


def test_replay_coach_sem_historico_ainda_orienta(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)

    out = _collect(agent.replay_current_prompt({"mode": "coach", "coach_step": 1}))

    assert "entrevista" in out.lower()
    assert "sair" in out.lower()
    assert "__STATE__" not in out


def test_replay_await_job_description(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)

    out = _collect(agent.replay_current_prompt({"mode": "await_job_description"}))

    assert "descri" in out.lower()  # descrição
    assert "menu" in out.lower()
    assert "__STATE__" not in out


def test_replay_modo_desconhecido_cai_no_menu(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    agent = MaestroAgent(paths)

    out = _collect(agent.replay_current_prompt({"mode": "scout"}))

    assert "ESTEIRA" in out
    assert "__STATE__" not in out
