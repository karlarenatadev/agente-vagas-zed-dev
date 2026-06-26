# Protocolo de Despacho e Handoff de Agentes

## Propósito

Esta skill define a lógica de roteamento para o Maestro despachar sub-agentes via `spawn_agent`. Ela especifica o formato do envelope de handoff, formato do envelope de resposta, regras de roteamento e contextos de despacho por agente.

## Tabela de Roteamento

O Maestro roteia as seleções de menu do usuário para agentes da seguinte forma:

1. **Entrada do usuário A** → despacha **Scout** (busca de vagas)
2. **Entrada do usuário B** → despacha **Curator** (busca de cursos)
3. **Entrada do usuário C** → despacha **Coach** (simulação de entrevista) — despachado 6 vezes sequencialmente; quando há vaga analisada e relatório de aderência, as perguntas são calibradas pela vaga e pelas lacunas do match
4. **Entrada do usuário D** → Maestro lida com refazer o diagnóstico internamente (sem despacho)

A **Esteira de Candidatura** (E–I) é orquestrada pelo próprio Maestro, que lê e escreve os artefatos em `data/` (sem `spawn_agent`):

5. **Entrada do usuário E** → análise da descrição de vaga colada → `data/job-description-analysis.md`
6. **Entrada do usuário F** → comparação vaga × currículo (Match) → `data/resume-match-report.md`
7. **Entrada do usuário G** → sugestões seguras de currículo (Tailor) → `data/resume-tailoring-suggestions.md`
8. **Entrada do usuário H** → geração de PDI de 7/30/60 dias → `data/pdi-plan.md`
9. **Entrada do usuário I** → reconciliação perfil × currículo × vaga, definindo o foco da candidatura → `data/reconciliation.md`

## Envelope de Despacho

O Maestro constrói um prompt para cada chamada `spawn_agent` usando esta estrutura exata:

```
## DESPACHO: [NOME_DO_AGENTE]
### referencia_persona
[Conteúdo completo de personas/<nome_do_agente_minusculo>.md — o agente despachado DEVE ler e adotar esta persona antes de executar a tarefa]

### tarefa
[Uma frase descrevendo o que o agente deve fazer]

### perfil_usuario
[Conteúdo de data/user-profile.md]

### contexto
[Contexto específico: ex: qual vaga para entrevistar, quais habilidades para buscar cursos]

### saida_esperada
[Exatamente qual formato o agente deve retornar]
```

Cada seção é obrigatória. Nenhuma seção pode ser omitida ou deixada vazia. **Exceção**: No despacho sequencial do Coach (despachos 2-6), omita a seção `referencia_persona` para economizar tokens.

**Crítico**: A seção `referencia_persona` DEVE conter o conteúdo completo do arquivo de persona do agente (ex: `personas/scout.md`, `personas/curator.md`, `personas/coach.md`). Isso garante que o agente despachado obedeça a todas as regras comportamentais, proibições de ferramentas, fluxos de trabalho e regras de formato de saída definidas em sua persona. O Maestro deve ler o arquivo de persona e incorporar todo o seu conteúdo no prompt de despacho.

## Envelope de Resposta

Todo agente despachado deve retornar uma resposta neste formato. O Maestro analisa e exibe a resposta para o usuário.

```
## RESPOSTA: [NOME_DO_AGENTE]
### estado
[sucesso | erro]

### resumo
[Resumo legível de 2-3 frases para o usuário]

### dados
[Resultados como listas numeradas com pares chave-valor. Sem tabelas markdown.]

### erros
[Somente se estado for erro: o que deu errado]
```

O Maestro lê o campo `estado`:
- Se `sucesso`: exibe `resumo` e `dados` para o usuário
- Se `erro`: exibe `erros` para o usuário e retorna ao menu

## Handoff do Scout

### Quando Despachado

Usuário seleciona a opção A do menu (Buscar vagas de emprego).

### Descrição da Tarefa

"Buscar vagas de emprego correspondentes à área de interesse e localização do usuário, realizar correspondência de habilidades contra as habilidades atuais do usuário e retornar até 5 resultados de vagas."

### Contexto Passado

O conteúdo de `data/user-profile.md` fornece:
- `Área de interesse`
- `Localização`
- `Nível de experiência`
- `Habilidades atuais`
- `Soft skills`
- `Objetivo de carreira`

O Maestro insere esses valores na seção `contexto` do Envelope de Despacho.

### Referência do Arquivo de Skill do Scout

O Scout usa a skill definida em `skills/job-search.md` para o fluxo de busca completo incluindo comandos firecrawl, lógica de correspondência de habilidades e formatação de resultados.

### Formato de Saída Esperado

O Scout retorna resultados de emprego como entradas numeradas com pares chave-valor:

```
1. titulo: [título da vaga]
   empresa: [nome da empresa]
   localizacao: [cidade ou Remoto]
   link: [URL]
   habilidades_correspondentes: [habilidade1, habilidade2]
   habilidades_faltantes: [habilidade3, habilidade4]
   contagem_correspondencia: [X de Y habilidades correspondem]

2. titulo: [próximo título de vaga]
   empresa: [próxima empresa]
   localizacao: [cidade ou Remoto]
   link: [URL]
   habilidades_correspondentes: [habilidade1]
   habilidades_faltantes: [habilidade2, habilidade3, habilidade4]
   contagem_correspondencia: [1 de 4 habilidades correspondem]
```

### Pós-Despacho

Após o Scout retornar com sucesso:
1. O Maestro escreve os resultados em `data/job-search-results.md`
2. O Maestro exibe o resumo e os dados para o usuário
3. O Maestro mostra o menu novamente

Se o Scout retornar um erro:
1. O Maestro exibe o erro para o usuário
2. O Maestro mostra o menu novamente

## Handoff do Curator

### Quando Despachado

Usuário seleciona a opção B do menu (Encontrar cursos para preencher lacunas de habilidades).

### Descrição da Tarefa

"Buscar na Alura cursos que abordem as lacunas de habilidades identificadas nos resultados de busca de vagas e retornar uma lista curada e ordenada de recomendações de cursos."

### Validação de Pré-requisito

Antes de despachar o Curator, o Maestro deve verificar se `data/job-search-results.md` existe e contém dados de `habilidades_faltantes`.

Se o arquivo não existir ou não tiver habilidades faltantes:
- O Maestro NÃO despacha o Curator
- O Maestro exibe um erro: "Nenhuma lacuna de habilidade encontrada. Por favor, busque vagas primeiro (opção A do menu) para identificar quais habilidades você precisa desenvolver."
- O Maestro mostra o menu novamente

### Contexto Passado

O Maestro lê `data/job-search-results.md` e extrai todos os valores únicos de cada campo `habilidades_faltantes` em todos os resultados de vagas. O Maestro desduplica esta lista e a passa para a seção `contexto` do Envelope de Despacho.

O Maestro também passa a `Área de interesse` do usuário de `data/user-profile.md`.

### Referência do Arquivo de Skill

O Curator usa a skill definida em `skills/course-analysis.md` para o fluxo de busca de cursos completo incluindo comandos firecrawl, seleção de cursos, classificação de nível e formatação de resultados.

### Formato de Saída Esperado

O Curator retorna resultados de curso como entradas numeradas com pares chave-valor:

```
1. nome_curso: [título do curso]
   duracao: [ex: 20 horas]
   nivel: [iniciante | intermediario | avancado]
   aborda_habilidade: [nome da habilidade]
   link: [URL]

2. nome_curso: [próximo título do curso]
   duracao: [ex: 12h30]
   nivel: [iniciante | intermediario | avancado]
   aborda_habilidade: [nome da habilidade]
   link: [URL]

Ordem sugerida:
1. [nome do curso]
2. [nome do curso]
3. [nome do curso]
```

### Pós-Despacho

Após o Curator retornar com sucesso:
1. O Maestro escreve os resultados em `data/course-recommendations.md`
2. O Maestro exibe o resumo e os dados para o usuário
3. O Maestro mostra o menu novamente

Se o Curator retornar um erro:
1. O Maestro exibe o erro para o usuário
2. O Maestro mostra o menu novamente

## Despacho Sequencial do Coach

### Quando Despachado

Usuário seleciona a opção C do menu (Praticar com uma entrevista simulada).

### Descrição da Tarefa

O Coach é despachado exatamente 6 vezes em sequência. Cada despacho constrói sobre o anterior para conduzir uma entrevista simulada estruturada de 5 perguntas, seguida por uma avaliação de pontuação final.

**Otimização de tokens**: Inclua a seção `referencia_persona` com o conteúdo completo de `personas/coach.md` apenas no Despacho 1. Nos despachos 2-6, omita `referencia_persona` e envie apenas `tarefa`, `perfil_usuario`, `contexto` e `saida_esperada`. O Coach já conhece sua persona a partir do primeiro despacho.

### Referência do Arquivo de Skill

O Coach usa a skill definida em `skills/interview-sim.md` para geração de perguntas, avaliação, feedback e lógica de pontuação.

### Resolução do Contexto da Vaga

Antes de despachar o Coach pela primeira vez, o Maestro resolve o contexto da vaga:
1. Se `data/job-search-results.md` existir e conter resultados de vagas, o Maestro usa o título e descrição da primeira vaga (ou selecionada pelo usuário)
2. Se nenhuma busca de vagas foi realizada, o Maestro usa as `Funções alvo` de `data/user-profile.md` como contexto da entrevista. O Coach informará ao usuário que as perguntas serão gerais, baseadas no perfil.

### Despacho 1 — Gerar Pergunta 1

- **Tarefa**: Gerar a primeira pergunta de entrevista (comportamental ou técnica) com base no contexto da vaga e perfil do usuário
- **Contexto**: Título da vaga, descrição da vaga (se disponível) e perfil do usuário de `data/user-profile.md`
- **Perguntas e Respostas Anteriores**: Nenhum
- **Saída esperada**: Coach gera Pergunta 1 e a retorna no formato de resposta por despacho
- **Ação do Maestro**: Registrar P1 em `data/interview-session.md`, exibir P1 para o usuário, aguardar resposta R1

### Despacho 2 — Avaliar R1, Gerar Pergunta 2

- **Tarefa**: Avaliar a resposta do usuário à Pergunta 1, fornecer feedback e gerar Pergunta 2
- **Contexto**: Mesmo título da vaga, descrição da vaga (se disponível)
- **Perguntas e Respostas Anteriores**: P1 e R1
- **Saída esperada**: Coach avalia R1, retorna feedback e gera Pergunta 2 no formato de resposta por despacho
- **Ação do Maestro**: Registrar R1 e P2 em `data/interview-session.md`, exibir feedback e P2 para o usuário, aguardar resposta R2

### Despacho 3 — Avaliar R2, Gerar Pergunta 3

- **Tarefa**: Avaliar a resposta do usuário à Pergunta 2, fornecer feedback e gerar Pergunta 3
- **Contexto**: Mesmo título da vaga, descrição da vaga (se disponível)
- **Perguntas e Respostas Anteriores**: P1/R1 e P2/R2
- **Saída esperada**: Coach avalia R2, retorna feedback e gera Pergunta 3 no formato de resposta por despacho
- **Ação do Maestro**: Registrar R2 e P3 em `data/interview-session.md`, exibir feedback e P3 para o usuário, aguardar resposta R3

### Despacho 4 — Avaliar R3, Gerar Pergunta 4

- **Tarefa**: Avaliar a resposta do usuário à Pergunta 3, fornecer feedback e gerar Pergunta 4
- **Contexto**: Mesmo título da vaga, descrição da vaga (se disponível)
- **Perguntas e Respostas Anteriores**: P1/R1 até P3/R3
- **Saída esperada**: Coach avalia R3, retorna feedback e gera Pergunta 4 no formato de resposta por despacho
- **Ação do Maestro**: Registrar R3 e P4 em `data/interview-session.md`, exibir feedback e P4 para o usuário, aguardar resposta R4

### Despacho 5 — Avaliar R4, Gerar Pergunta 5

- **Tarefa**: Avaliar a resposta do usuário à Pergunta 4, fornecer feedback e gerar Pergunta 5
- **Contexto**: Mesmo título da vaga, descrição da vaga (se disponível)
- **Perguntas e Respostas Anteriores**: P1/R1 até P4/R4
- **Saída esperada**: Coach avalia R4, retorna feedback e gera Pergunta 5 no formato de resposta por despacho
- **Ação do Maestro**: Registrar R4 e P5 em `data/interview-session.md`, exibir feedback e P5 para o usuário, aguardar resposta R5

### Despacho 6 — Avaliar R5, Pontuação Final

- **Tarefa**: Avaliar a resposta do usuário à Pergunta 5, calcular a pontuação final da entrevista e fornecer áreas de melhoria
- **Contexto**: Mesmo título da vaga, descrição da vaga (se disponível)
- **Perguntas e Respostas Anteriores**: P1/R1 até P5/R5
- **Saída esperada**: Coach retorna a avaliação final com pontuação e áreas de melhoria
- **Ação do Maestro**: Registrar R5 e pontuação final em `data/interview-session.md`, exibir a pontuação final e áreas de melhoria para o usuário

### Formato de Resposta por Despacho (Despachos 1-5)

```
### estado: sucesso
### pergunta_atual: [texto da pergunta]
### feedback_anterior: [feedback sobre resposta anterior, ou vazio para pergunta 1]
```

### Formato de Resposta Final (Despacho 6)

```
### estado: sucesso
### Entrevista Concluída
Pontuação: [X/10]

### Áreas de melhoria
1. [área de melhoria 1]
2. [área de melhoria 2]
```

### Arquivo de Sessão de Entrevista

O Maestro mantém `data/interview-session.md` durante os 6 despachos:

```
Contexto da Vaga: [título da vaga e empresa]
Número da Pergunta: [1-5]
Histórico de Perguntas e Respostas:
  P1: [texto da pergunta]
  R1: [texto da resposta do usuário]
  P2: [texto da pergunta]
  R2: [texto da resposta do usuário]
  P3: [texto da pergunta]
  R3: [texto da resposta do usuário]
  P4: [texto da pergunta]
  R4: [texto da resposta do usuário]
  P5: [texto da pergunta]
  R5: [texto da resposta do usuário]

Pontuação Final: [X/10]
Áreas de Melhoria:
1. [área de melhoria 1]
2. [área de melhoria 2]
```

### Pós-Despacho

Após todos os 6 despachos serem completados:
1. O Maestro exibe a pontuação final e áreas de melhoria
2. O Maestro mostra o menu novamente

## Refazer Quiz (Opção D do Menu)

Usuário seleciona a opção D do menu (Refazer o quiz). O Maestro lida com isso internamente sem despacho:

1. Sobrescreva `data/personality-quiz.md` completamente com novas respostas (não delete — reescreva)
2. Gere um novo `data/user-profile.md` a partir das respostas
3. Delete `data/job-search-results.md` se existir
4. Delete `data/course-recommendations.md` se existir
5. Delete `data/interview-session.md` se existir
6. Execute o Fluxo do Quiz do zero (veja maestro.md)
7. Após a conclusão do quiz, apresente o menu novamente

## Regras de Tratamento de Erros

- Se `spawn_agent` falhar para qualquer despacho, o Maestro reporta o erro exato ao usuário e retorna ao menu
- Se um agente despachado retornar `estado: erro`, o Maestro exibe o campo `erros` e retorna ao menu
- Se a cadeia de despachos do Coach for interrompida em qualquer ponto (despachos 1-5), o Maestro exibe o motivo da interrupção e retorna ao menu. O arquivo de sessão de entrevista é preservado para que o usuário possa retomar depois se desejar
- O Maestro nunca continua silenciosamente em caso de erro. Todas as falhas são relatadas explicitamente
