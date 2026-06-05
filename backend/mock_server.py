"""
Servidor mock para testar o frontend sem API keys.
Simula o Maestro com respostas pré-definidas via WebSocket.

Uso: python mock_server.py
"""

import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Recoloca IA — Mock Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Respostas mock ────────────────────────────────────────────────────────────

WELCOME = """Bem-vindo ao **import vagas** — sua plataforma de desenvolvimento de carreira com IA.

✓ Perfil carregado — **Ciência de Dados** · **Júnior** · Remoto

O que você quer fazer hoje?

**[A]** Buscar vagas compatíveis com seu perfil
**[B]** Encontrar cursos para preencher lacunas de habilidades
**[C]** Praticar com uma entrevista simulada
**[D]** Refazer o quiz de perfil"""

MENU = """O que você quer fazer agora?

**[A]** Buscar vagas compatíveis com seu perfil
**[B]** Encontrar cursos para preencher lacunas de habilidades
**[C]** Praticar com uma entrevista simulada
**[D]** Refazer o quiz de perfil"""

SCOUT_RESPONSE = """
🔍 Buscando vagas de **Ciência de Dados** em **Salvador - Bahia**...

✓ 5 vagas encontradas. Analisando detalhes...

  [1/5] Analisando: Cientista de Dados Júnior — Nubank...
  [2/5] Analisando: Analista de Dados — iFood...
  [3/5] Analisando: Analista BI Júnior — Ambev...
  [4/5] Analisando: Data Analyst — Mercado Livre...
  [5/5] Analisando: Cientista de Dados — Itaú...

## RESPOSTA: SCOUT
### estado
sucesso

### resumo
Encontrei 5 vagas para **Ciência de Dados** em **Salvador - Bahia**. Aqui estão os resultados com análise de correspondência de habilidades.

### dados

1. titulo: Cientista de Dados Júnior
   empresa: Nubank
   localizacao: Remoto
   salario: R$ 4.000 - R$ 6.000
   beneficios: VR, VT, Plano de Saúde, Stock Options
   link: https://nubank.com.br/vagas/123
   habilidades_correspondentes: Python, SQL, Git
   soft_skills_correspondentes: comunicação, trabalho em equipe
   habilidades_faltantes: Spark, Airflow, dbt
   contagem_correspondencia: 3 de 6 habilidades correspondem
   dica_curriculo: Destaque seus projetos com Python e SQL — são os requisitos principais desta vaga

2. titulo: Analista de Dados
   empresa: iFood
   localizacao: Remoto
   salario: R$ 3.500 - R$ 5.500
   beneficios: VR, Plano de Saúde, Gympass
   link: https://ifood.com.br/vagas/456
   habilidades_correspondentes: Python, SQL, Excel, Power BI
   soft_skills_correspondentes: proatividade, resolução de problemas
   habilidades_faltantes: Tableau, Looker
   contagem_correspondencia: 4 de 6 habilidades correspondem
   dica_curriculo: Mencione experiência com dashboards no Power BI — diferencial importante aqui

3. titulo: Analista BI Júnior
   empresa: Ambev
   localizacao: São Paulo - SP (Híbrido)
   salario: R$ 3.000 - R$ 4.500
   beneficios: VR, VT, Plano de Saúde, PLR
   link: https://ambev.com.br/vagas/789
   habilidades_correspondentes: SQL, Excel, Power BI
   soft_skills_correspondentes: comunicação, pensamento crítico
   habilidades_faltantes: SAP, Power Query
   contagem_correspondencia: 3 de 5 habilidades correspondem
   dica_curriculo: Destaque análises com SQL e Power BI — core desta posição

"""

CURATOR_RESPONSE = """📚 **CURATOR** — Buscando trilha de aprendizado...

  🔍 Buscando cursos para: **Spark**
  🔍 Buscando cursos para: **Airflow**
  🔍 Buscando cursos para: **dbt**

## RESPOSTA: CURATOR
### estado
sucesso

### resumo
Montei uma trilha de aprendizado acessivel para **3 habilidades** identificadas nas vagas, priorizando materiais gratuitos, videos, documentacao e cursos pagos quando fizer sentido.

### dados

**Habilidade Faltante: Spark**

ACESSIVEL:
nome_curso: Apache Spark com Python e PySpark
plataforma: Alura
duracao: 16 horas
nivel: intermediario
link: https://alura.com.br/curso-online-spark-python

GRATUITO:
nome_curso: Apache Spark Tutorial for Beginners
plataforma: YouTube
duracao: 3 horas
nivel: iniciante
link: https://youtube.com/watch?v=spark-tutorial

---

**Habilidade Faltante: Airflow**

ACESSIVEL:
nome_curso: Apache Airflow: Orquestração de Pipelines de Dados
plataforma: Udemy
duracao: 12 horas
nivel: intermediario
link: https://udemy.com/course/airflow-pipelines

GRATUITO:
nome_curso: Airflow Documentation — Quick Start
plataforma: Documentação Oficial
duracao: 2 horas
nivel: iniciante
link: https://airflow.apache.org/docs/

---

**Habilidade Faltante: dbt**

ACESSIVEL:
nome_curso: dbt (data build tool) — Do Zero ao Avançado
plataforma: Udemy
duracao: 10 horas
nivel: iniciante
link: https://udemy.com/course/dbt-data-build-tool

GRATUITO:
nome_curso: dbt Learn — Curso Oficial Gratuito
plataforma: Documentação Oficial
duracao: 4 horas
nivel: iniciante
link: https://courses.getdbt.com

---

"""

COACH_Q1 = """🎯 **COACH** — Entrevista simulada para: **Cientista de Dados Júnior — Nubank**

**Pergunta 1/5:**

Me conte sobre um projeto de dados que você desenvolveu do início ao fim. Qual foi o problema que você resolveu, quais ferramentas utilizou e qual foi o impacto do resultado?
"""

COACH_Q2 = """**Feedback da Pergunta 1:**
Boa resposta! Você demonstrou clareza ao descrever o problema e as ferramentas utilizadas. Para próximas entrevistas, tente quantificar o impacto — por exemplo, "reduzi o tempo de análise em 40%" é mais convincente do que "melhorei o processo".

**Pergunta 2/5:**

Como você lida com dados faltantes ou inconsistentes em um dataset? Me dê um exemplo prático de como você abordaria esse problema com Python.
"""

COACH_Q3 = """**Feedback da Pergunta 2:**
Excelente! Você mencionou técnicas sólidas como imputação e remoção de outliers. Poderia ter citado bibliotecas específicas como `pandas` ou `scikit-learn` para mostrar profundidade técnica.

**Pergunta 3/5:**

Imagine que você precisa apresentar uma análise complexa para um time de negócios sem background técnico. Como você estruturaria essa apresentação?
"""

COACH_FINAL = """**Feedback da Pergunta 5:**
Ótima resposta! Você demonstrou maturidade ao pensar na audiência e adaptar a comunicação.

---

**🏆 RESULTADO FINAL DA ENTREVISTA**

Pontuação: 7/10

**Pontos Fortes:**
1. Boa capacidade de comunicação e clareza nas respostas
2. Conhecimento técnico sólido em Python e SQL
3. Pensamento analítico bem estruturado

**Áreas de Melhoria:**
1. Quantifique mais os resultados — use números e métricas sempre que possível
2. Aprofunde o conhecimento em ferramentas de pipeline (Airflow, dbt)
3. Pratique a metodologia STAR para respostas comportamentais

**Dica Principal:**
Prepare 3-4 histórias de projetos usando a estrutura STAR (Situação, Tarefa, Ação, Resultado) — elas cobrem a maioria das perguntas comportamentais.
"""

QUIZ_Q1 = """Vamos criar seu perfil profissional!

**Pergunta 1/7:** Qual área mais te anima? Opções: Frontend, Backend, Ciência de Dados, Mobile, DevOps, Full Stack, Governança de Dados, Design UX, Design UI, Liderança, RH, Marketing de Mídias Sociais, Growth Marketing, Gestão de Produtos ou Cibersegurança
"""

QUIZ_DONE = """✓ Perfil criado com sucesso — **Ciência de Dados** · **Júnior**

"""

INVALID = """⚠ Opção inválida. Por favor, escolha uma das opções do menu: **A**, **B**, **C** ou **D**.

"""


# ── Helpers de streaming ──────────────────────────────────────────────────────

async def stream_text(ws: WebSocket, text: str, delay: float = 0.015):
    """Envia texto token a token simulando streaming."""
    # Divide em chunks de ~3 chars para parecer natural
    chunk_size = 3
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        await ws.send_json({"type": "token", "content": chunk})
        await asyncio.sleep(delay)


async def send_state(ws: WebSocket, state: dict):
    await ws.send_json({"type": "state", "content": state})


async def done(ws: WebSocket):
    await ws.send_json({"type": "done", "content": ""})


# ── WebSocket handler ─────────────────────────────────────────────────────────

@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    await ws.accept()

    session = {
        "mode": "menu",
        "quiz_step": 0,
        "quiz_answers": {},
        "coach_step": 0,
        "interview_context": "Cientista de Dados Júnior — Nubank",
    }

    # Boas-vindas automáticas — duas mensagens separadas
    await stream_text(ws, WELCOME, delay=0.008)
    await done(ws)
    await asyncio.sleep(0.05)
    await stream_text(ws, MENU)
    await send_state(ws, session)
    await done(ws)

    while True:
        try:
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg = data.get("content", "").strip().upper()

            if msg == "A":
                session["mode"] = "agent_running"
                await send_state(ws, {**session, "active_agent": "Scout"})
                await stream_text(ws, SCOUT_RESPONSE, delay=0.005)
                await done(ws)
                await asyncio.sleep(0.05)
                session["mode"] = "menu"
                await stream_text(ws, MENU)
                await send_state(ws, session)

            elif msg == "B":
                session["mode"] = "agent_running"
                await send_state(ws, {**session, "active_agent": "Curator"})
                await stream_text(ws, CURATOR_RESPONSE, delay=0.005)
                await done(ws)
                await asyncio.sleep(0.05)
                session["mode"] = "menu"
                await stream_text(ws, MENU)
                await send_state(ws, session)

            elif msg == "C":
                session["mode"] = "coach"
                session["coach_step"] = 1
                await send_state(ws, session)
                await stream_text(ws, COACH_Q1, delay=0.012)

            elif msg == "D":
                session["mode"] = "quiz"
                session["quiz_step"] = 0
                await send_state(ws, session)
                await stream_text(ws, "\n↺ **Reset completo.**\n\n")
                await done(ws)
                await asyncio.sleep(0.05)
                await stream_text(ws, QUIZ_Q1)

            elif session["mode"] == "coach":
                step = session["coach_step"]
                if step == 1:
                    session["coach_step"] = 2
                    await send_state(ws, session)
                    await stream_text(ws, COACH_Q2, delay=0.012)
                elif step == 2:
                    session["coach_step"] = 3
                    await send_state(ws, session)
                    await stream_text(ws, COACH_Q3, delay=0.012)
                elif step in (3, 4):
                    session["coach_step"] = step + 1
                    await send_state(ws, session)
                    q_num = step + 1
                    await stream_text(ws, f"**Feedback da Pergunta {step}:**\nBoa resposta! Continue desenvolvendo essa linha de raciocínio.\n\n**Pergunta {q_num}/5:**\n\nDescreva como você priorizaria tarefas em um projeto com múltiplas demandas simultâneas e prazos apertados.\n", delay=0.012)
                else:
                    session["mode"] = "menu"
                    session["coach_step"] = 0
                    await send_state(ws, session)
                    await stream_text(ws, COACH_FINAL, delay=0.010)
                    await done(ws)
                    await asyncio.sleep(0.05)
                    await stream_text(ws, MENU)

            elif session["mode"] == "quiz":
                step = session["quiz_step"]
                if step < 6:
                    session["quiz_step"] = step + 1
                    await send_state(ws, session)
                    questions = [
                        "**Pergunta 2/7:** Como você descreveria seu nível de experiência atual? Escolha um: Júnior, Pleno ou Sênior",
                        "**Pergunta 3/7:** Como você prefere trabalhar? Opções: Remoto, Híbrido ou Presencial",
                        "**Pergunta 4/7:** Onde você está localizado? Me diga sua cidade e estado, ou apenas diga 'Remoto'",
                        "**Pergunta 5/7:** Quais são suas soft skills mais fortes?",
                        "**Pergunta 6/7:** Onde você se vê em sua carreira? Opções: Crescimento técnico, Transição de carreira, Primeiro emprego ou Trilha de liderança",
                        "**Pergunta 7/7:** Quais habilidades técnicas você já tem? Liste separadas por vírgulas",
                    ]
                    await stream_text(ws, f"\n{questions[step]}\n")
                else:
                    session["mode"] = "menu"
                    session["quiz_step"] = 0
                    await send_state(ws, session)
                    await stream_text(ws, QUIZ_DONE)
                    await done(ws)
                    await asyncio.sleep(0.05)
                    await stream_text(ws, MENU)

            else:
                await stream_text(ws, INVALID)
                await done(ws)
                await asyncio.sleep(0.05)
                await stream_text(ws, MENU)

            await done(ws)

        except WebSocketDisconnect:
            break
        except Exception as e:
            await ws.send_json({"type": "error", "content": str(e)})
            await done(ws)


@app.get("/health")
async def health():
    return {"status": "mock", "agent": "Maestro"}


@app.get("/api/profile/")
async def get_profile():
    return {
        "exists": True,
        "data": {
            "Área de interesse": "Ciência de Dados",
            "Nível de experiência": "Júnior",
            "Preferências de trabalho": "Remoto",
            "Localização": "Salvador - Bahia",
            "Soft skills": "comunicação, trabalho em equipe, proatividade",
            "Objetivo de carreira": "Crescimento técnico",
            "Habilidades atuais": "Python, SQL, Excel, Figma, Git, Power BI",
            "Funções alvo": "Analista de Dados, Cientista de Dados Júnior, Analista BI",
            "Concluído": "true",
        },
    }


@app.get("/api/profile/quiz-status")
async def quiz_status():
    return {"exists": True, "completed": True}


@app.post("/api/resume/upload")
async def upload_resume_mock(file: UploadFile = File(...)):
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in {".txt", ".pdf", ".docx"}:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Formato inválido. Envie um arquivo PDF, DOCX ou TXT."},
        )

    content = await file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "Arquivo grande demais. O limite é de 5 MB."},
        )
    if not content:
        return JSONResponse(
            status_code=400,
            content={"success": False, "message": "O arquivo está vazio. Envie um currículo com texto legível."},
        )

    analysis = {
        "detected_name": "não identificado",
        "professional_summary": "Perfil com indícios de atuação em Ciência de Dados, nível Júnior, com habilidades em Python, SQL, Power BI e Git.",
        "probable_areas": ["Ciência de Dados"],
        "estimated_level": "Júnior",
        "technical_skills": ["Python", "SQL", "Power BI", "Git"],
        "soft_skills": ["comunicação", "trabalho em equipe", "proatividade"],
        "experience_summary": "Projetos acadêmicos e pessoais com análise de dados, dashboards e automação de relatórios.",
        "education_summary": "Formação ou cursos na área de dados precisam ser confirmados no quiz.",
        "suggested_target_roles": ["Analista de Dados Júnior", "Estagiária em Dados", "Assistente de BI"],
        "strengths": ["Habilidades técnicas alinhadas a vagas iniciais de dados.", "Boa base para dashboards e análise exploratória."],
        "improvement_points": ["Confirmar nível, localização e objetivo de carreira no quiz.", "Detalhar experiências com resultados mensuráveis."],
        "fields_to_confirm": ["Localização", "Preferência de trabalho", "Objetivo de carreira"],
    }

    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "resume-analysis.md").write_text(
        """Nome detectado: não identificado

Resumo profissional:
Perfil com indícios de atuação em Ciência de Dados, nível Júnior, com habilidades em Python, SQL, Power BI e Git.

Áreas prováveis:
- Ciência de Dados

Nível estimado:
Júnior

Habilidades técnicas detectadas:
- Python
- SQL
- Power BI
- Git

Soft skills detectadas:
- comunicação
- trabalho em equipe
- proatividade

Experiências detectadas:
Projetos acadêmicos e pessoais com análise de dados, dashboards e automação de relatórios.

Formação detectada:
Formação ou cursos na área de dados precisam ser confirmados no quiz.

Funções alvo sugeridas:
- Analista de Dados Júnior
- Estagiária em Dados
- Assistente de BI

Pontos fortes:
- Habilidades técnicas alinhadas a vagas iniciais de dados.
- Boa base para dashboards e análise exploratória.

Pontos de melhoria:
- Confirmar nível, localização e objetivo de carreira no quiz.
- Detalhar experiências com resultados mensuráveis.

Campos que precisam de confirmação no quiz:
- Localização
- Preferência de trabalho
- Objetivo de carreira

Concluído: true
""",
        encoding="utf-8",
    )

    return {
        "success": True,
        "message": "Currículo analisado com sucesso.",
        "analysis": analysis,
        "profile_updated": False,
    }


# ── Candidaturas (mock em memória) ────────────────────────────────────────────

import uuid as _uuid

_applications: list[dict] = []


@app.get("/api/applications/stats")
async def app_stats():
    stats: dict[str, int] = {}
    for a in _applications:
        s = a.get("status", "salva")
        stats[s] = stats.get(s, 0) + 1
    return {"total": len(_applications), "by_status": stats}


@app.get("/api/applications/")
async def list_apps():
    return sorted(_applications, key=lambda x: x.get("data_salva", ""), reverse=True)


@app.post("/api/applications/")
async def create_app(body: dict):
    from datetime import datetime
    new = {"id": str(_uuid.uuid4()), "data_salva": datetime.now().isoformat(), **body}
    _applications.append(new)
    return new


@app.patch("/api/applications/{app_id}")
async def update_app(app_id: str, body: dict):
    from datetime import datetime
    for a in _applications:
        if a["id"] == app_id:
            if "status" in body:
                a["status"] = body["status"]
                if body["status"] == "aplicada" and not a.get("data_aplicacao"):
                    a["data_aplicacao"] = datetime.now().isoformat()
            if "notas" in body:
                a["notas"] = body["notas"]
            return a
    return {"error": "not found"}


@app.delete("/api/applications/{app_id}")
async def delete_app(app_id: str):
    global _applications
    _applications = [a for a in _applications if a["id"] != app_id]
    return {"ok": True}


if __name__ == "__main__":
    print("🚀 Mock server rodando em http://localhost:8000")
    print("   WebSocket: ws://localhost:8000/ws/chat")
    print("   Pressione Ctrl+C para parar\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
