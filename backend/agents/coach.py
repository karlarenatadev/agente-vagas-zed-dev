"""
Agente Coach — Simulação de entrevistas de emprego.

Fluxo (6 despachos sequenciais):
- Despacho 1: Gera Pergunta 1
- Despachos 2-5: Avalia resposta anterior + gera próxima pergunta
- Despacho 6: Avalia última resposta + pontuação final
"""

from __future__ import annotations

from typing import AsyncGenerator

import config
from agents.base import BaseAgent


COACH_SYSTEM_PROMPT = """Você é o Coach, agente especializado em simulação de entrevistas de emprego do sistema Recoloca IA.

Seu papel:
- Conduzir entrevistas simuladas realistas e construtivas
- Fazer perguntas técnicas e comportamentais relevantes para a vaga
- Avaliar respostas com feedback específico e acionável
- Usar a metodologia STAR (Situação, Tarefa, Ação, Resultado) para avaliar respostas comportamentais
- Ser encorajador mas honesto

Regras de formato:
- NUNCA use tabelas markdown
- Seja direto e objetivo
- Feedback deve ser construtivo e específico
- Perguntas devem ser realistas para o nível e área do candidato

Tipos de perguntas (alterne entre elas):
1. Comportamental: "Me conte sobre uma vez que..."
2. Técnica: "Como você implementaria..."
3. Situacional: "O que você faria se..."
4. Motivacional: "Por que você quer trabalhar com..."
5. Competência: "Qual sua experiência com..." """


class CoachAgent(BaseAgent):
    """Agente de simulação de entrevistas."""

    name = "Coach"

    def _format_history(self, history: list[dict]) -> str:
        """Formata histórico de perguntas e respostas para o prompt."""
        if not history:
            return "Nenhum histórico anterior."
        lines = []
        for item in history:
            prefix = "Pergunta" if item["role"] == "assistant" else "Resposta do candidato"
            lines.append(f"{prefix} {item['step']}: {item['content']}")
        return "\n".join(lines)

    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        """
        Executa um passo da entrevista.
        context: {
            'step': int (1-6),
            'profile': str,
            'interview_context': str,
            'history': list[dict]
        }
        """
        step = context.get("step", 1)
        profile = context.get("profile", "")
        interview_context = context.get("interview_context", "")
        history = context.get("history", [])

        history_text = self._format_history(history)

        if step == 1:
            async for token in self._generate_question(step, profile, interview_context, history_text):
                yield token

        elif 2 <= step <= 5:
            async for token in self._evaluate_and_ask(step, profile, interview_context, history_text):
                yield token

        elif step == 6:
            async for token in self._final_evaluation(profile, interview_context, history_text):
                yield token

    async def _generate_question(
        self,
        step: int,
        profile: str,
        interview_context: str,
        history_text: str,
    ) -> AsyncGenerator[str, None]:
        """Gera a primeira pergunta da entrevista."""
        prompt = f"""Você está conduzindo uma entrevista simulada.

Contexto da vaga: {interview_context}

Perfil do candidato:
{profile}

Histórico anterior:
{history_text}

Gere a Pergunta {step} da entrevista. Deve ser relevante para a vaga e o perfil do candidato.
Varie entre perguntas comportamentais, técnicas e situacionais.

Responda APENAS com a pergunta, sem introdução ou explicação adicional.
Exemplo: "Me conte sobre um projeto desafiador que você liderou e como você superou os obstáculos."
"""
        yield f"**Pergunta {step}/5:**\n\n"
        async for token in self.stream_llm(COACH_SYSTEM_PROMPT, prompt):
            yield token
        yield "\n"

    async def _evaluate_and_ask(
        self,
        step: int,
        profile: str,
        interview_context: str,
        history_text: str,
    ) -> AsyncGenerator[str, None]:
        """Avalia resposta anterior e gera próxima pergunta."""
        prev_step = step - 1
        prompt = f"""Você está conduzindo uma entrevista simulada.

Contexto da vaga: {interview_context}

Perfil do candidato:
{profile}

Histórico de perguntas e respostas:
{history_text}

Tarefas:
1. Avalie a resposta à Pergunta {prev_step} com feedback construtivo (2-3 frases)
2. Gere a Pergunta {step} da entrevista

Formato de resposta:
**Feedback da Pergunta {prev_step}:**
[seu feedback aqui]

**Pergunta {step}/5:**
[sua pergunta aqui]
"""
        async for token in self.stream_llm(COACH_SYSTEM_PROMPT, prompt):
            yield token
        yield "\n"

    async def _final_evaluation(
        self,
        profile: str,
        interview_context: str,
        history_text: str,
    ) -> AsyncGenerator[str, None]:
        """Gera avaliação final com pontuação e áreas de melhoria."""
        prompt = f"""Você está finalizando uma entrevista simulada.

Contexto da vaga: {interview_context}

Perfil do candidato:
{profile}

Histórico completo da entrevista:
{history_text}

Avalie o desempenho geral do candidato e forneça:
1. Feedback da última resposta (2-3 frases)
2. Pontuação final de 0 a 10
3. Pontos fortes demonstrados (2-3 itens)
4. Áreas de melhoria (2-3 itens)
5. Dica principal para a próxima entrevista

Formato de resposta:
**Feedback da Pergunta 5:**
[feedback]

---

**🏆 RESULTADO FINAL DA ENTREVISTA**

Pontuação: [X]/10

**Pontos Fortes:**
1. [ponto forte]
2. [ponto forte]

**Áreas de Melhoria:**
1. [área]
2. [área]

**Dica Principal:**
[dica]
"""
        async for token in self.stream_llm(COACH_SYSTEM_PROMPT, prompt):
            yield token
        yield "\n"
