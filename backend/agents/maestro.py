"""
Agente Maestro — Orquestrador principal do sistema Recoloca IA.

Responsabilidades:
- Gerenciar o quiz de perfil do usuário
- Apresentar o menu de opções
- Despachar sub-agentes (Scout, Curator, Coach)
- Manter estado nos arquivos data/
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import AsyncGenerator

import config
from agents.base import BaseAgent
from agents.scout import ScoutAgent
from agents.curator import CuratorAgent
from agents.coach import CoachAgent


# Mapeamento fixo de funções alvo (área + nível → funções)
TARGET_ROLES_MAP: dict[str, list[str]] = {
    "frontend_júnior": ["Desenvolvedor Frontend", "Desenvolvedor UI Júnior", "Desenvolvedor Web"],
    "frontend_pleno": ["Engenheiro Frontend", "Desenvolvedor UI", "Desenvolvedor React"],
    "frontend_sênior": ["Engenheiro Frontend Sênior", "Líder de Desenvolvimento UI", "Arquiteto Frontend"],
    "backend_júnior": ["Desenvolvedor Backend", "Desenvolvedor API Júnior", "Desenvolvedor de Software"],
    "backend_pleno": ["Engenheiro Backend", "Desenvolvedor API", "Desenvolvedor Python/Java"],
    "backend_sênior": ["Engenheiro Backend Sênior", "Arquiteto de Sistemas", "Líder Técnico"],
    "ciência de dados_júnior": ["Analista de Dados", "Cientista de Dados Júnior", "Analista BI"],
    "ciência de dados_pleno": ["Cientista de Dados", "Engenheiro de Machine Learning", "Engenheiro de Dados"],
    "ciência de dados_sênior": ["Cientista de Dados Sênior", "Arquiteto ML", "Líder IA"],
    "mobile_júnior": ["Desenvolvedor Mobile", "Desenvolvedor iOS/Android Júnior", "Desenvolvedor de Apps"],
    "mobile_pleno": ["Desenvolvedor iOS", "Desenvolvedor Android", "Desenvolvedor React Native"],
    "mobile_sênior": ["Engenheiro Mobile Sênior", "Arquiteto Mobile", "Líder Flutter"],
    "devops_júnior": ["Engenheiro DevOps Júnior", "Suporte Cloud", "SysAdmin"],
    "devops_pleno": ["Engenheiro DevOps", "Engenheiro Cloud", "SRE"],
    "devops_sênior": ["Engenheiro DevOps Sênior", "Arquiteto Cloud", "Líder de Plataforma"],
    "full stack_júnior": ["Desenvolvedor Full Stack", "Desenvolvedor Web Júnior", "Desenvolvedor de Aplicações"],
    "full stack_pleno": ["Engenheiro Full Stack", "Desenvolvedor de Aplicações Web", "Desenvolvedor Full Stack Pleno"],
    "full stack_sênior": ["Engenheiro Full Stack Sênior", "Líder Técnico", "Arquiteto de Soluções"],
    "governança de dados_júnior": ["Analista de Governança de Dados Júnior", "Gestor de Dados Júnior", "Assistente de Compliance"],
    "governança de dados_pleno": ["Analista de Governança de Dados", "DPO", "Analista de Qualidade de Dados"],
    "governança de dados_sênior": ["Head de Governança de Dados", "Diretor Chefe de Dados", "Líder de Arquitetura de Dados"],
    "design ux_júnior": ["Designer UX Júnior", "Assistente UI/UX", "Pesquisador UX Jr"],
    "design ux_pleno": ["Designer UX", "Pesquisador UX", "Designer de Produto"],
    "design ux_sênior": ["Designer UX Sênior", "Líder UX", "Head de UX"],
    "design ui_júnior": ["Designer UI Júnior", "Designer Visual Jr", "Assistente de Design System"],
    "design ui_pleno": ["Designer UI", "Designer Visual", "Designer de Interação"],
    "design ui_sênior": ["Designer UI Sênior", "Líder UI", "Arquiteto de Design System"],
    "liderança_júnior": ["Líder de Equipe Júnior", "Coordenador de Projetos", "Scrum Master Jr"],
    "liderança_pleno": ["Gerente de Engenharia", "Gerente de Projetos", "Agile Coach"],
    "liderança_sênior": ["Diretor de Engenharia", "VP de Tecnologia", "CTO"],
    "rh_júnior": ["Analista de RH Júnior", "Assistente de Aquisição de Talentos", "Coordenador de RH"],
    "rh_pleno": ["Analista de RH", "Recrutador", "Especialista em Operações de Pessoas"],
    "rh_sênior": ["Gerente de RH", "Head de Pessoas", "Diretor de Talentos"],
    "marketing de mídias sociais_júnior": ["Assistente de Mídias Sociais", "Criador de Conteúdo Jr", "Community Manager Jr"],
    "marketing de mídias sociais_pleno": ["Gerente de Mídias Sociais", "Estrategista de Conteúdo", "Analista de Marketing Digital"],
    "marketing de mídias sociais_sênior": ["Head de Mídias Sociais", "Diretor de Mídias Sociais", "Líder Estrategista de Marca"],
    "growth marketing_júnior": ["Assistente de Growth Marketing", "Analista de Marketing Jr", "Marketing de Performance Jr"],
    "growth marketing_pleno": ["Growth Marketer", "Gerente de Marketing de Performance", "Especialista CRO"],
    "growth marketing_sênior": ["Head de Growth", "Diretor de Growth", "VP de Marketing"],
    "gestão de produtos_júnior": ["Analista de Produto", "Gerente de Produto Associado", "Product Owner Jr"],
    "gestão de produtos_pleno": ["Gerente de Produto", "Product Owner", "Gerente de Produto Técnico"],
    "gestão de produtos_sênior": ["Gerente de Produto Sênior", "Head de Produto", "VP de Produto"],
    "cibersegurança_júnior": ["Analista de Segurança Júnior", "Analista SOC", "Assistente de Segurança da Informação"],
    "cibersegurança_pleno": ["Engenheiro de Segurança", "Testador de Penetração", "Consultor de Segurança"],
    "cibersegurança_sênior": ["Engenheiro de Segurança Sênior", "CISO", "Líder Arquiteto de Segurança"],
}

QUIZ_QUESTIONS = [
    {
        "id": "area",
        "text": "Qual área mais te anima? Opções: Frontend, Backend, Ciência de Dados, Mobile, DevOps, Full Stack, Governança de Dados, Design UX, Design UI, Liderança, RH, Marketing de Mídias Sociais, Growth Marketing, Gestão de Produtos ou Cibersegurança",
        "field": "Área de interesse",
    },
    {
        "id": "level",
        "text": "Como você descreveria seu nível de experiência atual? Escolha um: Júnior, Pleno ou Sênior",
        "field": "Nível de experiência",
    },
    {
        "id": "work_pref",
        "text": "Como você prefere trabalhar? Opções: Remoto, Híbrido ou Presencial",
        "field": "Preferências de trabalho",
    },
    {
        "id": "location",
        "text": "Onde você está localizado? Me diga sua cidade e estado, ou apenas diga 'Remoto'",
        "field": "Localização",
    },
    {
        "id": "soft_skills",
        "text": "Quais são suas soft skills mais fortes? Pense em coisas como comunicação, trabalho em equipe, liderança, resolução de problemas — o que for mais natural para você",
        "field": "Soft skills",
    },
    {
        "id": "career_goal",
        "text": "Onde você se vê em sua carreira? Opções: Crescimento técnico, Transição de carreira, Primeiro emprego ou Trilha de liderança",
        "field": "Objetivo de carreira",
    },
    {
        "id": "skills",
        "text": "Quais habilidades técnicas você já tem? Apenas liste-as separadas por vírgulas — por exemplo: Python, SQL, Excel, Figma, Git",
        "field": "Habilidades atuais",
    },
]

MENU_TEXT = """
╔══════════════════════════════════════════╗
║         CENTRAL DE OPERAÇÕES             ║
╠══════════════════════════════════════════╣
║  [A]  Buscar Vagas          ⚔  Scout    ║
║  [B]  Encontrar Cursos      📚 Curator  ║
║  [C]  Entrevista Simulada   🎯 Coach    ║
║  [D]  Refazer Quiz          ↺  Reset    ║
╚══════════════════════════════════════════╝

Digite A, B, C ou D:"""


class MaestroAgent(BaseAgent):
    """Orquestrador principal — gerencia quiz, menu e despacho de sub-agentes."""

    name = "Maestro"

    def __init__(self):
        super().__init__()
        # Estado da sessão em memória
        self.quiz_answers: dict[str, str] = {}
        self.quiz_step: int = 0
        self.mode: str = "init"  # init | quiz | menu | scout | curator | coach
        self.coach_step: int = 0
        self.interview_context: str = ""

    # ─── Utilitários de arquivo ───────────────────────────────────────────────

    def _load_quiz(self) -> dict[str, str]:
        """Lê o quiz do arquivo e retorna como dicionário."""
        content = self._read_file(config.QUIZ_FILE)
        result: dict[str, str] = {}
        for line in content.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
        return result

    def _save_quiz(self, answers: dict[str, str]) -> None:
        """Salva as respostas do quiz no arquivo."""
        lines = [
            f"Área de interesse: {answers.get('Área de interesse', '')}",
            f"Nível de experiência: {answers.get('Nível de experiência', '')}",
            f"Preferências de trabalho: {answers.get('Preferências de trabalho', '')}",
            f"Localização: {answers.get('Localização', '')}",
            f"Soft skills: {answers.get('Soft skills', '')}",
            f"Objetivo de carreira: {answers.get('Objetivo de carreira', '')}",
            f"Habilidades atuais: {answers.get('Habilidades atuais', '')}",
            f"Concluído: {answers.get('Concluído', 'false')}",
        ]
        self._write_file(config.QUIZ_FILE, "\n".join(lines))

    def _generate_profile(self, answers: dict[str, str]) -> None:
        """Gera o user-profile.md a partir das respostas do quiz."""
        area = answers.get("Área de interesse", "").lower()
        level = answers.get("Nível de experiência", "").lower()
        key = f"{area}_{level}"
        roles = TARGET_ROLES_MAP.get(key, ["Profissional de Tecnologia"])
        roles_str = ", ".join(roles)

        lines = [
            f"Área de interesse: {answers.get('Área de interesse', '')}",
            f"Nível de experiência: {answers.get('Nível de experiência', '')}",
            f"Preferências de trabalho: {answers.get('Preferências de trabalho', '')}",
            f"Localização: {answers.get('Localização', '')}",
            f"Soft skills: {answers.get('Soft skills', '')}",
            f"Objetivo de carreira: {answers.get('Objetivo de carreira', '')}",
            f"Habilidades atuais: {answers.get('Habilidades atuais', '')}",
            f"Funções alvo: {roles_str}",
            f"Concluído: true",
        ]
        self._write_file(config.PROFILE_FILE, "\n".join(lines))

    def _reset_data_files(self) -> None:
        """Remove arquivos de dados derivados ao refazer o quiz."""
        for path in [config.JOB_RESULTS_FILE, config.COURSE_RECS_FILE, config.INTERVIEW_FILE]:
            if path.exists():
                path.unlink()

    # ─── Fluxo principal ──────────────────────────────────────────────────────

    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        """
        Ponto de entrada principal.
        context deve conter:
          - 'message': texto enviado pelo usuário
          - 'mode': estado atual da sessão (passado pelo router)
          - 'quiz_step': passo atual do quiz
          - 'quiz_answers': respostas parciais do quiz
          - 'coach_step': passo atual da entrevista
          - 'interview_context': contexto da vaga para entrevista
        """
        # Restaura estado da sessão
        self.mode = context.get("mode", "init")
        self.quiz_step = context.get("quiz_step", 0)
        self.quiz_answers = context.get("quiz_answers", {})
        self.coach_step = context.get("coach_step", 0)
        self.interview_context = context.get("interview_context", "")

        message = context.get("message", "").strip()

        if self.mode == "init":
            async for token in self._handle_init():
                yield token

        elif self.mode == "quiz":
            async for token in self._handle_quiz(message):
                yield token

        elif self.mode == "menu":
            async for token in self._handle_menu(message):
                yield token

        elif self.mode == "coach":
            async for token in self._handle_coach(message):
                yield token

        else:
            # Fallback: volta ao menu
            async for token in self._show_menu():
                yield token

    # ─── Init ─────────────────────────────────────────────────────────────────

    async def _handle_init(self) -> AsyncGenerator[str, None]:
        """Inicialização: verifica quiz e decide próximo passo."""
        yield "◈ MAESTRO ONLINE\n\n"
        yield "Bem-vindo ao **Recoloca IA** — seu sistema de desenvolvimento de carreira.\n\n"

        quiz_data = self._load_quiz()

        if quiz_data.get("Concluído") == "true":
            # Quiz completo — gera perfil e vai ao menu
            self._generate_profile(quiz_data)
            area = quiz_data.get("Área de interesse", "")
            level = quiz_data.get("Nível de experiência", "")
            yield f"✓ Perfil carregado — **{area}** · **{level}**\n\n"
            async for token in self._show_menu():
                yield token
            # Sinaliza transição de estado
            yield "\n__STATE__:menu"

        elif quiz_data and quiz_data.get("Concluído") != "true":
            # Quiz incompleto
            yield "Encontrei um perfil incompleto salvo.\n"
            yield "Deseja **continuar de onde parou** ou **refazer o quiz**?\n\n"
            yield "Digite **continuar** ou **refazer**:\n"
            yield "\n__STATE__:quiz_resume"

        else:
            # Sem quiz — inicia
            yield "Para começar, preciso conhecer seu perfil profissional.\n"
            yield "Vou fazer algumas perguntas rápidas — uma de cada vez.\n\n"
            yield f"**Pergunta 1/7:** {QUIZ_QUESTIONS[0]['text']}\n"
            yield "\n__STATE__:quiz:0"

    # ─── Quiz ─────────────────────────────────────────────────────────────────

    async def _handle_quiz(self, message: str) -> AsyncGenerator[str, None]:
        """Processa resposta do quiz e avança para próxima pergunta."""
        if not message:
            # Repete a pergunta atual
            q = QUIZ_QUESTIONS[self.quiz_step]
            yield f"**Pergunta {self.quiz_step + 1}/7:** {q['text']}\n"
            yield f"\n__STATE__:quiz:{self.quiz_step}"
            return

        # Salva resposta atual
        field = QUIZ_QUESTIONS[self.quiz_step]["field"]
        self.quiz_answers[field] = message
        next_step = self.quiz_step + 1

        if next_step >= len(QUIZ_QUESTIONS):
            # Quiz completo
            self.quiz_answers["Concluído"] = "true"
            self._save_quiz(self.quiz_answers)
            self._generate_profile(self.quiz_answers)

            area = self.quiz_answers.get("Área de interesse", "")
            level = self.quiz_answers.get("Nível de experiência", "")
            yield f"\n✓ Perfil criado com sucesso — **{area}** · **{level}**\n\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
        else:
            # Próxima pergunta
            q = QUIZ_QUESTIONS[next_step]
            yield f"\n**Pergunta {next_step + 1}/7:** {q['text']}\n"
            yield f"\n__STATE__:quiz:{next_step}:{self._encode_answers()}"

    def _encode_answers(self) -> str:
        """Serializa respostas parciais para passar no token de estado."""
        import json, base64
        return base64.b64encode(json.dumps(self.quiz_answers).encode()).decode()

    # ─── Menu ─────────────────────────────────────────────────────────────────

    async def _show_menu(self) -> AsyncGenerator[str, None]:
        """Exibe o menu principal."""
        yield MENU_TEXT

    async def _handle_menu(self, message: str) -> AsyncGenerator[str, None]:
        """Processa seleção do menu."""
        choice = message.upper().strip()

        if choice == "A":
            async for token in self._dispatch_scout():
                yield token

        elif choice == "B":
            async for token in self._dispatch_curator():
                yield token

        elif choice == "C":
            async for token in self._dispatch_coach_start():
                yield token

        elif choice == "D":
            async for token in self._handle_reset():
                yield token

        else:
            yield f"⚠ Opção inválida: **{message}**\n"
            yield "Por favor, escolha uma das opções do menu: A, B, C ou D.\n\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"

    # ─── Scout ────────────────────────────────────────────────────────────────

    async def _dispatch_scout(self) -> AsyncGenerator[str, None]:
        """Despacha o agente Scout para busca de vagas."""
        yield "\n⚔ **SCOUT** — Iniciando varredura de vagas...\n\n"
        yield "__STATE__:agent_running:scout\n"

        profile = self._read_file(config.PROFILE_FILE)
        if not profile:
            yield "⚠ Perfil não encontrado. Complete o quiz primeiro.\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

        scout = ScoutAgent()
        result_chunks = []

        async for token in scout.run({"profile": profile}):
            result_chunks.append(token)
            yield token

        # Salva resultado
        full_result = "".join(result_chunks)
        self._write_file(config.JOB_RESULTS_FILE, full_result)

        yield "\n\n"
        async for token in self._show_menu():
            yield token
        yield "\n__STATE__:menu"

    # ─── Curator ──────────────────────────────────────────────────────────────

    async def _dispatch_curator(self) -> AsyncGenerator[str, None]:
        """Despacha o agente Curator para busca de cursos."""
        job_results = self._read_file(config.JOB_RESULTS_FILE)
        if not job_results or "habilidades_faltantes" not in job_results:
            yield "⚠ Nenhuma lacuna de habilidade encontrada.\n"
            yield "Por favor, busque vagas primeiro (opção **A**) para identificar quais habilidades você precisa desenvolver.\n\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

        yield "\n📚 **CURATOR** — Buscando trilha de aprendizado...\n\n"
        yield "__STATE__:agent_running:curator\n"

        profile = self._read_file(config.PROFILE_FILE)
        curator = CuratorAgent()
        result_chunks = []

        async for token in curator.run({"profile": profile, "job_results": job_results}):
            result_chunks.append(token)
            yield token

        full_result = "".join(result_chunks)
        saved_result = f"Data da Busca: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n{full_result}"
        self._write_file(config.COURSE_RECS_FILE, saved_result)

        yield "\n\n"
        async for token in self._show_menu():
            yield token
        yield "\n__STATE__:menu"

    # ─── Coach ────────────────────────────────────────────────────────────────

    async def _dispatch_coach_start(self) -> AsyncGenerator[str, None]:
        """Inicia a sequência de entrevista simulada (Despacho 1)."""
        job_results = self._read_file(config.JOB_RESULTS_FILE)
        profile = self._read_file(config.PROFILE_FILE)

        # Resolve contexto da vaga
        if job_results:
            # Extrai primeira vaga dos resultados
            lines = job_results.splitlines()
            titulo = next((l.split(":", 1)[1].strip() for l in lines if l.strip().startswith("titulo:")), "")
            empresa = next((l.split(":", 1)[1].strip() for l in lines if l.strip().startswith("empresa:")), "")
            self.interview_context = f"{titulo} — {empresa}" if titulo else "Posição baseada no seu perfil"
        else:
            # Usa funções alvo do perfil
            for line in profile.splitlines():
                if line.startswith("Funções alvo:"):
                    self.interview_context = line.split(":", 1)[1].strip()
                    break
            else:
                self.interview_context = "Posição baseada no seu perfil"

        # Inicializa arquivo de sessão
        session_content = f"Contexto da Vaga: {self.interview_context}\nNúmero da Pergunta: 1\nHistórico de Perguntas e Respostas:\n"
        self._write_file(config.INTERVIEW_FILE, session_content)

        yield f"\n🎯 **COACH** — Entrevista simulada para: **{self.interview_context}**\n\n"
        yield "__STATE__:agent_running:coach\n"

        coach = CoachAgent()
        result_chunks = []
        async for token in coach.run({
            "step": 1,
            "profile": profile,
            "interview_context": self.interview_context,
            "history": [],
        }):
            result_chunks.append(token)
            yield token

        coach_output = "".join(result_chunks)
        question = self._extract_coach_section(coach_output, "pergunta_atual") or self._strip_coach_text(coach_output)
        self._update_interview_session(
            [{"role": "assistant", "step": 1, "content": question}],
            1,
        )

        yield f"\n__STATE__:coach:1:{self.interview_context}"

    async def _handle_coach(self, message: str) -> AsyncGenerator[str, None]:
        """Processa resposta do usuário durante a entrevista e avança para próximo passo."""
        profile = self._read_file(config.PROFILE_FILE)
        session = self._read_file(config.INTERVIEW_FILE)

        # Extrai histórico do arquivo de sessão
        history = self._parse_interview_history(session)

        # Registra resposta do usuário
        current_q_num = self.coach_step  # coach_step = número da pergunta que acabou de ser respondida
        history.append({"role": "user", "step": current_q_num, "content": message})
        self._update_interview_session(history, current_q_num)

        next_step = current_q_num + 1

        if next_step > 5:
            # Todas as perguntas respondidas — pontuação final
            yield "\n🎯 **COACH** — Calculando pontuação final...\n\n"
            yield "__STATE__:agent_running:coach\n"

            coach = CoachAgent()
            result_chunks = []
            async for token in coach.run({
                "step": 6,
                "profile": profile,
                "interview_context": self.interview_context,
                "history": history,
            }):
                result_chunks.append(token)
                yield token

            coach_output = "".join(result_chunks)
            feedback = self._extract_coach_section(coach_output, "feedback_anterior")
            score = self._extract_coach_section(coach_output, "pontuacao_final")
            improvements = self._extract_coach_section(coach_output, "areas_de_melhoria")
            if feedback:
                history.append({"role": "feedback", "step": current_q_num, "content": feedback})
            self._update_interview_session(
                history,
                current_q_num,
                final_score=score,
                improvements=improvements,
            )

            yield "\n\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
        else:
            # Próxima pergunta
            yield f"\n🎯 **COACH** — Avaliando resposta e gerando pergunta {next_step}...\n\n"
            yield "__STATE__:agent_running:coach\n"

            coach = CoachAgent()
            result_chunks = []
            async for token in coach.run({
                "step": next_step,
                "profile": profile,
                "interview_context": self.interview_context,
                "history": history,
            }):
                result_chunks.append(token)
                yield token

            coach_output = "".join(result_chunks)
            feedback = self._extract_coach_section(coach_output, "feedback_anterior")
            question = self._extract_coach_section(coach_output, "pergunta_atual")
            if feedback:
                history.append({"role": "feedback", "step": current_q_num, "content": feedback})
            if question:
                history.append({"role": "assistant", "step": next_step, "content": question})
            self._update_interview_session(history, next_step)

            yield f"\n__STATE__:coach:{next_step}:{self.interview_context}"

    def _parse_interview_history(self, session: str) -> list[dict]:
        """Extrai histórico de perguntas e respostas do arquivo de sessão."""
        history = []
        for line in session.splitlines():
            line = line.strip()
            feedback_match = re.match(r"Feedback\s+(\d+):\s*(.*)", line)
            if feedback_match:
                history.append({
                    "role": "feedback",
                    "step": int(feedback_match.group(1)),
                    "content": feedback_match.group(2),
                })
                continue

            match = re.match(r"(P|R)(\d+):\s*(.*)", line)
            if match:
                role = "assistant" if match.group(1) == "P" else "user"
                step = int(match.group(2))
                content = match.group(3)
                history.append({"role": role, "step": step, "content": content})
        return history

    def _update_interview_session(
        self,
        history: list[dict],
        current_step: int,
        final_score: str | None = None,
        improvements: str | None = None,
    ) -> None:
        """Atualiza o arquivo de sessão com o histórico atual."""
        lines = [f"Contexto da Vaga: {self.interview_context}",
                 f"Número da Pergunta: {current_step}",
                 "Histórico de Perguntas e Respostas:"]
        for item in history:
            if item["role"] == "feedback":
                lines.append(f"  Feedback {item['step']}: {item['content']}")
            else:
                prefix = "P" if item["role"] == "assistant" else "R"
                lines.append(f"  {prefix}{item['step']}: {item['content']}")
        if final_score:
            lines.extend(["", f"PontuaÃ§Ã£o Final: {final_score}"])
        if improvements:
            lines.extend(["Ãreas de Melhoria:", improvements])
        self._write_file(config.INTERVIEW_FILE, "\n".join(lines))

    def _extract_coach_section(self, text: str, section: str) -> str:
        pattern = rf"###\s+{re.escape(section)}\s*\n(.*?)(?=\n###\s+|\Z)"
        match = re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE)
        if not match:
            return ""
        return self._strip_coach_text(match.group(1))

    def _strip_coach_text(self, text: str) -> str:
        lines = []
        for line in text.strip().splitlines():
            clean = line.strip()
            if not clean or clean.startswith("## RESPOSTA:") or clean.startswith("###"):
                continue
            if clean.lower() in {"sucesso", "erro"}:
                continue
            lines.append(clean)
        return " ".join(lines).strip()

    # ─── Reset ────────────────────────────────────────────────────────────────

    async def _handle_reset(self) -> AsyncGenerator[str, None]:
        """Reseta todos os dados e reinicia o quiz."""
        self._reset_data_files()
        # Sobrescreve quiz com estado vazio
        self._write_file(config.QUIZ_FILE, "Concluído: false\n")

        self.quiz_answers = {}
        self.quiz_step = 0

        yield "\n↺ **Reset completo.** Todos os dados foram apagados.\n\n"
        yield "Vamos recomeçar do zero.\n\n"
        yield f"**Pergunta 1/7:** {QUIZ_QUESTIONS[0]['text']}\n"
        yield "\n__STATE__:quiz:0"
