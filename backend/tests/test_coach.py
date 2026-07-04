"""Testes da lógica de construção de brief e perguntas de fallback do Coach.

Como no Scout/Curator, o `run()` depende do LLM e fica de fora destes testes.
Aqui protegemos a parte pura: o brief que resume perfil + vaga analisada + match,
e as perguntas de fallback geradas a partir desse brief.
"""

import pytest

from agents.base import LLMProviderError
from agents.coach import CoachAgent
from agents.job_description_analyzer import analysis_from_markdown
from agents.resume_matcher import match_report_from_markdown
from artifacts import mark_dependents_stale, register_artifact
from session import SessionPaths


PROFILE = (
    "Area de interesse: dados\n"
    "Localizacao: remoto\n"
    "Nivel de experiencia: junior\n"
    "Funcoes alvo: Analista de Dados\n"
    "Habilidades atuais: Python, SQL\n"
    "Soft skills: Comunicacao\n"
    "Objetivo de carreira: Atuar com analytics\n"
    "Concluido: true\n"
)

# Vaga com responsabilidades em bullets, para exercitar o passo 4 (cenário).
JOB_DESC_COM_RESPONSABILIDADES = """\
Analista de Dados Pleno

Responsabilidades:
- Construir dashboards no Power BI
- Analisar KPIs de produto
- Criar pipelines de ETL

Requisitos obrigatórios:
- Experiência com Python e SQL
- Conhecimento de Excel
- Modelagem de dados

Ferramentas: Power BI, Excel, Git.
"""


@pytest.fixture
def coach():
    return CoachAgent(SessionPaths())


def _brief(coach, **overrides):
    base = dict(
        profile_text=PROFILE,
        job_results="",
        course_recommendations="",
        interview_context="Analista de Dados — Acme",
    )
    base.update(overrides)
    return coach._build_interview_brief(**base)


def test_brief_inclui_campos_da_vaga_analisada(coach, job_markdown):
    brief = _brief(coach, job_analysis=job_markdown)

    assert "Vaga analisada (titulo):" in brief
    assert "Vaga analisada (empresa):" in brief
    assert "Requisitos obrigatorios da vaga:" in brief
    assert "Hard skills da vaga:" in brief

    # O título da fixture do conftest vem da descrição "Analista de Dados Júnior na Acme".
    analysis = analysis_from_markdown(job_markdown)
    assert analysis["title"] in brief


def test_brief_inclui_campos_do_match(coach, match_markdown):
    brief = _brief(coach, match_report=match_markdown)

    assert "Score de aderencia:" in brief
    assert "Nivel de prontidao:" in brief
    assert "Lacunas criticas do match:" in brief

    report = match_report_from_markdown(match_markdown)
    assert f"{report['overall_score']}/100" in brief


def test_brief_cai_no_scout_perfil_quando_artefatos_vazios(coach):
    brief = _brief(coach)

    # Linhas antigas permanecem mesmo sem vaga/match.
    assert "Contexto da entrevista:" in brief
    assert "Area de interesse: dados" in brief
    assert "Status da preparacao:" in brief
    # E nenhum enriquecimento de vaga/match é adicionado.
    assert "Vaga analisada (titulo):" not in brief
    assert "Score de aderencia:" not in brief


def test_pergunta_passo2_usa_requisitos_e_hard_skills_da_vaga(coach, job_markdown):
    brief = _brief(coach, job_analysis=job_markdown)

    question = coach._question_for_step(2, brief)
    assert "requisitos obrigatorios da vaga" in question.casefold()
    assert "hard skills" in question.casefold()


def test_pergunta_passo4_usa_responsabilidades_e_lacunas(coach, match_markdown):
    # Vaga com responsabilidades em bullets para o passo 4 ter o que citar.
    job_markdown = analysis_to_markdown_safe(JOB_DESC_COM_RESPONSABILIDADES)
    brief = _brief(coach, job_analysis=job_markdown, match_report=match_markdown)

    question = coach._question_for_step(4, brief)
    assert "responsabilidades da vaga" in question.casefold()


def test_pergunta_passo2_cai_no_scout_quando_vaga_vazia(coach):
    brief = _brief(coach)

    question = coach._question_for_step(2, brief)
    # Sem vaga analisada, mantém o texto de fallback com habilidades atuais.
    assert "habilidades atuais" in question.casefold()


def test_parsers_toleram_entrada_vazia(coach):
    assert analysis_from_markdown("") is None
    assert match_report_from_markdown("") is None
    assert coach._parse_job_analysis("") == {}
    assert coach._parse_match_report("") == {}


def analysis_to_markdown_safe(description: str) -> str:
    from agents.job_description_analyzer import (
        JobDescriptionAnalyzer,
        analysis_to_markdown,
    )

    return analysis_to_markdown(JobDescriptionAnalyzer().analyze(description))


@pytest.mark.asyncio
async def test_run_nao_bloqueia_com_vaga_analisada_sem_scout(coach, monkeypatch, job_markdown):
    """Vaga analisada destrava a entrevista mesmo sem Scout (gate relaxado).

    Mockamos o streaming do LLM para simular falha e cair no fallback local —
    assim o teste não depende de rede/chave e ainda assim percorre o `run()`
    além do gate, confirmando que ele não bloqueia sem Scout.
    """

    async def _boom(_system_prompt, _prompt):
        raise LLMProviderError("indisponivel", provider_error="test")
        yield  # pragma: no cover - torna a função em generator

    monkeypatch.setattr(coach, "stream_llm", _boom)

    chunks = []
    async for chunk in coach.run({
        "step": 1,
        "profile": PROFILE,
        "job_results": "",
        "course_recommendations": "",
        "job_analysis": job_markdown,
        "match_report": "",
        "interview_context": "Analista de Dados — Acme",
        "history": [],
    }):
        chunks.append(chunk)

    output = "".join(chunks)
    # O gate passou: o estado não é "erro" de bloqueio.
    assert "### estado" in output
    estado = output.split("### estado", 1)[1].split("###", 1)[0]
    assert "erro" not in estado
    # Mensagem de bloqueio antiga (que exigia Scout) não aparece.
    assert "Rode a busca do Scout" not in output


@pytest.mark.asyncio
async def test_run_bloqueia_match_stale_sem_chamar_llm(
    tmp_path,
    monkeypatch,
    job_markdown,
    match_markdown,
):
    paths = SessionPaths("coach-stale", base_dir=tmp_path)
    paths.dir.mkdir(parents=True)
    paths.RESUME_MATCH_REPORT_FILE.write_text(match_markdown, encoding="utf-8")
    register_artifact(
        paths.dir,
        "match",
        paths.RESUME_MATCH_REPORT_FILE,
        generator_version="match:v1",
    )
    mark_dependents_stale(paths.dir, "resume")
    agent = CoachAgent(paths)

    async def _unexpected_call(_system_prompt, _prompt):
        raise AssertionError("LLM nao deve ser chamado com match stale")
        yield

    monkeypatch.setattr(agent, "stream_llm", _unexpected_call)

    chunks = []
    async for chunk in agent.run(
        {
            "step": 1,
            "profile": PROFILE,
            "job_analysis": job_markdown,
            "match_report": match_markdown,
            "interview_context": "Analista de Dados",
        }
    ):
        chunks.append(chunk)

    output = "".join(chunks)
    assert "### estado\nerro" in output
    assert "match" in output.casefold()
    assert "obsoleto" in output.casefold()
    assert paths.RESUME_MATCH_REPORT_FILE.exists()


# --- Rodada P1: calibração do feedback pelo contexto real (score/lacunas/evidências) ---


def test_brief_inclui_evidencias_do_curriculo(coach, match_markdown):
    brief = _brief(coach, match_report=match_markdown)

    assert "Resumo do curriculo:" in brief
    assert "Evidencias parciais do curriculo:" in brief


def test_calibracao_com_match_cita_score_e_evidencias(coach, match_markdown):
    brief = _brief(coach, match_report=match_markdown)
    report = match_report_from_markdown(match_markdown)

    directive = coach._calibration_directive(brief)

    assert f"{report['overall_score']}/100" in directive
    assert "tecnico, comportamental ou de evidencia" in directive.casefold()
    # Resposta melhorada ancorada apenas em evidências reais do candidato.
    assert "evidencias reais" in directive.casefold()


def test_calibracao_sem_match_nao_finge(coach):
    brief = _brief(coach)

    directive = coach._calibration_directive(brief)

    assert "comparar vaga" in directive.casefold()
    # Sem match, não inventa score nem finge personalização por aderência.
    assert "/100" not in directive


@pytest.mark.asyncio
async def test_prompt_avaliacao_inclui_calibracao_com_match(coach, monkeypatch, match_markdown):
    brief = _brief(coach, match_report=match_markdown)
    captured = {}

    async def _capture(_system_prompt, prompt):
        captured["prompt"] = prompt
        yield "ok"

    monkeypatch.setattr(coach, "stream_llm", _capture)

    async for _ in coach._evaluate_and_ask(2, brief, "P1: x\nR1: y"):
        pass

    assert "Calibracao obrigatoria do feedback" in captured["prompt"]


@pytest.mark.asyncio
async def test_prompt_avaliacao_sem_match_nao_finge(coach, monkeypatch):
    brief = _brief(coach)
    captured = {}

    async def _capture(_system_prompt, prompt):
        captured["prompt"] = prompt
        yield "ok"

    monkeypatch.setattr(coach, "stream_llm", _capture)

    async for _ in coach._evaluate_and_ask(2, brief, "P1: x\nR1: y"):
        pass

    assert "nao finja" in captured["prompt"].casefold()


@pytest.mark.asyncio
async def test_prompt_final_inclui_plano_calibrado(coach, monkeypatch, match_markdown):
    brief = _brief(coach, match_report=match_markdown)
    captured = {}

    async def _capture(_system_prompt, prompt):
        captured["prompt"] = prompt
        yield "ok"

    monkeypatch.setattr(coach, "stream_llm", _capture)

    async for _ in coach._final_evaluation(brief, "R5: resposta"):
        pass

    assert "plano de preparacao deve priorizar as lacunas criticas" in captured["prompt"].casefold()


def test_fallback_final_usa_lacunas_quando_ha_match(coach, match_markdown):
    brief = _brief(coach, match_report=match_markdown)
    report = match_report_from_markdown(match_markdown)

    output = coach._fallback_final_evaluation(
        brief,
        "R1: a\nR2: b\nR3: c\nR4: d\nR5: e",
        LLMProviderError("x", provider_error="test"),
    )

    assert f"{report['overall_score']}/100" in output
    assert "plano_preparacao" in output


def test_fallback_final_sem_match_recomenda_rodar_match(coach):
    brief = _brief(coach)

    output = coach._fallback_final_evaluation(
        brief,
        "R1: a\nR2: b\nR3: c\nR4: d\nR5: e",
        LLMProviderError("x", provider_error="test"),
    )

    assert "comparar vaga" in output.casefold()
    assert "/100" not in output
