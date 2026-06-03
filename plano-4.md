# Aula 4: Coach - Simulador de Entrevistas

## Visao Geral

Este documento define o Coach, agente acionado pela opcao C do menu. O Coach conduz uma entrevista simulada em 5 perguntas, usando o perfil do usuario e a vaga mais relevante disponivel.

O objetivo e ajudar a pessoa a treinar respostas com menos ansiedade e mais clareza. O feedback deve ser direto, especifico e acionavel, como uma revisao curta de performance.

## Dor do Usuario

1. A pessoa nao sabe quais perguntas esperar em entrevistas.
2. A pessoa tem dificuldade de transformar experiencia em resposta estruturada.
3. A pessoa precisa de feedback objetivo, sem julgamento vago.
4. A pessoa precisa praticar perguntas tecnicas e comportamentais ligadas a vaga.
5. A pessoa precisa sair com 2 ou 3 pontos claros de melhoria.

## Responsabilidade do Coach

1. Gerar 5 perguntas de entrevista.
2. Alternar perguntas tecnicas, comportamentais e situacionais.
3. Calibrar dificuldade por senioridade: junior, pleno ou senior.
4. Avaliar cada resposta anterior antes de perguntar a proxima.
5. Dar feedback curto com acertos, gaps e proximo ajuste.
6. Ao final, entregar pontuacao de 1 a 10 e areas criticas de melhoria.

## Fluxo de 6 Despachos

1. Despacho 1: gerar Pergunta 1.
2. Despacho 2: avaliar R1 e gerar Pergunta 2.
3. Despacho 3: avaliar R2 e gerar Pergunta 3.
4. Despacho 4: avaliar R3 e gerar Pergunta 4.
5. Despacho 5: avaliar R4 e gerar Pergunta 5.
6. Despacho 6: avaliar R5 e gerar pontuacao final.

## Estado Persistido

O Maestro deve criar e atualizar `data/interview-session.md` durante toda a simulacao.

Formato:

```text
Contexto da Vaga: [titulo e empresa ou funcao alvo]
Numero da Pergunta: [1-5]
Historico de Perguntas e Respostas:
  P1: [texto da pergunta]
  R1: [texto da resposta]
  Feedback 1: [texto do feedback]
  P2: [texto da pergunta]
  R2: [texto da resposta]
  Feedback 2: [texto do feedback]
  ...
  P5: [texto da pergunta]
  R5: [texto da resposta]
  Feedback 5: [texto do feedback]

Pontuacao Final: [X/10]
Areas de Melhoria:
1. [area]
2. [area]
3. [area]
```

## Envelope de Saida do Coach

### Pergunta inicial

```text
## RESPOSTA: COACH
### estado
sucesso

### pergunta_atual
[texto da pergunta 1]
```

### Perguntas intermediarias

```text
## RESPOSTA: COACH
### estado
sucesso

### feedback_anterior
Acerto: [ponto positivo]
Gap: [lacuna]
Ajuste: [como melhorar na proxima resposta]

### pergunta_atual
[texto da proxima pergunta]
```

### Resultado final

```text
## RESPOSTA: COACH
### estado
sucesso

### feedback_anterior
[feedback da resposta 5]

### pontuacao_final
[X]/10

### areas_de_melhoria
1. [area]
2. [area]
3. [area]
```

## Tasks da Aula 4

1. Escrever `skills/interview-sim.md` com calibragem por senioridade e tom do feedback.
2. Escrever `personas/coach.md` com formato exato de saida.
3. Atualizar o Coach para usar formato parseavel.
4. Atualizar o Maestro para gravar perguntas, respostas, feedbacks e pontuacao em `data/interview-session.md`.
5. Validar que a opcao C completa o ciclo e retorna ao menu.

## Criterios de Aceite

1. Ao escolher C, a entrevista inicia com uma vaga real quando houver `data/job-search-results.md`.
2. Se nao houver vaga, a entrevista usa `Funcoes alvo` do perfil.
3. Cada resposta do usuario e salva como `R[N]`.
4. Cada pergunta do Coach e salva como `P[N]`.
5. Feedbacks intermediarios sao salvos como `Feedback [N]`.
6. Ao final, `Pontuacao Final` e `Areas de Melhoria` sao salvas.
7. O Maestro retorna ao menu apos o despacho final.
