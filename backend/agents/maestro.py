"""
Agente Maestro — Orquestrador principal do sistema Recoloca IA.

Responsabilidades:
- Gerenciar o quiz de perfil do usuário
- Apresentar o menu de opções
- Despachar sub-agentes (Scout, Curator, Coach)
- Manter estado nos arquivos data/
"""

from __future__ import annotations

import base64
import json
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
╔════════════════════════════════════════════════════╗
║              ESTEIRA DE CARREIRA                  ║
╠════════════════════════════════════════════════════╣
║  [A]  Encontrar oportunidades compatíveis  Scout  ║
║  [B]  Mapear lacunas e evolução           Curator ║
║  [C]  Simular entrevista direcionada       Coach  ║
║  [D]  Refazer diagnóstico                 Maestro ║
╚════════════════════════════════════════════════════╝

Digite A, B, C ou D:"""


class MaestroAgent(BaseAgent):
    """Orquestrador principal — gerencia quiz, menu e despacho de sub-agentes."""

    name = "Maestro"
    # Frase enviada pelo botão "Iniciar/Continuar diagnóstico" do frontend.
    # É um comando, não uma resposta de quiz — interceptado em run().
    START_PROFILE_COMMAND = "quero criar meu perfil profissional"
    COACH_EXIT_COMMANDS = {
        "sair",
        "encerrar",
        "cancelar",
        "voltar",
        "menu",
        "voltar ao menu",
        "parar entrevista",
    }

    def __init__(self):
        super().__init__()
        # Estado da sessão em memória
        self.quiz_answers: dict[str, str] = {}
        self.quiz_step: int = 0
        self.mode: str = "init"  # init | quiz | menu | scout | curator | coach
        self.coach_step: int = 0
        self.interview_context: str = ""
        # Filtro de recência das vagas escolhido no frontend (24h/7d/1mês/todas).
        self.date_filter: str = ""

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

    def _profile_summary(self, answers: dict[str, str]) -> str:
        area = answers.get("Área de interesse", "Não informado")
        level = answers.get("Nível de experiência", "Não informado")
        preference = answers.get("Preferências de trabalho", "Não informado")
        location = answers.get("Localização", "Não informado")
        goal = answers.get("Objetivo de carreira", "Não informado")
        skills = answers.get("Habilidades atuais", "Não informado")
        roles = ""

        profile = self._read_file(config.PROFILE_FILE)
        for line in profile.splitlines():
            if line.startswith("Funções alvo:"):
                roles = line.split(":", 1)[1].strip()
                break

        if not roles:
            roles = "Profissional de Tecnologia"

        return (
            "Diagnóstico concluído. Aqui está a base que vou usar na sua jornada:\n\n"
            f"1. Área: {area}\n"
            f"2. Nível: {level}\n"
            f"3. Modelo desejado: {preference}\n"
            f"4. Localização: {location}\n"
            f"5. Objetivo: {goal}\n"
            f"6. Habilidades atuais: {skills}\n"
            f"7. Funções alvo: {roles}\n\n"
            "Próximo passo: comece por oportunidades compatíveis, depois use as lacunas para guiar sua evolução.\n\n"
        )

    def _next_quiz_step(self, answers: dict[str, str]) -> int:
        for index, question in enumerate(QUIZ_QUESTIONS):
            if not answers.get(question["field"], "").strip():
                return index
        return len(QUIZ_QUESTIONS)

    def _is_profile_complete(self) -> bool:
        profile = self._read_file(config.PROFILE_FILE)
        if not profile.strip():
            return False

        fields: dict[str, str] = {}
        for line in profile.splitlines():
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            normalized_key = (
                key.strip()
                .lower()
                .replace("í", "i")
                .replace("á", "a")
                .replace("ã", "a")
                .replace("õ", "o")
                .replace("ó", "o")
                .replace("ú", "u")
                .replace("ç", "c")
                .replace("ê", "e")
                .replace("é", "e")
            )
            fields[normalized_key] = value.strip()

        required_fields = [
            "area de interesse",
            "nivel de experiencia",
            "habilidades atuais",
            "funcoes alvo",
        ]
        if any(not fields.get(field) for field in required_fields):
            return False

        return fields.get("concluido", "").strip().lower() == "true"

    def _reset_data_files(self) -> None:
        """Remove arquivos de dados derivados ao refazer o quiz."""
        for path in [config.PROFILE_FILE, config.JOB_RESULTS_FILE, config.COURSE_RECS_FILE, config.INTERVIEW_FILE]:
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
        self.date_filter = context.get("date_filter", "") or ""

        message = context.get("message", "").strip()

        # Comando explícito de (re)iniciar o diagnóstico. Nunca deve ser tratado
        # como resposta de quiz; aproveita o currículo analisado para pré-preencher.
        if message.casefold() == self.START_PROFILE_COMMAND:
            async for token in self._start_diagnostico():
                yield token
            return

        if self.mode == "init":
            async for token in self._handle_init():
                yield token

        elif self.mode == "quiz":
            async for token in self._handle_quiz(message):
                yield token

        elif self.mode == "quiz_resume":
            async for token in self._handle_quiz_resume(message):
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
            yield self._profile_summary(quiz_data)
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
            # Sem quiz — inicia (aproveitando o currículo quando houver)
            yield "Para começar, preciso conhecer seu perfil profissional.\n"
            if not config.RESUME_ANALYSIS_FILE.exists():
                yield "Se preferir, você também pode enviar um currículo para eu analisar antes do quiz.\n"
            async for token in self._start_diagnostico():
                yield token

    # ─── Quiz ─────────────────────────────────────────────────────────────────

    async def _handle_quiz_resume(self, message: str) -> AsyncGenerator[str, None]:
        """Retoma ou reinicia um quiz incompleto salvo em data/personality-quiz.md."""
        choice = message.strip().lower()

        if choice in {"refazer", "reiniciar", "recomeçar", "recomecar"}:
            async for token in self._handle_reset():
                yield token
            return

        if choice not in {"continuar", "seguir", "sim"}:
            yield "Escolha **continuar** para retomar o quiz ou **refazer** para começar de novo.\n"
            yield "\n__STATE__:quiz_resume"
            return

        quiz_data = self._load_quiz()
        self.quiz_answers = {
            key: value
            for key, value in quiz_data.items()
            if key != "Concluído" and value.strip()
        }
        self.quiz_step = self._next_quiz_step(self.quiz_answers)

        if self.quiz_step >= len(QUIZ_QUESTIONS):
            self.quiz_answers["Concluído"] = "true"
            self._save_quiz(self.quiz_answers)
            self._generate_profile(self.quiz_answers)
            yield "✓ Perfil consolidado a partir do quiz salvo.\n\n"
            yield self._profile_summary(self.quiz_answers)
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

        q = QUIZ_QUESTIONS[self.quiz_step]
        yield f"Vamos continuar do ponto salvo.\n\n**Pergunta {self.quiz_step + 1}/7:** {q['text']}\n"
        yield f"\n__STATE__:quiz:{self.quiz_step}:{self._encode_answers()}"

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
        # Avança para o próximo campo ainda não respondido (pula os já preenchidos
        # pelo currículo), em vez de seguir linearmente.
        next_step = self._next_quiz_step(self.quiz_answers)

        if next_step >= len(QUIZ_QUESTIONS):
            # Quiz completo
            self.quiz_answers["Concluído"] = "true"
            self._save_quiz(self.quiz_answers)
            self._generate_profile(self.quiz_answers)

            area = self.quiz_answers.get("Área de interesse", "")
            level = self.quiz_answers.get("Nível de experiência", "")
            yield f"\n✓ Perfil criado com sucesso — **{area}** · **{level}**\n\n"
            yield self._profile_summary(self.quiz_answers)
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
        return base64.b64encode(json.dumps(self.quiz_answers).encode()).decode()

    # ─── Diagnóstico (quiz + currículo) ───────────────────────────────────────

    @staticmethod
    def _normalize_level(level: str) -> str:
        """Mapeia o nível estimado do currículo para Júnior/Pleno/Sênior."""
        value = level.casefold()
        if "sênior" in value or "senior" in value:
            return "Sênior"
        if "pleno" in value:
            return "Pleno"
        if "júnior" in value or "junior" in value or "estágio" in value or "estagio" in value:
            return "Júnior"
        return ""

    def _seed_answers_from_resume(self) -> dict[str, str]:
        """Extrai respostas do quiz a partir de data/resume-analysis.md.

        Aproveita as palavras-chave do currículo (área, nível, habilidades e
        soft skills) para pré-preencher o quiz e perguntar só o que falta.
        """
        content = self._read_file(config.RESUME_ANALYSIS_FILE)
        if not content.strip():
            return {}

        lines = [line.rstrip() for line in content.splitlines()]
        placeholders = {"não identificado", "nao identificado", ""}

        def list_after(header: str) -> list[str]:
            items: list[str] = []
            capturing = False
            for line in lines:
                stripped = line.strip()
                if stripped == header:
                    capturing = True
                    continue
                if not capturing:
                    continue
                if stripped.startswith("- "):
                    items.append(stripped[2:].strip())
                elif stripped == "":
                    if items:
                        break
                else:
                    break
            return [item for item in items if item.casefold() not in placeholders]

        def value_after(header: str) -> str:
            capturing = False
            for line in lines:
                stripped = line.strip()
                if stripped == header:
                    capturing = True
                    continue
                if capturing and stripped:
                    return stripped
            return ""

        answers: dict[str, str] = {}

        areas = list_after("Áreas prováveis:")
        if areas:
            answers["Área de interesse"] = areas[0]

        level = self._normalize_level(value_after("Nível estimado:"))
        if level:
            answers["Nível de experiência"] = level

        skills = list_after("Habilidades técnicas detectadas:")
        if skills:
            answers["Habilidades atuais"] = ", ".join(skills)

        soft_skills = list_after("Soft skills detectadas:")
        if soft_skills:
            answers["Soft skills"] = ", ".join(soft_skills)

        return answers

    async def _start_diagnostico(self) -> AsyncGenerator[str, None]:
        """Inicia o diagnóstico, pré-preenchendo o quiz com o currículo analisado.

        Pergunta apenas os campos que o currículo não cobre.
        """
        seeded = self._seed_answers_from_resume()
        self.quiz_answers = dict(seeded)
        self.quiz_step = self._next_quiz_step(self.quiz_answers)
        self._save_quiz({**self.quiz_answers, "Concluído": "false"})

        if seeded:
            yield "\n◈ Aproveitei seu currículo para adiantar o diagnóstico:\n"
            if seeded.get("Área de interesse"):
                yield f"• Área: **{seeded['Área de interesse']}**\n"
            if seeded.get("Nível de experiência"):
                yield f"• Nível: **{seeded['Nível de experiência']}**\n"
            if seeded.get("Habilidades atuais"):
                yield f"• Habilidades: {seeded['Habilidades atuais']}\n"
            if seeded.get("Soft skills"):
                yield f"• Soft skills: {seeded['Soft skills']}\n"
            yield "\n"

        # Currículo já cobriu todos os campos do quiz.
        if self.quiz_step >= len(QUIZ_QUESTIONS):
            self.quiz_answers["Concluído"] = "true"
            self._save_quiz(self.quiz_answers)
            self._generate_profile(self.quiz_answers)
            area = self.quiz_answers.get("Área de interesse", "")
            level = self.quiz_answers.get("Nível de experiência", "")
            yield f"✓ Perfil montado a partir do currículo — **{area}** · **{level}**\n\n"
            yield self._profile_summary(self.quiz_answers)
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

        if seeded:
            yield "Só preciso confirmar o que o currículo não deixa claro.\n\n"
        else:
            yield "Vou fazer algumas perguntas rápidas — uma de cada vez.\n\n"

        question = QUIZ_QUESTIONS[self.quiz_step]
        yield f"**Pergunta {self.quiz_step + 1}/7:** {question['text']}\n"
        yield f"\n__STATE__:quiz:{self.quiz_step}:{self._encode_answers()}"

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
        profile = self._read_file(config.PROFILE_FILE)
        if not profile or not self._is_profile_complete():
            yield "⚠ Perfil não encontrado. Complete o quiz primeiro.\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

        yield "\n⚔ **SCOUT** — Iniciando varredura de vagas...\n\n"
        yield "__STATE__:agent_running:scout\n"

        scout = ScoutAgent()
        result_chunks = []

        async for token in scout.run({"profile": profile, "date_filter": self.date_filter}):
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
        if not self._is_profile_complete():
            yield "⚠ Perfil incompleto. Complete o quiz antes de buscar cursos.\n\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

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
        profile = self._read_file(config.PROFILE_FILE)
        if not profile or not self._is_profile_complete():
            yield "⚠ Perfil incompleto. Complete o quiz antes de iniciar a entrevista simulada.\n\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

        job_results = self._read_file(config.JOB_RESULTS_FILE)
        if not job_results or "habilidades_faltantes" not in job_results:
            yield "⚠ Ainda não há resultados do Scout para direcionar a entrevista.\n"
            yield "Rode a opção **A** primeiro para mapear oportunidades, lacunas e requisitos recorrentes.\n\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

        course_recommendations = self._read_file(config.COURSE_RECS_FILE)
        if not course_recommendations.strip():
            yield "ℹ A trilha do Curator ainda não foi gerada. Vou iniciar a entrevista com base no perfil e nas oportunidades; para uma preparação mais completa, rode a opção **B** depois.\n\n"

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
        try:
            async for token in coach.run({
                "step": 1,
                "profile": profile,
                "job_results": job_results,
                "course_recommendations": course_recommendations,
                "interview_context": self.interview_context,
                "history": [],
            }):
                result_chunks.append(token)
                yield token
        except Exception as exc:
            error_response = self._coach_error_response(exc)
            yield error_response
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

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
        job_results = self._read_file(config.JOB_RESULTS_FILE)
        course_recommendations = self._read_file(config.COURSE_RECS_FILE)
        session = self._read_file(config.INTERVIEW_FILE)

        if self._is_coach_exit_command(message):
            self._mark_interview_paused(session)
            yield self._coach_pause_response()
            yield "\n\n"
            async for token in self._show_menu():
                yield token
            yield "\n__STATE__:menu"
            return

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
            try:
                async for token in coach.run({
                    "step": 6,
                    "profile": profile,
                    "job_results": job_results,
                    "course_recommendations": course_recommendations,
                    "interview_context": self.interview_context,
                    "history": history,
                }):
                    result_chunks.append(token)
                    yield token
            except Exception as exc:
                yield self._coach_error_response(exc)
                async for token in self._show_menu():
                    yield token
                yield "\n__STATE__:menu"
                return

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
            try:
                async for token in coach.run({
                    "step": next_step,
                    "profile": profile,
                    "job_results": job_results,
                    "course_recommendations": course_recommendations,
                    "interview_context": self.interview_context,
                    "history": history,
                }):
                    result_chunks.append(token)
                    yield token
            except Exception as exc:
                yield self._coach_error_response(exc)
                async for token in self._show_menu():
                    yield token
                yield "\n__STATE__:menu"
                return

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

    def _coach_error_response(self, exc: Exception) -> str:
        return (
            "## RESPOSTA: COACH\n"
            "### estado\n"
            "erro\n\n"
            "### resumo\n"
            "Nao consegui concluir a etapa da entrevista, mas o WebSocket continuou ativo.\n\n"
            "### dados\n"
            f"tipo_erro: {type(exc).__name__}\n\n"
            "### erros\n"
            "Erro recuperavel no Coach. Tente iniciar a entrevista novamente.\n"
        )

    def _is_coach_exit_command(self, message: str) -> bool:
        normalized = re.sub(r"\s+", " ", message.strip().casefold()).strip(" .!?")
        return normalized in self.COACH_EXIT_COMMANDS

    def _mark_interview_paused(self, session: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        pause_lines = [
            "",
            f"Status da Entrevista: pausada em {timestamp}",
            "Progresso salvo: true",
        ]

        if session.strip():
            content = session.rstrip() + "\n" + "\n".join(pause_lines)
        else:
            context = self.interview_context or "Posição baseada no seu perfil"
            content = "\n".join([
                f"Contexto da Vaga: {context}",
                "Número da Pergunta: 0",
                "Histórico de Perguntas e Respostas:",
                *pause_lines,
            ])

        self._write_file(config.INTERVIEW_FILE, content)

    def _coach_pause_response(self) -> str:
        return (
            "## RESPOSTA: COACH\n"
            "### estado\n"
            "sucesso\n\n"
            "### resumo\n"
            "Entrevista pausada/encerrada com sucesso.\n\n"
            "### dados\n"
            "progresso_salvo: true\n"
            "proxima_acao: voltar para a esteira de carreira\n\n"
            "### erros\n"
            "Nenhum erro.\n"
        )

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
            lines.extend(["", f"Pontuação Final: {final_score}"])
        if improvements:
            lines.extend(["Áreas de Melhoria:", improvements])
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
