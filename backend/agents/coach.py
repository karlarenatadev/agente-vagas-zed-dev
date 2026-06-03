"""
Agente Coach - simulacao de entrevistas.

Fluxo:
1. Despacho 1: gera P1.
2. Despachos 2-5: avalia resposta anterior e gera proxima pergunta.
3. Despacho 6: avalia R5, pontua e entrega areas de melhoria.
"""

from __future__ import annotations

from typing import AsyncGenerator

from agents.base import BaseAgent


COACH_SYSTEM_PROMPT = """Voce e o Coach, agente especializado em entrevistas simuladas do sistema Recoloca IA.

Regras:
1. Nunca use tabelas markdown.
2. Responda no formato exato pedido pelo usuario.
3. Nao invente experiencias do candidato.
4. Calibre dificuldade por senioridade.
5. Alterne perguntas tecnicas, comportamentais e situacionais.
6. Feedback deve ser curto e especifico, com Acerto, Gap e Ajuste.
7. Para respostas comportamentais, avalie STAR: Situacao, Tarefa, Acao e Resultado.
8. Para respostas tecnicas, avalie clareza, exemplos, tradeoffs e riscos.
"""


class CoachAgent(BaseAgent):
    """Agente de simulacao de entrevistas."""

    name = "Coach"

    def _format_history(self, history: list[dict]) -> str:
        if not history:
            return "Nenhum historico anterior."

        lines: list[str] = []
        for item in history:
            role = item.get("role")
            step = item.get("step")
            content = item.get("content", "")
            if role == "assistant":
                lines.append(f"P{step}: {content}")
            elif role == "user":
                lines.append(f"R{step}: {content}")
            elif role == "feedback":
                lines.append(f"Feedback {step}: {content}")
        return "\n".join(lines)

    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        step = int(context.get("step", 1))
        profile = context.get("profile", "")
        interview_context = context.get("interview_context", "")
        history = context.get("history", [])
        history_text = self._format_history(history)

        if step == 1:
            async for token in self._generate_question(profile, interview_context):
                yield token
        elif 2 <= step <= 5:
            async for token in self._evaluate_and_ask(step, profile, interview_context, history_text):
                yield token
        elif step == 6:
            async for token in self._final_evaluation(profile, interview_context, history_text):
                yield token
        else:
            yield "## RESPOSTA: COACH\n### estado\nerro\n\n### erros\nEtapa de entrevista invalida.\n"

    async def _generate_question(
        self,
        profile: str,
        interview_context: str,
    ) -> AsyncGenerator[str, None]:
        prompt = f"""Gere a primeira pergunta da entrevista simulada.

Contexto da vaga:
{interview_context}

Perfil do candidato:
{profile}

Requisitos:
1. A pergunta deve ser adequada ao nivel do candidato.
2. A pergunta deve conectar experiencia/projeto com a vaga alvo.
3. Gere apenas uma pergunta.

Retorne exatamente:
## RESPOSTA: COACH
### estado
sucesso

### pergunta_atual
[texto da pergunta 1]
"""
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
        prev_step = step - 1
        prompt = f"""Avalie a resposta anterior e gere a proxima pergunta da entrevista simulada.

Contexto da vaga:
{interview_context}

Perfil do candidato:
{profile}

Historico:
{history_text}

Requisitos:
1. Avalie R{prev_step}; nao avalie outra resposta.
2. Use feedback curto com Acerto, Gap e Ajuste.
3. Gere apenas a Pergunta {step}.
4. Alterne o tipo de pergunta em relacao ao historico.

Retorne exatamente:
## RESPOSTA: COACH
### estado
sucesso

### feedback_anterior
Acerto: [ponto positivo]
Gap: [lacuna]
Ajuste: [orientacao objetiva]

### pergunta_atual
[texto da pergunta {step}]
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
        prompt = f"""Finalize a entrevista simulada.

Contexto da vaga:
{interview_context}

Perfil do candidato:
{profile}

Historico completo:
{history_text}

Requisitos:
1. Avalie R5.
2. Atribua pontuacao final de 1 a 10.
3. Liste 2 ou 3 areas criticas de melhoria.
4. Seja especifico e acionavel.

Retorne exatamente:
## RESPOSTA: COACH
### estado
sucesso

### feedback_anterior
Acerto: [ponto positivo]
Gap: [lacuna]
Ajuste: [orientacao final]

### pontuacao_final
[X]/10

### areas_de_melhoria
1. [area critica]
2. [area critica]
3. [area critica]
"""
        async for token in self.stream_llm(COACH_SYSTEM_PROMPT, prompt):
            yield token
        yield "\n"
