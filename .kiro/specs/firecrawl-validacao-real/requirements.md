# Requirements Document

## Introduction

Esta especificação cobre a validação do Firecrawl em condições reais (item P0 do
`checklist_prio.md`), recortada para a parte **automatizável e testável em código**.
A execução real consumindo créditos do Firecrawl permanece como um passo de
**validação manual guiada e reproduzível**, descrito em um requisito próprio com
critérios objetivos de aprovação.

O escopo concentra-se em quatro eixos:

1. **Origem dos dados (data provenance):** instrumentar e exibir de forma
   consistente, no Scout (vagas) e no Curator (cursos), a distinção entre dados
   reais do Firecrawl, sugestões de IA (LLM) e dados simulados, além do estado da
   busca (sucesso real, degradado, sem créditos, erro, timeout, vazio).
2. **Validação dos artefatos extraídos:** salários e requisitos das vagas (Scout)
   e atributos dos cursos (Curator), com normalização consistente e marcação
   explícita de "não informado" quando o dado estiver ausente.
3. **Normalização e abertura segura de links:** apenas URLs http(s) válidas de
   vagas reais podem ser clicáveis; sugestões de IA e dados simulados nunca podem
   aparecer como links clicáveis.
4. **Roteiro de validação manual reproduzível:** checklist executável com chave e
   créditos reais do Firecrawl, com critérios objetivos de aceite.

O comportamento descrito reflete o código já existente em
`backend/firecrawl_client.py`, `backend/agents/scout.py`,
`backend/agents/curator.py` e `frontend/src/components/ScoutReport.tsx`. A
normalização de links no `CuratorReport` é uma pendência P1 separada; pode ser
referenciada como contexto, mas não é o foco deste item P0.

## Glossary

- **Sistema:** o aplicativo Recoloca IA como um todo (backend e frontend).
- **Scout:** agente backend (`backend/agents/scout.py`) responsável pela busca de
  vagas e pela montagem dos `job_entry`.
- **Curator:** agente backend (`backend/agents/curator.py`) responsável por
  recomendar cursos e materiais de aprendizado.
- **Firecrawl_Client:** módulo `backend/firecrawl_client.py` que encapsula o SDK
  oficial `firecrawl-py` (`firecrawl_search`/`firecrawl_scrape`).
- **ScoutReport:** componente frontend (`frontend/src/components/ScoutReport.tsx`)
  que renderiza o resultado do Scout.
- **CuratorReport:** componente frontend que renderiza o resultado do Curator.
- **Origem do dado (source):** rótulo que classifica a procedência de uma vaga em
  `real` (dado verificado do Firecrawl), `llm` (sugestão gerada por IA, não
  verificada) ou `simulated` (dado determinístico gerado a partir do perfil).
- **Estado de busca (search_status):** classificação do resultado de uma busca de
  vagas do Scout, com os valores `real_success`, `real_empty`, `real_degraded`,
  `no_credits`, `external_error` e `timeout`.
- **Busca degradada:** situação em que a busca específica falhou (erro ou timeout)
  e apenas uma busca ampla recuperou vagas reais.
- **FirecrawlProviderError:** exceção de domínio para falhas controladas do
  Firecrawl.
- **FirecrawlCreditError:** subclasse de FirecrawlProviderError que sinaliza
  ausência de créditos/cota.
- **Link clicável:** elemento de interface que abre uma URL externa no navegador;
  neste documento, restrito a URLs http(s) válidas.
- **Não informado:** marcador textual padronizado usado quando um atributo
  esperado está ausente no dado de origem.
- **Roteiro de validação manual:** documento reproduzível (checklist) que orienta
  a execução real do Firecrawl com chave e créditos, com critérios de aceite.

## Requirements

### Requirement 1: Origem dos dados das vagas (Scout)

**User Story:** Como usuário que recebe resultados de busca de vagas, quero saber
claramente de onde cada vaga veio, para confiar nos dados reais e tratar
sugestões de IA ou dados simulados com o devido ceticismo.

#### Acceptance Criteria

1. WHEN o Scout monta uma entrada de vaga, THE Scout SHALL atribuir ao campo
   `source` exatamente um dos valores `real`, `llm` ou `simulated`.
2. WHEN o Scout obtém vagas reais do Firecrawl, THE Scout SHALL definir o campo
   `source` da vaga como `real`.
3. WHEN o Scout gera sugestões de vagas por meio do LLM, THE Scout SHALL definir o
   campo `source` da vaga como `llm`.
4. WHEN o Scout gera oportunidades simuladas a partir do perfil, THE Scout SHALL
   definir o campo `source` da vaga como `simulated`.
5. WHERE a origem de uma vaga é `llm` ou `simulated`, THE Scout SHALL preencher os
   campos `fallback_reason` e `fallback_message` com o motivo e a mensagem
   correspondentes.
6. WHERE a origem de uma vaga é `real`, THE Scout SHALL manter os campos
   `fallback_reason` e `fallback_message` vazios, sem adicionar campos de fallback.
7. WHEN o Scout emite o relatório de vagas, THE Scout SHALL incluir o campo
   `status_busca` com exatamente um dos valores `real_success`, `real_empty`,
   `real_degraded`, `no_credits`, `external_error` ou `timeout`.
8. IF qualquer entrada de vaga não possui o campo `source` definido com `real`,
   `llm` ou `simulated`, THEN THE Scout SHALL impedir a geração do relatório de
   vagas até que a origem do dado seja definida.

### Requirement 2: Classificação do estado de busca do Scout

**User Story:** Como usuário, quero entender se a busca de vagas teve sucesso
real, ficou degradada, ficou sem créditos, falhou ou expirou, para saber o quanto
confiar no resultado.

#### Acceptance Criteria

1. WHEN a busca específica retorna vagas reais do Firecrawl, THE Scout SHALL
   definir `status_busca` como `real_success`.
2. WHEN a busca específica falha por erro ou timeout e uma busca ampla recupera
   vagas reais, THE Scout SHALL definir `status_busca` como `real_degraded` e
   sinalizar `busca_degradada` como verdadeiro.
3. IF o Firecrawl sinaliza ausência de créditos por meio de FirecrawlCreditError,
   THEN THE Scout SHALL definir `status_busca` como `no_credits`.
4. IF a busca do Firecrawl falha por FirecrawlProviderError sem indicação de
   créditos, THEN THE Scout SHALL definir `status_busca` como `external_error`.
5. IF a busca do Firecrawl excede o tempo limite configurado, THEN THE Scout SHALL
   definir `status_busca` como `timeout`.
6. WHEN nenhuma vaga real é encontrada sem ocorrência de erro, timeout ou falta de
   créditos, THE Scout SHALL definir `status_busca` como `real_empty`.

### Requirement 3: Origem dos dados dos cursos (Curator)

**User Story:** Como usuário que recebe recomendações de cursos, quero distinguir
cursos obtidos de busca real de recomendações internas de fallback, para avaliar a
confiabilidade da trilha sugerida.

#### Acceptance Criteria

1. WHEN o Curator recebe resultados de cursos do Firecrawl, THE Curator SHALL
   marcar cada recurso resultante com origem real.
2. WHEN a busca de cursos do Firecrawl falha, THE Curator SHALL registrar o motivo
   da falha no campo `error` do SearchOutcome correspondente.
3. WHERE a busca externa de cursos não fornece cobertura suficiente para uma
   habilidade, THE Curator SHALL complementar a trilha com recursos da base
   interna INTERNAL_RECOMMENDATIONS e marcá-los como recomendação interna.
4. WHEN o Curator emite o relatório de cursos, THE Curator SHALL indicar a origem
   de cada recurso de forma que o usuário distinga curso de busca real de
   recomendação interna.

### Requirement 4: Registro estruturado da origem e do resultado da busca

**User Story:** Como operador do sistema, quero registros estruturados das buscas
do Firecrawl, para auditar a origem dos dados e diagnosticar falhas por sessão.

#### Acceptance Criteria

1. WHEN uma busca do Firecrawl é concluída com sucesso, THE Firecrawl_Client SHALL
   registrar um log JSON com evento `firecrawl_search_success` contendo o
   `session_id` e a contagem de resultados.
2. IF uma busca do Firecrawl falha, THEN THE Firecrawl_Client SHALL registrar um
   log JSON de erro contendo o `session_id` e o tipo do erro.
3. WHEN o erro do Firecrawl indica exaustão de créditos, THE Firecrawl_Client SHALL
   converter a falha em FirecrawlCreditError.
4. IF o erro do Firecrawl não indica exaustão de créditos, THEN THE
   Firecrawl_Client SHALL converter a falha em FirecrawlProviderError.

### Requirement 5: Validação e normalização de salários e requisitos das vagas

**User Story:** Como usuário, quero que salários e requisitos das vagas sejam
apresentados de forma consistente, marcando claramente o que não foi informado,
para comparar oportunidades sem ambiguidade.

#### Acceptance Criteria

1. WHEN o Scout monta uma entrada de vaga sem salário disponível, THE Scout SHALL
   preencher o campo `salario` com o marcador "Não informado na descrição".
2. WHEN o Scout monta uma entrada de vaga sem benefícios disponíveis, THE Scout
   SHALL preencher o campo `beneficios` com o marcador "Não informado na
   descrição".
3. WHEN o Scout calcula a correspondência de habilidades de uma vaga, THE Scout
   SHALL produzir as listas de habilidades correspondentes, habilidades faltantes
   e a contagem de correspondência referentes aos requisitos daquela vaga.
4. WHERE uma lista de habilidades correspondentes ou faltantes está vazia, THE
   Scout SHALL preencher o campo correspondente com o marcador "Nenhuma".
5. WHEN o Scout calcula o score de aderência de uma vaga, THE Scout SHALL produzir
   um valor inteiro entre 0 e 100.
6. WHEN o Scout consolida os requisitos das vagas, THE Scout SHALL produzir a lista
   de requisitos mais recorrentes com a contagem de ocorrências de cada requisito.

### Requirement 6: Validação e normalização dos atributos dos cursos (Curator)

**User Story:** Como usuário, quero que os atributos dos cursos (plataforma,
preço, nível e duração) venham normalizados e com "não informado" quando ausentes,
para comparar materiais de estudo de forma confiável.

#### Acceptance Criteria

1. WHEN o Curator constrói um recurso de aprendizado a partir de um resultado de
   busca, THE Curator SHALL determinar a plataforma a partir do domínio da URL do
   recurso.
2. WHEN o Curator constrói um recurso de aprendizado, THE Curator SHALL classificar
   o nível como `iniciante`, `intermediario` ou `avancado`.
3. WHEN a duração de um curso não pode ser extraída do título ou da descrição, THE
   Curator SHALL preencher o campo de duração com o marcador "Nao informado".
4. WHEN o Curator constrói um recurso de aprendizado, THE Curator SHALL atribuir um
   valor de preço normalizado dentre as categorias de preço definidas.

### Requirement 7: Normalização e abertura segura de links de vagas

**User Story:** Como usuário, quero clicar para abrir no navegador apenas links de
vagas reais e válidas, para nunca ser levado a URLs inventadas por IA ou a dados
simulados.

#### Acceptance Criteria

1. WHEN o ScoutReport prepara o link de uma vaga com origem `real`, THE ScoutReport
   SHALL exibir um link clicável somente se o valor for uma URL com esquema
   `http` ou `https` válido.
2. IF a origem de uma vaga é `llm` ou `simulated`, THEN THE ScoutReport SHALL NOT
   exibir nenhum link clicável para essa vaga.
3. IF o valor do link de uma vaga real não é uma URL http(s) válida, THEN THE
   ScoutReport SHALL omitir o link clicável dessa vaga.
4. WHEN o Scout gera uma vaga sugerida por IA, THE Scout SHALL preencher o campo
   `link` com um texto não navegável que identifique a sugestão como gerada por IA
   e não verificada.
5. WHEN o ScoutReport exibe um link clicável de vaga real, THE ScoutReport SHALL
   abrir o link em uma nova aba com atributos de segurança `noopener` e
   `noreferrer`.

### Requirement 8: Testes automatizados de origem dos dados

**User Story:** Como desenvolvedor, quero testes automatizados que verifiquem a
classificação de origem e o estado de busca, para impedir regressões na
sinalização de procedência dos dados.

#### Acceptance Criteria

1. THE Sistema SHALL possuir testes automatizados que verifiquem a atribuição do
   campo `source` para os casos `real`, `llm` e `simulated` do Scout.
2. THE Sistema SHALL possuir testes automatizados que verifiquem a atribuição de
   `status_busca` para cada um dos valores `real_success`, `real_empty`,
   `real_degraded`, `no_credits`, `external_error` e `timeout`.
3. THE Sistema SHALL possuir testes automatizados que verifiquem a conversão de
   falhas do Firecrawl em FirecrawlProviderError e FirecrawlCreditError conforme a
   indicação de créditos.

### Requirement 9: Testes automatizados de extração de salários e requisitos

**User Story:** Como desenvolvedor, quero testes automatizados de extração e
normalização de salários e requisitos, para garantir consistência dos artefatos
das vagas e dos cursos.

#### Acceptance Criteria

1. THE Sistema SHALL possuir testes automatizados que verifiquem a marcação "Não
   informado na descrição" para salário e benefícios ausentes em vagas do Scout.
2. THE Sistema SHALL possuir testes automatizados que verifiquem a consolidação
   dos requisitos mais recorrentes com suas contagens de ocorrências.
3. THE Sistema SHALL possuir testes automatizados que verifiquem a normalização de
   plataforma, nível, duração e preço dos cursos do Curator, incluindo a marcação
   "Nao informado" para duração ausente.

### Requirement 10: Testes automatizados de normalização de links

**User Story:** Como desenvolvedor, quero testes automatizados da normalização de
links, para garantir que apenas vagas reais com URLs http(s) válidas sejam
clicáveis.

#### Acceptance Criteria

1. THE Sistema SHALL possuir testes automatizados que verifiquem que uma vaga com
   origem `real` e URL http(s) válida produz um link clicável.
2. THE Sistema SHALL possuir testes automatizados que verifiquem que vagas com
   origem `llm` ou `simulated` não produzem link clicável.
3. THE Sistema SHALL possuir testes automatizados que verifiquem que um valor de
   link sem esquema http(s) válido em uma vaga real não produz link clicável.

### Requirement 11: Roteiro de validação manual com chave e créditos reais

**User Story:** Como validador, quero um roteiro reproduzível para executar o
Firecrawl com chave e créditos reais, para confirmar de ponta a ponta a busca de
vagas e de cursos com critérios objetivos de aprovação.

#### Acceptance Criteria

1. THE Sistema SHALL fornecer um roteiro de validação manual versionado que
   descreva os pré-requisitos de configuração da chave e dos créditos do
   Firecrawl.
2. THE roteiro de validação manual SHALL descrever os passos para executar uma
   busca completa de vagas pelo Scout e registrar o `status_busca` observado.
3. THE roteiro de validação manual SHALL descrever os passos para executar uma
   busca real de cursos pelo Curator e registrar a origem dos recursos
   apresentados.
4. THE roteiro de validação manual SHALL definir critérios objetivos de aprovação
   para salários e requisitos extraídos, para a exibição da origem dos dados e para
   a abertura de links reais de vagas no navegador.
5. WHERE a execução real resulta em ausência de créditos, erro ou timeout, THE
   roteiro de validação manual SHALL definir o resultado esperado para cada um
   desses casos.

## Notas de escopo

- A normalização e validação dos links do CuratorReport (aplicando a mesma
  proteção já existente no ScoutReport) é uma pendência **P1 separada** e não faz
  parte desta especificação; é citada apenas como contexto.
- A execução real consumindo créditos do Firecrawl é coberta como **validação
  manual guiada** (Requisito 11) e não como teste automatizado, por depender de
  chave, créditos e serviço externo.
