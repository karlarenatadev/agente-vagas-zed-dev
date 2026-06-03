# Aula 4: Coach — Simulador de Entrevistas (Módulo de Simulação)

## Visão Geral
Este documento define o **Coach** (Opção C do menu), o agente responsável por conduzir simulações de entrevistas iterativas baseadas nos requisitos literais de uma vaga de tecnologia e no perfil do usuário.

## Diretrizes Estritas para Modelos MoE
- Comunicação limpa, silenciosa e objetiva de terminal. **Sem tabelas markdown**, apenas chave-valor[cite: 1, 2, 3, 4, 5, 6].
- O Maestro orquestra esta etapa enviando **6 despachos sequenciais** para o Coach não perder o contexto da conversa.

## Estrutura do Agente
- **Responsabilidade:** Conduzir 5 perguntas (misturando técnica e comportamental) adequadas ao nível de senioridade, dando feedback contínuo.
- **Skills:** `skills/interview-sim.md` (OBRIGATÓRIO).

## Fluxo de Execução Iterativo (`skills/interview-sim.md`)
1. **Despacho 1:** O Maestro envia a `referencia_persona`, a Vaga Alvo e manda o Coach gerar a **Pergunta 1** (P1)[cite: 5].
2. **Despachos 2 a 5:** O Maestro envia a resposta do usuário (R1... R4). O Coach avalia a resposta anterior (dando feedback em estilo *code review* rápido, apontando acertos e gaps) e gera a próxima pergunta[cite: 5]. As perguntas devem focar na stack da vaga (ex: estruturação de pipelines de dados, criação de dashboards, modelagem de banco).
3. **Despacho 6 (Final):** O Maestro envia a última resposta (R5). O Coach avalia R5, retorna uma pontuação final (1-10) e 2 a 3 áreas críticas de melhoria[cite: 5].

## Protocolos de Despacho (Exemplos)

**Despacho do Meio (Ex: Despacho 3):**
*Nota: A persona não é reenviada nos despachos subsequentes para economizar tokens[cite: 5].*
```text
## DESPACHO: COACH
### tarefa
Avaliar resposta anterior e gerar próxima pergunta.

### perfil_usuario
[Conteúdo de data/user-profile.md]

### contexto
Vaga: [título e descrição]
Número da pergunta: 3
Histórico:
  P1: [texto]
  R1: [texto]
  P2: [texto]
  R2: [texto da resposta atual do usuário]

### saida_esperada
Estado, feedback_anterior (sobre R2) e pergunta_atual (P3).
Despacho Final (Despacho 6):

Plaintext
## DESPACHO: COACH
### tarefa
Avaliar resposta final e dar pontuação da entrevista.

### contexto
[Histórico completo P1/R1 a P5/R5]

### saida_esperada
Estado, pontuação_final (X/10) e áreas_de_melhoria.
Esquema de Dados: data/interview-session.md
O Maestro deve criar e atualizar constantemente este arquivo durante a simulação.

Plaintext
Contexto da Vaga: [título e empresa da vaga escolhida]
Número da Pergunta: [1-5]
Histórico de Perguntas e Respostas:
  P1: [texto]
  R1: [texto]
  Feedback 1: [texto]
  P2: [texto]
  R2: [texto]
  ...
Pontuação Final: [X/10]
Áreas de Melhoria:
1. [item 1]
2. [item 2]
Tasks para o Codex
Escrever skills/interview-sim.md definindo a calibração de dificuldade (Júnior/Pleno/Sênior) e o tom do feedback.

Escrever personas/coach.md garantindo o formato de saída exato para cada etapa dos despachos iterativos.

Atualizar o Maestro para gerenciar o loop de 6 despachos sequenciais, atualizando data/interview-session.md a cada iteração do usuário.