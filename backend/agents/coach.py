"""
Agente Coach - simulacao de entrevistas.

Fluxo:
1. Despacho 1: gera P1.
2. Despachos 2-5: avalia resposta anterior e gera proxima pergunta.
3. Despacho 6: avalia R5, pontua e entrega areas de melhoria.
"""

from __future__ import annotations

import re
from typing import AsyncGenerator

from agents.base import BaseAgent, LLMProviderError


COACH_SYSTEM_PROMPT = """Voce e o Coach, agente especializado em entrevistas simuladas do sistema Recoloca IA.

Regras:
1. Nunca use tabelas markdown.
2. Responda no formato exato pedido pelo usuario.
3. Nao invente experiencias do candidato.
4. Calibre dificuldade por senioridade.
5. Siga exatamente o tipo de pergunta solicitado para cada etapa.
6. Feedback deve ser curto e especifico, com Acerto, Gap e Ajuste.
7. Para respostas comportamentais, avalie STAR: Situacao, Tarefa, Acao e Resultado.
8. Para respostas tecnicas, avalie clareza, exemplos, tradeoffs e riscos.
9. Nao invente experiencias, empresas, projetos ou resultados do candidato.
10. Se a resposta vier vazia, vaga ou "nao sei", oriente com STAR, CAR ou uma estrutura tecnica simples.
"""


QUESTION_PLAN = {
    1: ("comportamental", "trajetoria, motivacao e aderencia ao objetivo de carreira"),
    2: ("tecnica", "habilidades atuais, requisitos recorrentes e lacunas do Scout"),
    3: ("comportamental", "colaboracao, comunicacao, lideranca ou tomada de decisao"),
    4: ("tecnica", "cenario pratico ligado as vagas compativeis"),
    5: ("estrategica", "priorizacao de carreira, aprendizado e proximos passos"),
}


class CoachAgent(BaseAgent):
    """Agente de simulacao de entrevistas."""

    name = "Coach"

    def _normalize_key(self, value: str) -> str:
        normalized = value.casefold().replace("ã", "a").replace("õ", "o").replace("ç", "c")
        normalized = normalized.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        normalized = normalized.replace("â", "a").replace("ê", "e").replace("ô", "o")
        return normalized.strip()

    def _parse_profile(self, profile_text: str) -> dict[str, str]:
        data: dict[str, str] = {}
        for line in profile_text.splitlines():
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            data[self._normalize_key(key)] = value.strip()
        return data

    def _profile_value(self, profile: dict[str, str], *keys: str, default: str = "nao informado") -> str:
        for key in keys:
            value = profile.get(self._normalize_key(key))
            if value:
                return value
        return default

    def _is_profile_complete(self, profile_text: str) -> bool:
        if not profile_text.strip():
            return False
        profile = self._parse_profile(profile_text)
        completion = self._profile_value(profile, "Concluido", "Concluído", default="")
        has_minimum_fields = any("area de interesse" in key for key in profile)
        return has_minimum_fields and completion.casefold().strip() == "true"

    def _extract_list_values(self, text: str, field: str) -> list[str]:
        values: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.casefold().startswith(field.casefold()):
                continue
            raw = stripped.split(":", 1)[1] if ":" in stripped else ""
            for item in re.split(r"[,;]", raw):
                clean = item.strip().strip("[]")
                if clean and clean.casefold() not in {"nenhuma", "nao informado", "não informado"}:
                    values.append(clean)
        return values

    def _extract_recurring_requirements(self, job_results: str) -> list[str]:
        requirements: list[str] = []
        for line in job_results.splitlines():
            stripped = line.strip()
            if "requisito:" in stripped.casefold():
                value = stripped.split(":", 1)[1].strip()
                if value:
                    requirements.append(value)
        return requirements

    def _extract_job_titles(self, job_results: str) -> list[str]:
        titles: list[str] = []
        for line in job_results.splitlines():
            stripped = line.strip()
            if "titulo:" in stripped.casefold():
                title = stripped.split(":", 1)[1].strip()
                if title and title not in titles:
                    titles.append(title)
        return titles

    def _extract_learning_focus(self, course_recommendations: str) -> list[str]:
        focus: list[str] = []
        for line in course_recommendations.splitlines():
            stripped = line.strip()
            if "habilidade:" in stripped.casefold():
                skill = stripped.split(":", 1)[1].strip()
                if skill and skill not in focus:
                    focus.append(skill)
        return focus[:5]

    def _build_interview_brief(
        self,
        profile_text: str,
        job_results: str,
        course_recommendations: str,
        interview_context: str,
    ) -> str:
        profile = self._parse_profile(profile_text)
        area = self._profile_value(profile, "Area de interesse", "Área de interesse")
        level = self._profile_value(profile, "Nivel de experiencia", "Nível de experiência")
        target_roles = self._profile_value(profile, "Funcoes alvo", "Funções alvo")
        current_skills = self._profile_value(profile, "Habilidades atuais", "Skills atuais")
        career_goal = self._profile_value(profile, "Objetivo de carreira", "Objetivo")
        work_prefs = self._profile_value(profile, "Preferencias de trabalho", "Preferências de trabalho")

        missing_skills = self._extract_list_values(job_results, "habilidades_faltantes")[:8]
        recurring_requirements = self._extract_recurring_requirements(job_results)[:8]
        compatible_jobs = self._extract_job_titles(job_results)[:5]
        learning_focus = self._extract_learning_focus(course_recommendations)

        course_status = (
            "Trilha do Curator disponivel."
            if course_recommendations.strip()
            else "Trilha do Curator ausente; preparar entrevista com base em perfil e Scout."
        )

        return "\n".join(
            [
                f"Contexto da entrevista: {interview_context or 'Posicao baseada no perfil'}",
                f"Area de interesse: {area}",
                f"Nivel de experiencia: {level}",
                f"Funcoes alvo: {target_roles}",
                f"Objetivo de carreira: {career_goal}",
                f"Preferencias de trabalho: {work_prefs}",
                f"Habilidades atuais declaradas: {current_skills}",
                f"Vagas compativeis do Scout: {', '.join(compatible_jobs) if compatible_jobs else 'nao informado'}",
                f"Habilidades faltantes: {', '.join(missing_skills) if missing_skills else 'nao informado'}",
                f"Requisitos recorrentes: {', '.join(recurring_requirements) if recurring_requirements else 'nao informado'}",
                f"Focos da trilha de evolucao: {', '.join(learning_focus) if learning_focus else 'nao informado'}",
                f"Status da preparacao: {course_status}",
            ]
        )

    def _read_context_file(self, path) -> str:
        return self._read_file(path)

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

    def _brief_value(self, interview_brief: str, label: str, default: str = "nao informado") -> str:
        prefix = f"{label}:"
        for line in interview_brief.splitlines():
            if line.casefold().startswith(prefix.casefold()):
                value = line.split(":", 1)[1].strip()
                return value or default
        return default

    def _question_for_step(self, step: int, interview_brief: str) -> str:
        area = self._brief_value(interview_brief, "Area de interesse")
        target_roles = self._brief_value(interview_brief, "Funcoes alvo")
        career_goal = self._brief_value(interview_brief, "Objetivo de carreira")
        current_skills = self._brief_value(interview_brief, "Habilidades atuais declaradas")
        missing_skills = self._brief_value(interview_brief, "Habilidades faltantes")
        requirements = self._brief_value(interview_brief, "Requisitos recorrentes")
        jobs = self._brief_value(interview_brief, "Vagas compativeis do Scout")

        if step == 1:
            return (
                f"Para uma oportunidade em {area}, mirando {target_roles}, conte como sua trajetoria ate aqui "
                f"se conecta ao objetivo de carreira '{career_goal}'. Use uma situacao real, o que voce fez "
                "e qual resultado ou aprendizado conseguiu gerar."
            )
        if step == 2:
            return (
                f"Considerando suas habilidades atuais ({current_skills}) e os requisitos recorrentes ({requirements}), "
                "explique como voce resolveria um problema tecnico comum dessa funcao. Deixe claro seu raciocinio, "
                "ferramentas usadas e principais tradeoffs."
            )
        if step == 3:
            return (
                "Descreva uma situacao em que voce precisou alinhar expectativas, comunicar uma decisao tecnica "
                "ou lidar com conflito em equipe. Qual era o contexto, que acao voce tomou e qual foi o resultado?"
            )
        if step == 4:
            return (
                f"As oportunidades mapeadas incluem {jobs}. Escolha uma lacuna relevante ({missing_skills}) e explique "
                "como voce se prepararia para aplicar essa habilidade em um projeto real nos proximos 30 dias."
            )
        return (
            f"Olhando para seu objetivo ({career_goal}) e para as lacunas mapeadas ({missing_skills}), quais seriam "
            "suas prioridades de evolucao antes de se candidatar e como voce mediria progresso?"
        )

    def _fallback_first_question(
        self,
        interview_brief: str,
        has_course_recommendations: bool,
        error: Exception,
    ) -> str:
        question_type, question_focus = QUESTION_PLAN[1]
        preparation = (
            "Use tambem a trilha do Curator para conectar resposta, lacunas e plano de evolucao."
            if has_course_recommendations
            else "Como a trilha do Curator nao foi encontrada, responda com base no perfil e nas oportunidades do Scout."
        )
        return f"""## RESPOSTA: COACH
### estado
sucesso

### resumo
Entrevista simulada direcionada iniciada com fallback local porque o LLM ficou indisponivel. Pergunta 1 de 5, tipo {question_type}.

### dados
tipo_pergunta: {question_type}
foco_pergunta: {question_focus}
instrucao_resposta: Responda em 3 partes: contexto, acao e resultado. Se nao souber responder, diga o que voce faria e quais evidencias buscaria.
preparacao: {preparation}

### pergunta_atual
{self._question_for_step(1, interview_brief)}

### erros
LLM indisponivel durante a geracao da pergunta inicial ({type(error).__name__}). Usei uma pergunta local baseada no perfil, Scout e Curator.
"""

    def _last_user_answer(self, history_text: str, step: int) -> str:
        pattern = rf"R{step}:\s*(.*?)(?=\n(?:P|R|Feedback)\d+:|\Z)"
        match = re.search(pattern, history_text, flags=re.DOTALL)
        return match.group(1).strip() if match else ""

    def _fallback_evaluate_and_ask(
        self,
        step: int,
        interview_brief: str,
        history_text: str,
        error: Exception,
    ) -> str:
        prev_step = step - 1
        previous_type = QUESTION_PLAN[prev_step][0]
        question_type, question_focus = QUESTION_PLAN[step]
        answer = self._last_user_answer(history_text, prev_step)
        if answer:
            acerto = "Voce trouxe uma resposta aproveitavel para continuar a simulacao."
            gap = "Faltou explicitar contexto, acao e impacto com mais objetividade."
            ajuste = "Reestruture a resposta em contexto, decisao, execucao e resultado."
            score = "6/10"
        else:
            acerto = "Voce sinalizou uma lacuna com honestidade, o que ajuda a preparar melhor a resposta."
            gap = "A resposta ainda nao trouxe exemplo, raciocinio ou evidencia."
            ajuste = "Use STAR: Situacao, Tarefa, Acao e Resultado. Se nao tiver experiencia real, descreva como conduziria o caso."
            score = "4/10"

        return f"""## RESPOSTA: COACH
### estado
sucesso

### resumo
Resposta {prev_step} avaliada com fallback local. Proxima pergunta: {step} de 5, tipo {question_type}.

### dados
tipo_pergunta_anterior: {previous_type}
tipo_proxima_pergunta: {question_type}
instrucao_resposta: Para a proxima resposta, seja especifico e conecte sua acao ao impacto esperado na vaga.

### feedback_anterior
Acerto: {acerto}
Gap: {gap}
Ajuste: {ajuste}

### pontos_fortes
1. Continuidade na simulacao e disposicao para estruturar melhor a resposta.

### pontos_a_melhorar
1. Trazer exemplo, decisao tomada, tradeoffs e resultado esperado.

### resposta_melhorada
Em uma situacao relacionada a vaga, eu partiria do contexto, explicaria minha responsabilidade, mostraria a acao tomada e fecharia com resultado, aprendizado ou metrica observavel.

### nota_parcial
{score}

### pergunta_atual
{self._question_for_step(step, interview_brief)}

### erros
LLM indisponivel durante avaliacao/pergunta ({type(error).__name__}). Usei avaliacao local para nao interromper a entrevista.
"""

    def _fallback_final_evaluation(self, interview_brief: str, history_text: str, error: Exception) -> str:
        answered = len(re.findall(r"\n?R\d+:", history_text))
        return f"""## RESPOSTA: COACH
### estado
sucesso

### resumo
Entrevista simulada concluida com fallback local. Avaliacao final baseada nas respostas registradas.

### dados
perguntas_respondidas: {answered}

### feedback_anterior
Acerto: Voce concluiu a simulacao e gerou material suficiente para revisar sua preparacao.
Gap: As respostas precisam ficar mais especificas, com exemplos e impacto mensuravel.
Ajuste: Reescreva as respostas usando STAR para comportamentais e problema-solucao-tradeoff-impacto para tecnicas.

### pontuacao_final
6/10

### resumo_desempenho
Boa base para treino, mas ainda ha oportunidade de tornar as respostas mais concretas e conectadas as vagas mapeadas.

### pontos_fortes
1. Conclusao da simulacao.
2. Direcionamento para a esteira de carreira e oportunidades do Scout.

### pontos_de_melhoria
1. Usar exemplos mais objetivos.
2. Conectar habilidades faltantes a um plano pratico de evolucao.

### areas_de_melhoria
1. Estrutura das respostas.
2. Evidencias tecnicas.
3. Clareza sobre impacto profissional.

### plano_preparacao
1. Reescrever as respostas comportamentais em STAR.
2. Preparar 2 exemplos tecnicos ligados as lacunas do Scout.
3. Revisar a trilha do Curator e escolher um projeto pratico para demonstrar evolucao.

### proximos_passos
1. Rodar novamente a simulacao depois de revisar as respostas.
2. Atualizar o curriculo com evidencias dos projetos praticos.

### erros
LLM indisponivel durante avaliacao final ({type(error).__name__}). Usei avaliacao local para nao interromper a entrevista.
"""

    async def run(self, context: dict) -> AsyncGenerator[str, None]:
        step = int(context.get("step", 1))
        profile = context.get("profile", "") or self._read_context_file(self.paths.PROFILE_FILE)
        job_results = context.get("job_results", "") or self._read_context_file(self.paths.JOB_RESULTS_FILE)
        course_recommendations = context.get("course_recommendations", "") or self._read_context_file(self.paths.COURSE_RECS_FILE)
        interview_context = context.get("interview_context", "")
        history = context.get("history", [])
        history_text = self._format_history(history)
        interview_brief = self._build_interview_brief(profile, job_results, course_recommendations, interview_context)

        if not self._is_profile_complete(profile):
            yield "## RESPOSTA: COACH\n### estado\nerro\n\n### resumo\nPerfil incompleto.\n\n### dados\n\n### erros\nConclua o diagnostico antes de iniciar a entrevista simulada.\n"
            return

        if not job_results.strip() or "habilidades_faltantes" not in job_results:
            yield "## RESPOSTA: COACH\n### estado\nerro\n\n### resumo\nAinda nao ha resultados do Scout para direcionar a entrevista.\n\n### dados\n\n### erros\nRode a opcao A primeiro para gerar oportunidades, lacunas e requisitos recorrentes.\n"
            return

        if step == 1:
            async for token in self._generate_question(interview_brief, bool(course_recommendations.strip())):
                yield token
        elif 2 <= step <= 5:
            async for token in self._evaluate_and_ask(step, interview_brief, history_text):
                yield token
        elif step == 6:
            async for token in self._final_evaluation(interview_brief, history_text):
                yield token
        else:
            yield "## RESPOSTA: COACH\n### estado\nerro\n\n### resumo\nEtapa invalida.\n\n### dados\n\n### erros\nEtapa de entrevista invalida.\n"

    async def _generate_question(
        self,
        interview_brief: str,
        has_course_recommendations: bool,
    ) -> AsyncGenerator[str, None]:
        question_type, question_focus = QUESTION_PLAN[1]
        preparation_note = (
            "Use tambem a trilha do Curator para calibrar a preparacao."
            if has_course_recommendations
            else "Avise de forma discreta que a entrevista seguira sem a trilha do Curator, entao a preparacao fica menos completa."
        )
        prompt = f"""Inicie uma entrevista simulada direcionada com 5 perguntas no total.

Brief da esteira de carreira:
{interview_brief}

Pergunta atual:
- numero: 1 de 5
- tipo: {question_type}
- foco: {question_focus}

Requisitos:
1. Gere uma pergunta acolhedora, objetiva e profissional.
2. Conecte a pergunta ao objetivo, funcoes alvo, vagas do Scout e lacunas quando fizer sentido.
3. Nao invente experiencia profissional do candidato.
4. {preparation_note}

Retorne exatamente:
## RESPOSTA: COACH
### estado
sucesso

### resumo
Entrevista simulada direcionada iniciada. Pergunta 1 de 5, tipo {question_type}.

### dados
tipo_pergunta: {question_type}
foco_pergunta: {question_focus}
instrucao_resposta: Responda em 3 partes: contexto, acao e resultado. Se nao tiver um exemplo real, explique como conduziria a situacao.

### pergunta_atual
[texto da pergunta 1]

### erros
Nenhum erro.
"""
        try:
            async for token in self.stream_llm(COACH_SYSTEM_PROMPT, prompt):
                yield token
        except LLMProviderError as exc:
            yield self._fallback_first_question(interview_brief, has_course_recommendations, exc)
        yield "\n"

    async def _evaluate_and_ask(
        self,
        step: int,
        interview_brief: str,
        history_text: str,
    ) -> AsyncGenerator[str, None]:
        prev_step = step - 1
        previous_type = QUESTION_PLAN[prev_step][0]
        question_type, question_focus = QUESTION_PLAN[step]
        prompt = f"""Avalie a resposta anterior e gere a proxima pergunta da entrevista simulada.

Brief da esteira de carreira:
{interview_brief}

Historico:
{history_text}

Requisitos:
1. Avalie R{prev_step}; nao avalie outra resposta.
2. A pergunta anterior era do tipo {previous_type}; use o criterio adequado para avaliar.
3. Retorne feedback claro, pontos fortes, pontos a melhorar, resposta melhorada e nota parcial de 0 a 10.
4. Gere apenas a Pergunta {step}, do tipo {question_type}, com foco em {question_focus}.
5. Se R{prev_step} estiver vazia, vaga ou disser que nao sabe, oriente com estrutura STAR para comportamental ou uma estrutura de raciocinio tecnico para tecnica.
6. Nao invente exemplos, metricas ou experiencia do candidato.

Retorne exatamente:
## RESPOSTA: COACH
### estado
sucesso

### resumo
Resposta {prev_step} avaliada. Proxima pergunta: {step} de 5, tipo {question_type}.

### dados
tipo_pergunta_anterior: {previous_type}
tipo_proxima_pergunta: {question_type}
instrucao_resposta: Responda com exemplo ou raciocinio estruturado, conectando sua decisao ao impacto esperado na vaga.

### feedback_anterior
Acerto: [ponto positivo]
Gap: [lacuna]
Ajuste: [orientacao objetiva]

### pontos_fortes
1. [ponto forte]

### pontos_a_melhorar
1. [ponto a melhorar]

### resposta_melhorada
[sugestao objetiva de resposta melhorada, sem inventar fatos; use placeholders como "em um projeto..." quando necessario]

### nota_parcial
[0-10]/10

### pergunta_atual
[texto da pergunta {step}]

### erros
Nenhum erro.
"""
        try:
            async for token in self.stream_llm(COACH_SYSTEM_PROMPT, prompt):
                yield token
        except LLMProviderError as exc:
            yield self._fallback_evaluate_and_ask(step, interview_brief, history_text, exc)
        yield "\n"

    async def _final_evaluation(
        self,
        interview_brief: str,
        history_text: str,
    ) -> AsyncGenerator[str, None]:
        prompt = f"""Finalize a entrevista simulada.

Brief da esteira de carreira:
{interview_brief}

Historico completo:
{history_text}

Requisitos:
1. Avalie R5.
2. Atribua nota final de 0 a 10 considerando clareza, aderencia ao perfil, tecnica, exemplos e maturidade profissional.
3. Entregue resumo de desempenho, pontos fortes, pontos de melhoria, plano de preparacao e proximos passos.
4. Seja especifico e acionavel.
5. Nao invente experiencia, metricas ou resultados do candidato.

Retorne exatamente:
## RESPOSTA: COACH
### estado
sucesso

### resumo
Entrevista simulada concluida. Avaliacao final baseada nas 5 respostas.

### dados
perguntas_respondidas: 5

### feedback_anterior
Acerto: [ponto positivo]
Gap: [lacuna]
Ajuste: [orientacao final]

### pontuacao_final
[X]/10

### resumo_desempenho
[resumo objetivo]

### pontos_fortes
1. [ponto forte]
2. [ponto forte]

### pontos_de_melhoria
1. [ponto de melhoria]
2. [ponto de melhoria]

### areas_de_melhoria
1. [area critica]
2. [area critica]
3. [area critica]

### plano_preparacao
1. [acao pratica antes da proxima entrevista]
2. [acao pratica antes da proxima entrevista]
3. [acao pratica antes da proxima entrevista]

### proximos_passos
1. [proximo passo]
2. [proximo passo]

### erros
Nenhum erro.
"""
        try:
            async for token in self.stream_llm(COACH_SYSTEM_PROMPT, prompt):
                yield token
        except LLMProviderError as exc:
            yield self._fallback_final_evaluation(interview_brief, history_text, exc)
        yield "\n"
