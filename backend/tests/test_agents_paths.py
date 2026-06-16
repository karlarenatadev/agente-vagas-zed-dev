"""Garante que os agentes respeitam o isolamento por sessão.

Os agentes recebem um SessionPaths e devem ler/gravar na pasta da sessão, não
mais num 'data/' global. A fixture autouse do conftest injeta a chave fake do
cliente OpenAI, então instanciar os agentes não dispara rede.
"""

from agents.coach import CoachAgent
from agents.curator import CuratorAgent
from agents.maestro import MaestroAgent
from agents.scout import ScoutAgent
from session import SessionPaths


def test_maestro_usa_paths_da_sessao():
    maestro = MaestroAgent(SessionPaths("alice"))
    assert "alice" in str(maestro.paths.PROFILE_FILE)
    assert maestro.paths.session_id == "alice"


def test_agente_sem_paths_cai_na_sessao_default():
    coach = CoachAgent()
    assert coach.paths.session_id == "_default"


def test_agentes_de_sessoes_diferentes_nao_colidem():
    a = ScoutAgent(SessionPaths("alice"))
    b = CuratorAgent(SessionPaths("bob"))
    assert a.paths.dir != b.paths.dir


def test_curator_read_data_file_usa_pasta_da_sessao(tmp_path):
    paths = SessionPaths("alice", base_dir=tmp_path)
    paths.dir.mkdir(parents=True)
    (paths.dir / "user-profile.md").write_text("Área de interesse: Dados", encoding="utf-8")

    curator = CuratorAgent(paths)
    # Lê da pasta da sessão, não de um data/ global.
    assert "Dados" in curator._read_data_file("user-profile.md")
