# Roadmap — Evolução do Import Vagas

## Menu de esteiras: accordion → master/detail (front)

Sessão executada em 2026-06-23.

Handoff de design do Claude Design alterando o comportamento dos botões do
menu no rodapé do chat.

* [x] `frontend/src/components/ChatInput.tsx`: substituído o accordion (2 cards
  que expandiam) pelo fluxo **master/detail** — 2 pills compactos de esteira;
  ao clicar, só as opções daquela esteira aparecem, com botão "Esteiras"
  (ArrowLeft) para voltar. Estado `activeSection` (null = master).
* [x] `useEffect` reseta para a seleção de esteiras quando o menu sai (agente
  assume), garantindo que os 2 botões reapareçam ao retornar.
* [x] `frontend/src/index.css`: removido o bloco `.menu-accordion-*`,
  adicionado o CSS master/detail (`.esteira-flow`, `.esteira-picker`,
  `.esteira-pill`, `.esteira-detail`, `.esteira-back`, `.esteira-active`).
  `.menu-option*` reaproveitados. `tsc --noEmit` limpo.

## Reconciliação perfil × currículo × vaga

Sessão executada em 2026-06-18.

Detecção de conflitos entre os três artefatos centrais da jornada (perfil do
quiz, currículo analisado e vaga analisada) com escolha de "foco da
candidatura" que define qual fonte deve prevalecer.

### Arquitetura

* [x] `agents/reconciliation.py`: heurística pura (sem LLM, sem IO), reusando
  os helpers canônicos do `resume_matcher` (`_normalize`, `_canonical`,
  `_unique`, `_parse_markdown`, `SENIORITY_ORDER`) para evitar falsos
  conflitos de aliasing (ex.: "powerbi" vs "Power BI").
* [x] `routers/reconciliation.py`: rota HTTP espelhando o padrão do
  `resume_match` — `GET /api/reconciliation/latest` e
  `POST /api/reconciliation/analyze`, com `read_required` + `validate_*` para
  perfil/currículo/vaga e persistência atômica sob lock de sessão.
* [x] O par currículo×vaga **não é recalculado**: o `Reconciler` reusa
  `ResumeMatcher.match` (ou o relatório já salvo em
  `resume-match-report.md`) e incorpora o score ao diagnóstico.

### Detecção de conflitos

* [x] **perfil↔currículo**: Área, Nível, Habilidades técnicas, Soft skills,
  Funções alvo.
* [x] **perfil↔vaga**: Nível, Habilidades técnicas, Ferramentas, Soft skills,
  Modalidade, Localização.
* [x] **currículo↔vaga**: reusado do `ResumeMatcher` existente.
* [x] Score de consistência agregado (0–100) pesando match + conflitos +
  alinhamentos, com nível textual (coerente / divergências relevantes /
  inconsistente).

### Foco da candidatura

* [x] Linha `Foco da candidatura: {perfil|currículo|vaga}` em
  `user-profile.md`, lida por `parse_focus` (tolera acento: "currículo").
* [x] Resolução por precedência: parâmetro explícito no `POST /analyze` >
  linha do perfil > default "vaga".
* [x] Recomendações geradas conforme o foco (ex.: foco "currículo" →
  atualizar o perfil para refletir o currículo).

### Wiring e testes

* [x] `RECONCILIATION_FILE` adicionado em `config.py` e `SessionPaths`
  (`session.py`), espelhando o padrão dos demais artefatos.
* [x] Router registrado em `main.py` (33 rotas totais, +2).
* [x] `tests/test_reconciliation.py`: 20 testes cobrindo `validate_profile`,
  `parse_focus`, detecção de conflitos nos dois pares novos, variação do
  foco, reuso do match e round-trip Markdown.
* [x] `py_compile` nos arquivos novos/modificados; `import main` com as rotas
  registradas; `102 passed` na suíte completa.

### Fora de escopo (registrado para próximas sessões)

* [x] Endpoint PUT/PATCH dedicado para setar o foco (hoje vem do perfil ou do
  body do `POST /analyze`).
  Fechado em 2026-06-24: `PUT /api/reconciliation/focus`.
* [x] Integração com o fluxo conversacional do Maestro (opção de menu).
  Fechado em 2026-06-23: opção **I** no menu (roteamento conversacional E–I).
* [x] Leitura do foco pelos agentes match/tailor/PDI para pesar resultados.
  Fechado em 2026-06-24: agentes recebem `focus` e priorizam o `next_steps`.
* [ ] "Atualizar perfil somente com confirmação do usuário" e os demais
  sub-itens de escolha de base.

## Hardening do Backend e Resiliencia (Recem-Concluido)

Esta etapa transformou o backend de um prototipo funcional para uma API com padrao de producao, resiliente a quedas de rede, falhas de LLM e I/O concorrente.

### Fase 1: Observabilidade e Logs Estruturados

* [x] Configuracao centralizada em `logging_config.py` com saida JSON e fallback em arquivo (`backend.log`).
* [x] Rastreio completo do WebSocket (conexao, streaming e troca de estado) atrelado ao `session_id`.
* [x] Rastreio de LLMOps na base dos agentes (latencia, tokens, erros e tamanho de prompt).

### Fase 2: Tratamento de Excecoes e Contratos de Erro

* [x] Remocao de capturas genericas nos fluxos criticos dos agentes.
* [x] Criacao da excecao de dominio `LLMProviderError` para falhas da OpenAI e envelope seguro para falhas do Firecrawl.
* [x] Handlers globais no FastAPI para padronizar erros 422 (validacao) e 500 (internos) em JSON seguro, sem vazar stack trace.
* [x] WebSocket fecha conexoes de forma limpa e libera recursos da memoria.

### Fase 3: Persistencia Segura e Escrita Atomica (Fim da Corrupcao de Dados)

* [x] Uso de `asyncio.Lock` global/por sessao para isolar leitura/escrita em operacoes simultaneas.
* [x] Funcao `write_text_atomic_async` usando arquivo `.tmp` e `os.replace` para proteger contra crash no meio da gravacao.
* [x] Remocao de bloqueio do Event Loop com `asyncio.to_thread` para I/O de disco.
* [x] Teste de estresse (`test_concurrency.py`) comprovando 50 escritas simultaneas sem perdas.

### Fase 4: Persistencia de Estado do WebSocket

* [x] Criacao do `chat_state.json` isolado na pasta da sessao (`data/sessions/{id}/`).
* [x] Gravacao atomica do estado (agente atual, passo do quiz, etapa do Coach e historico recente) a cada mudanca critica.
* [x] Restauracao automatica de contexto no handshake do WebSocket: o usuario recarrega a pagina e a conversa continua de onde parou.

### Fase 5: Seguranca e Integracoes Oficiais

* [x] Substituicao do Firecrawl CLI pelo SDK oficial `firecrawl-py`, removendo chamadas de `subprocess` que travavam em ambientes Windows.
* [x] Chamadas do SDK protegidas por `asyncio.to_thread`, mantendo o Event Loop do FastAPI responsivo.
* [x] Endurecimento do upload de curriculos com Magic Numbers, validacao de `Content-Type`, limite rigido de tamanho e retorno 413 para payload grande.
* [x] Validacao automatizada: `pytest` completo com 73 testes passando.

### Fase 6: Validacao em cascata

* [x] Fluxo curriculo -> vaga -> match -> sugestoes -> PDI auditado no backend.
* [x] Validadores de sugestoes e PDI fortalecidos para rejeitar score de match fora de 0..100.
* [x] Testes unitarios cobrem score ausente, scores invalidos (-1/100, 101/100, 999/100, texto) e scores validos (0/100, 1/100, 50/100, 100/100).
* [ ] Pendente: adicionar testes HTTP para artefatos corrompidos nas rotas de sugestoes e PDI.

## Carroceria e Pista (Proximos Marcos Arquiteturais)

Agora que o motor esta blindado, o foco passa a ser entrega continua, infraestrutura e UX de erros.

### 1. Frontend Resiliente (Conectando as pontas do Backend)

* [x] Tratamento visual de erros: consumir os contratos padronizados 422 e 500 do FastAPI para exibir toasts ou banners amigaveis quando o LLM demorar ou a API externa falhar.
  Núcleo concluído via `apiRequest` (sub-itens abaixo); resta só ampliar os testes de reconexão longa do WebSocket.
  * [x] Helper `frontend/src/lib/api.ts` criado para normalizar 422, 500, corpo vazio, HTML/texto inesperado, falha de rede e timeout.
  * [x] Fluxos de curriculo, vaga, match/reconciliacao, sugestoes, PDI e pipeline passaram a usar `apiRequest`.
  * [x] `ProfilePanel` e `ApplicationTracker` auditados e migrados para `apiRequest`, preservando loading, estado vazio, estado anterior e mensagens de erro existentes.
  * [x] Validacoes executadas nesta frente: `npm run test`, `npm run lint` e `npm run build` no frontend.
  * [x] Envio silencioso do WebSocket auditado e corrigido: `sendMessage` retorna sucesso/falha e adiciona mensagem amigavel quando a conexao cai antes do envio.
  * [x] Validado com teste de envio WebSocket aberto e tentativa de envio com socket fechado.
  * [ ] Pendente: ampliar testes de estabilidade para reconexao real do WebSocket durante streaming longo.
* [ ] Recuperacao visual de sessao: fazer o React usar o estado restaurado do WebSocket no primeiro load para repintar quiz/Coach sem expor a reconexao ao usuario.

### 2. Infraestrutura e Containerizacao (Docker)

* [x] Dockerizacao do Backend: criar `Dockerfile` com imagem Python leve, dependencias instaladas e porta 8000 configurada.
  `backend/Dockerfile` (`python:3.12-slim`, usuário sem privilégios, `HEALTHCHECK` em
  `/health`, `uvicorn main:app` em 0.0.0.0:8000); contexto de build na raiz para
  incluir `personas/` e `skills/`.
* [x] Dockerizacao do Frontend: criar `Dockerfile` para build React/Vite servido por Nginx.
  `frontend/Dockerfile` multi-stage (`node:22-alpine` → `nginx:1.27-alpine`) +
  `nginx.conf.template` com proxy reverso de `/api` e `/ws`.
* [x] Docker Compose: orquestrar Frontend, Backend e Mock Server com `docker-compose up`.
  `docker-compose.yml` com os três serviços, volume `backend-data` para o estado e
  profile `mock`.

### 3. Esteira de Automacao Continua (CI/CD Definitivo)

* [x] Rodar testes na nuvem: configurar GitHub Actions para executar a suite robusta (+70 testes) a cada push.
  `backend-ci.yml` roda `pytest backend/tests/ -v` em PRs/pushes para `main` (último estado: 120 testes).
* [x] Pipeline bloqueante: impedir merge quando `test_concurrency.py` ou testes de contrato falharem.
  `backend-ci.yml` roda a suíte completa, incluindo `test_concurrency.py`.

---

## Problemas críticos de arquitetura: isolamento + lock

Sessão executada em 2026-06-16.

### Lock e escrita atômica de applications.json

* [x] `asyncio.Lock` serializa o ciclo ler-modificar-gravar (create/update/delete).
* [x] Escrita atômica via arquivo temporário + `os.replace` (nunca trunca o JSON
  se o processo cair no meio).
* [x] `tests/test_applications.py`: 8 testes (CRUD, stats, 404, atomicidade e
  isolamento entre sessões) — rotas que antes não tinham cobertura.

### Isolamento multiusuário por session_id anônimo

* [x] `backend/session.py`: `SessionPaths` (espelha os nomes de `config`),
  `sanitize_session_id` (neutraliza path traversal) e dependency
  `get_session_paths` (lê o header `X-Session-Id`). Sessão default usa `data/`;
  sessões reais ficam em `data/sessions/{id}/`.
* [x] Todas as rotas REST migradas para `Depends(get_session_paths)`:
  data_files, profile, resume, resume_match, resume_tailoring, job_description,
  pdi e applications.
* [x] `BaseAgent` recebe `SessionPaths`; Maestro, Coach, Scout e Curator usam
  `self.paths.*` em vez de `config.*_FILE`/`Path("data")`. Maestro propaga os
  paths aos sub-agentes.
* [x] WebSocket lê `session_id` da query string e cria o Maestro com os paths
  da sessão.
* [x] Frontend: `lib/session.ts` gera um ID anônimo (localStorage), injeta o
  header `X-Session-Id` em todo `/api/` via wrapper de `fetch`, e passa
  `session_id` na URL do WebSocket.
* [x] `tests/test_session.py` (8) e `tests/test_agents_paths.py` (4) cobrindo
  sanitização, isolamento de paths e propagação aos agentes.
* [x] `59 passed`; `npm run lint`/`npm run build` do frontend passam; app FastAPI
  importa com 31 rotas.
* [ ] Migração de dados legados de `data/*.md` para uma sessão (hoje viram a
  sessão default; usuários novos começam em `data/sessions/{id}/`).

## Primeiros testes automatizados do backend

Sessão executada em 2026-06-16.

* [x] Instalado `pytest==9.1.0` no venv; criado `backend/requirements-dev.txt`.
* [x] Criado `backend/pytest.ini` (`pythonpath = .`, `testpaths = tests`).
* [x] `tests/test_job_description_analyzer.py`: análise heurística (`analyze`),
  contrato das chaves do dict, round-trip `analysis_to/from_markdown` e
  `validate_job_analysis`.
* [x] `tests/test_common.py`: `read_required` lê arquivo, e levanta HTTP 400 para
  arquivo ausente e arquivo vazio (`tmp_path`).
* [x] `tests/test_job_description_route.py`: integração via `TestClient` — POST
  `/analyze` 200 e 400 (descrição curta), persistência + GET `/latest`, e 404
  sem análise prévia (`monkeypatch` isola o arquivo de `data/`).
* [x] `tests/conftest.py`: fixtures compartilhadas `job_markdown` e
  `resume_markdown` (formato real dos artefatos de `data/`).
* [x] `tests/test_resume_matcher.py`: `match()` (score 0–100, skill presente vs
  ausente, contrato do dict), round-trip do relatório e validadores.
* [x] `tests/test_pdi_validators.py` e `tests/test_tailor_validators.py`:
  validadores de pré-requisito aceitam o relatório de match REAL (testes
  encadeados entre agentes) e rejeitam lixo; `*_from_markdown` devolve `None`.
* [x] `tests/test_scout.py`: lógica pura do Scout — `_match_skills`
  (case-insensitive), `_priority_from_score`, `_score_opportunity` (limite 100),
  `_area_skills` (default) e `_build_job_entry` (contrato do dict).
* [x] `tests/test_curator.py`: lógica pura do Curator — `_platform_for_url`,
  `_price_for_platform`, `_classify_level` e `_extract_duration`.
* [x] `conftest.py`: fixture `autouse` injeta chave fake pro cliente OpenAI ser
  instanciável (Scout/Curator herdam de BaseAgent, que cria o cliente no init).
* [x] `39 passed` em `python -m pytest`. `run()` de Scout/Curator fica de fora
  (depende de Firecrawl/rede); só a heurística determinística é testada.
* [ ] Testes do caminho real de LLM (hoje cai em fallback — ver bug do base_url).

Achados menores detectados pelos testes — corrigidos:

* [x] `Curator._price_for_platform` agora remove acentos antes de checar o texto,
  então "grátis"/"gratuíto" casam com "gratis"/"gratuito".
* [x] `Curator._extract_duration` preserva a unidade completa ("10 horas",
  "30 minutos"): a alternância do regex prioriza palavras longas antes de "h" e
  reúne número + unidade com um único espaço.
* [x] `39 passed` após as correções; `py_compile` de `curator.py` OK.

## Auditoria atual

Última revisão: 2026-06-15.

Validação executada nesta revisão:

* [x] `npm run lint` concluído sem erros.
* [x] `npm run build` concluído sem erros.
  Os bloqueios de props em `App.tsx`/`StatusBar` e tipagem de `Skill` em `ChatMessage.tsx` foram corrigidos.
* [x] Backend compilado e aplicação FastAPI importada com sucesso.
* [x] Rotas REST e WebSocket registradas na aplicação.
* [x] Firecrawl SDK (`firecrawl-py`) declarado no backend e usado sem CLI/subprocess.
* [x] `FIRECRAWL_API_KEY` configurada em `backend/.env` e carregada por caminho absoluto.
* [x] Suíte automatizada de testes disponível.
  `backend/tests/` cobre agentes, rotas, concorrência e isolamento por sessão. Última execução: `150 passed`.
* [x] QA visual completo executado em navegadores reais.
  A estabilização responsiva foi validada no Chrome em oito resoluções. As rodadas finais de visual, acessibilidade e fluxo funcional com backend real foram validadas no Chrome e Edge.

### Estrutura de arquivos validada

* [x] Arquivos gerados em `data/` tratados como estado local e ignorados pelo Git.
* [x] `data/README.md` mantido como único arquivo versionado da pasta.
* [x] Artefatos locais presentes após os fluxos executados:
  * [x] `course-recommendations.md`
  * [x] `job-description-analysis.md`
  * [x] `job-search-results.md`
  * [x] `pdi-plan.md`
  * [x] `personality-quiz.md`
  * [x] `resume-analysis.md`
  * [x] `resume-match-report.md`
  * [x] `resume-tailoring-suggestions.md`
  * [x] `user-profile.md`
* [x] `interview-session.md` tratado como artefato opcional, criado somente após
  iniciar uma entrevista simulada.
* [x] Geração e leitura de `resume-analysis.md` validadas.
  O artefato pode estar ausente no estado inicial limpo e é criado pelo upload.
* [x] Geração e leitura de `resume-match-report.md` validadas.
  O artefato pode estar ausente antes da primeira comparação.
* [x] Geração e leitura de `resume-tailoring-suggestions.md` validadas.
  O artefato pode estar ausente antes da primeira geração de sugestões.

### Rotas backend validadas

* [x] Todas as rotas implementadas:
  * [x] `applications.py` - Candidaturas
  * [x] `chat.py` - WebSocket e streaming
  * [x] `common.py` - Utilitários compartilhados
  * [x] `data_files.py` - Leitura de arquivos Markdown
  * [x] `job_description.py` - Análise de vaga
  * [x] `pdi.py` - Geração de PDI
  * [x] `profile.py` - Perfil do usuário
  * [x] `resume.py` - Upload e análise de currículo
  * [x] `resume_match.py` - Comparação vaga x currículo
  * [x] `resume_tailoring.py` - Sugestões seguras

### Agentes backend validados

* [x] Todos os agentes implementados:
  * [x] `base.py` - Classe base comum
  * [x] `coach.py` - Entrevista simulada
  * [x] `curator.py` - Trilhas de aprendizado
  * [x] `job_description_analyzer.py` - Análise de vaga
  * [x] `maestro.py` - Orquestrador principal
  * [x] `pdi_generator.py` - Geração de PDI por vaga
  * [x] `resume_matcher.py` - Match vaga x currículo
  * [x] `resume_tailor.py` - Sugestões seguras de currículo
  * [x] `scout.py` - Busca de vagas

### Componentes frontend validados

* [x] Todos os componentes principais implementados:
  * [x] `ApplicationPipeline.tsx` - Pipeline visual de candidatura
  * [x] `ApplicationTracker.tsx` - Rastreamento de candidaturas
  * [x] `ChatTerminal.tsx` - Terminal de chat
  * [x] `JobDescriptionAnalyzer.tsx` - Analisador de vaga
  * [x] `PdiPlan.tsx` - Visualização de PDI
  * [x] `ProfilePanel.tsx` - Painel lateral de perfil
  * [x] `QuizPanel.tsx` - Quiz de perfil
  * [x] `ResumeMatchReport.tsx` - Relatório de aderência
  * [x] `ResumeTailoringSuggestions.tsx` - Sugestões seguras
  * [x] `ResumeUpload.tsx` - Upload de currículo
  * [x] `ScoutReport.tsx` - Relatório de busca

## Diagnóstico a partir do currículo

Sessão executada em 2026-06-14.

* [x] Maestro passou a reconhecer explicitamente o comando do botão “Iniciar/Continuar diagnóstico” como início de diagnóstico, sem tratá-lo como resposta do quiz.
* [x] Diagnóstico reaproveita `data/resume-analysis.md` para pré-preencher área, nível, habilidades técnicas e soft skills.
* [x] Quiz agora pula campos já detectados no currículo e pergunta somente localização, preferência de trabalho, objetivo de carreira ou qualquer outro campo ainda ausente.
* [x] Frontend passou a aparar espaços da pergunta atual antes de renderizar o painel do quiz.
* [x] Corrigida codificação de `backend/requirements.txt`, que havia sido salvo como UTF-16.
* [x] Corrigido texto corrompido “Áreas de Melhoria” ao salvar a sessão de entrevista.
* [x] Validação executada: `npm run lint`, `npm run build`, `py_compile`, `import main` e smoke do Maestro com paths temporários.
* [x] Checagem visual curta executada no navegador interno com frontend e backend reais em localhost.
* [ ] Criar teste automatizado cobrindo o pré-preenchimento do quiz a partir do currículo.
* [x] Validar o fluxo no navegador com upload real de currículo seguido de “Iniciar/Continuar diagnóstico”.

## Correção do card de perfil e limpeza do backend

Sessão executada em 2026-06-14.

### Frontend

* [x] Corrigir bug em que o card de perfil (`.profile-summary`) era esmagado de
  ~66px para ~9px ao abrir "Detalhes do perfil", parecendo sumir.
  Causa: `overflow: hidden` zera o `min-height` automático do flex item, então o
  card encolhia quando o `<details>` fazia o container transbordar.
  Correção: `flex-shrink: 0` em `.profile-summary` (mantém o card sticky fixo).
* [x] Reproduzido e validado no navegador (antes 9px, depois 66px com detalhes abertos).

### Backend — bugs e qualidade de código

* [x] Maestro: corrigir mojibake `"PontuaÃ§Ã£o Final"`/`"Ãreas de Melhoria"`
  gravado em `data/interview-session.md` → `"Pontuação Final"`/`"Áreas de Melhoria"`.
* [x] Maestro: mover imports `json`/`base64` do corpo de `_encode_answers` para o topo.
* [x] `base.py`: proteger `stream_llm`/`call_llm` contra chunks/respostas com `choices` vazio.
* [x] `main.py`: usar `config.DATA_DIR` (absoluto) no `lifespan` em vez de caminho
  relativo `../data`, alinhando com o I/O real dos agentes.
* [x] Extrair `read_required` duplicado para `routers/common.py`
  (usado por resume_match, resume_tailoring e pdi).
* [x] Validação: `py_compile` em todos os arquivos alterados + `import main`
  com sucesso no `backend/.venv` (25 rotas).

### Itens identificados e NÃO resolvidos (registro)

* [x] Isolamento multiusuário: agentes leem/escrevem `data/*.md` globais sem
  `session_id`; usuários simultâneos sobrescrevem dados uns dos outros
  (refactor arquitetural, fora do escopo desta sessão).
  Resolvido em 2026-06-16: `session.py`/`SessionPaths` isola por `session_id` (`test_session.py`).
* [x] `applications.json`: read-modify-write sem lock (possível corrida).
  Resolvido em 2026-06-16: `asyncio.Lock` + escrita atômica (`test_applications.py`).
* [ ] Limpar checagens defensivas de mojibake espalhadas (curator/coach) após
  garantir UTF-8 na origem dos dados.

### Git

* [x] Dois commits na `fable` (frontend + backend), push e merge fast-forward na `main`.

## Estabilização responsiva do frontend

Etapa executada em 2026-06-14, sem alterações de backend, agentes ou escopo do PDI.

* [x] Sidebar não corta conteúdo em `1366x768`.
* [x] Sidebar não corta conteúdo em `1280x720`.
* [x] Sidebar não possui scroll duplo.
* [x] Painel inferior da sidebar rola corretamente.
* [x] Tags da sidebar não vazam.
* [x] Barra de progresso respeita a largura.
* [x] Lista de agentes permanece acessível.
* [x] Logo `import vagas` continua clicável.
* [x] Item ativo continua visível.
* [x] Header não sobrepõe ações.
* [x] Pipeline continua legível em notebook menor.
* [x] Chat/input não cobre conteúdo.
* [x] Não existe scroll horizontal em notebook menor.
* [x] Não existe scroll horizontal em mobile.
* [x] Mobile mantém navegação utilizável.
* [x] `npm run lint` passa.
* [x] `npm run build` passa.

Resoluções validadas no Chrome:

* [x] `1440x900`
* [x] `1366x768`
* [x] `1280x720`
* [x] `1024x768`
* [x] `900x720`
* [x] `768x1024`
* [x] `390x844`
* [x] `360x800`

## QA final visual e acessibilidade

Etapa executada em 2026-06-14, sem alterações de backend, agentes, PDI ou dependências.

* [x] Tags e textos extremos não causam overflow horizontal.
* [x] Botões principais têm altura mínima confortável para clique.
* [x] Controles em dispositivos touch têm área mínima de `44x44` CSS px.
* [x] Foco por teclado permanece visível nos controles e campos.
* [x] Modais mantêm o foco, fecham com `Escape` e restauram o foco.
* [x] Status combinam texto e ícone e não dependem apenas de cor.
* [x] Contraste dos textos principais, badges, botões e alertas foi revisado.
* [x] Redução de movimento foi validada para CSS e Framer Motion.
* [x] Chrome `149.0.7827.114` validado em `1366x768` e `390x844`.
* [x] Edge `149.0.4022.69` validado em `1366x768` e `390x844`.
* [x] `npm run lint` passa.
* [x] `npm run build` passa.

## QA funcional final com backend real

Etapa executada em 2026-06-14, sem alterações de backend, agentes, PDI ou dependências.

* [x] Backend real permaneceu saudável durante os testes.
* [x] Chrome `149.0.7827.114` concluiu o fluxo principal em `1366x768`.
* [x] Edge `149.0.4022.69` concluiu o fluxo principal em `1366x768`.
* [x] Sidebar, logo, pipeline, modal de vaga, navegação lateral e chat permaneceram funcionais.
* [x] Upload e análise de currículo TXT concluídos.
* [x] Análise de vaga, match e sugestões seguras concluídos.
* [x] Cópia de seção confirmou o estado “Copiado”.
* [x] Relatórios reais com parágrafos, listas e tags extensas não causaram overflow horizontal.
* [x] Cards longos mantiveram largura, rolagem e ações acessíveis.
* [x] O fallback do botão de copiar foi corrigido para contextos com Clipboard API restrita.
* [x] Nenhum erro HTTP ou exceção de navegador foi observado.
* [x] `npm run lint` passa.
* [x] `npm run build` passa.

Pendências mantidas:

* [ ] Executar todos os fluxos de erro com backend disponível e indisponível.
  Restam match sem vaga válida, sugestões sem match e desligamento físico do processo backend.
* [x] Confirmar separadamente a atualização do perfil após o upload do currículo.
* [x] Revalidar quiz e painel de candidaturas em uma rodada dedicada.

Pendências críticas confirmadas:

* [x] Componente `PdiPlan` implementado no frontend (`frontend/src/components/PdiPlan.tsx`).
* [x] **Integrar o componente `PdiPlan` à interface visível e ao pipeline.**
  Implementado em modal lazy, com ação liberada após as sugestões seguras e leitura do plano salvo.
* [x] Fazer a pipeline reconhecer uma análise de currículo concluída após upload e nos artefatos dependentes.
  Implementado via localStorage e validação de artefatos dependentes (match/tailoring).
* [x] **Expor `resume-analysis.md` por uma rota de leitura** para detectar o arquivo diretamente em uma nova sessão.
  Implementado em `GET /api/data/resume-analysis`; a pipeline usa a API como fonte principal.
* [x] **Criar arquivo `resume-analysis.md` durante upload/análise de currículo.**
  Validado com upload TXT real no Chrome em 2026-06-14.
* [x] Conectar o Coach à descrição da vaga e ao relatório de aderência.
  Fechado em 2026-06-23: Coach lê `job-description-analysis.md` e `resume-match-report.md` (`test_coach.py`).
* [x] Criar testes automatizados mínimos para backend e frontend.
  Fechado: 150 testes no backend + 26 no frontend.
* [x] Executar e registrar `docs/frontend-qa-checklist.md`.

## Barra de escrita flutuante + cards de opção no chat

Sessão executada em 2026-06-15.

* [x] `ChatInput`: barra de escrita agora é flutuante (translúcida, com blur,
  glow e cantos arredondados; shell sem fundo sólido, fade por baixo).
* [x] No modo `menu`, a barra é substituída por cards de opção (A/B/C/D) com
  ícone, atalho e cor por agente (Scout/Curator/Coach/Maestro).
* [x] Durante o streaming a barra permanece; os cards só entram quando o agente
  termina (`showOptions = mode === 'menu' && !isStreaming`).
* [x] Animações com `AnimatePresence`: troca barra↔cards com fade/slide e
  stagger por card; hover/tap nos cards.
* [x] Removidos os textos auxiliares acima/abaixo da barra.
* [x] Shell do input deixado totalmente transparente (removida a faixa de
  gradiente que tampava o conteúdo atrás dos cards) — só os botões flutuam.
* [x] Faixa/seam eliminada de vez: a barra agora é `position: absolute` no rodapé
  do `.main-content` (z-index 6), sobreposta ao `.chat-terminal`, que passa a
  preencher toda a altura por baixo — fundo contínuo, sem emenda. Terminal ganhou
  `padding-bottom` para a última mensagem não ficar atrás da barra.
* [x] `npm run build` passa.

## Centralização vertical da barra e animação de expandir

Sessão executada em 2026-06-15.

* [x] Barra recolhida centralizada na vertical: `padding-bottom: 0` virou
  padding vertical simétrico (16px), o badge não encosta mais na borda.
* [x] Animação de expandir mais bonita: `pipeline-track` agora abre com
  `AnimatePresence` (altura 0→auto + fade) e cada etapa entra com stagger
  (framer-motion), em vez de aparecer instantânea.
* [x] README da raiz atualizado com o estado completo do projeto.
* [x] `npm run build` passa.

## Polimento da barra recolhida e da sidebar

Sessão executada em 2026-06-15.

* [x] Barra de progresso recolhida centralizada (`align-self: center`) com
  animação de entrada (`minibar-enter`, fade + slide, respeita reduced-motion).
* [x] Removido o toggle de sidebar duplicado no header do workspace (mantido só
  no mobile, onde é o único jeito de abrir o painel off-canvas); no desktop fica
  apenas o toggle dentro do ProfilePanel.
* [x] Transição da sidebar/`profile-panel` suavizada (cubic-bezier 0.34s +
  `will-change`) para reduzir o travamento ao recolher/expandir.
* [x] `npm run build` passa.

## Barra de progresso recolhida + correção de ordem do chat

Sessão executada em 2026-06-15.

Rota de candidatura recolhida vira barra de progresso:

* [x] `ApplicationPipeline`: quando recolhida, renderiza `.pipeline-minibar`
  com 6 nós ligados por conectores, no estilo do mock de baixa fidelidade.
* [x] Refino de layout: recolhida, a barra fica inline no cabeçalho entre o
  rótulo "Career Arcade Pipeline" e o badge "X de 4"; a seta de toggle fica à
  direita do badge; o título "Sua rota de candidatura" e o subtexto só aparecem
  quando expandida.
* [x] Visual futurista: nós concluídos com núcleo neon ciano e brilho;
  conectores concluídos em gradiente ciano→rosa com glow; etapa atual com anel
  rosa pulsante (respeita `prefers-reduced-motion`).
* [x] Bug de layout corrigido: `.pipeline-header > div` (especificidade 0,1,1)
  sobrescrevia o `display:flex` da minibar e das ações (segmentos e seta
  empilhavam na vertical). A regra grid passou a mirar só `.pipeline-heading`.
* [x] Eyebrow "Career Arcade Pipeline" forçado em ciano neon; título/subtexto
  ficam no DOM e somem via CSS quando recolhido, evitando que o `:last-child`
  atinja o eyebrow.

Correção do fluxo do chat (resposta aparecendo na bolha de cima):

* [x] `useWebSocket`: a mutação de `streamingIdRef` saiu de dentro do updater do
  `setMessages` (no modo concorrente o updater pode rodar/descartar mais de uma
  vez, mandando tokens para a bolha errada).
* [x] `sendMessage` zera `streamingIdRef` ao enviar, garantindo que a resposta
  abra uma bolha nova abaixo da mensagem do usuário.
* [x] `npm run build` passa.

## Privacidade dos dados locais

Sessão executada em 2026-06-15.

* [x] Arquivos Markdown gerados em `data/` deixaram de ser rastreados pelo Git.
* [x] `.gitignore` passou a ignorar `data/*.md`.
* [x] `data/README.md` e futuros arquivos `*.example.md` permanecem permitidos
  para documentar a pasta sem versionar dados pessoais.
* [x] `data/README.md` documenta que perfil, vagas, análises e planos são estado
  local, variam por pessoa/sessão e podem conter informações sensíveis.
* [x] Artefatos locais continuam disponíveis em runtime, mas somente
  `data/README.md` permanece rastreado no repositório.

## Filtro de data nas vagas + rota de candidatura retraível

Sessão executada em 2026-06-15.

Filtro de recência das vagas (24h / 7 dias / 1 mês / todas):

* [x] Scout: `_run_firecrawl_search` aceita `tbs` e passa `--tbs` (qdr:d/w/m) ao
  Firecrawl; `run()` lê `date_filter` do contexto via `DATE_FILTER_TBS`.
* [x] Maestro: guarda `self.date_filter` e repassa ao `ScoutAgent.run`.
* [x] Router `chat.py`: encaminha `date_filter` da mensagem para o contexto.
* [x] Frontend: `WsOutgoing.date_filter` + tipo `DateFilter`; `sendMessage`
  só envia o filtro quando há recorte (todas = sem filtro).
* [x] UI: chips de período sob "Oportunidades" na sidebar; clicar dispara a
  busca já filtrada. "all" não aplica `--tbs`.
* [x] Validado: `firecrawl search --tbs qdr:w` retorna 10 vagas reais.

Rota de candidatura (ApplicationPipeline) retraível:

* [x] Botão de toggle (chevron) no cabeçalho; estado persistido em
  localStorage (`import-vagas:pipeline-collapsed`).
* [x] Track e nota de sync ocultados quando recolhido; chevron rotaciona.
* [x] `npm run lint`, `npm run build`, `py_compile` e importação do FastAPI passam.

## Correção do botão "Continuar para o quiz" (descasamento de comando)

Sessão executada em 2026-06-15.

Causa raiz: o botão "Continuar para o quiz" enviava a mensagem
`'Iniciar/Continuar diagnóstico'`, mas o Maestro só intercepta o comando de
(re)iniciar o diagnóstico quando a mensagem é exatamente
`"quero criar meu perfil profissional"` (`START_PROFILE_COMMAND`). Sem casar, a
mensagem caía em `_handle_menu` como opção inválida e o menu A/B/C/D reaparecia.

Correção:

* [x] `App.tsx` (`handleContinueQuizAfterResume`): envia a string exata de
  `START_PROFILE_COMMAND`. Agora o clique sempre reinicia o diagnóstico.
* [x] Verificado que `_start_diagnostico` → `_seed_answers_from_resume` já
  pré-preenche Área, Nível, Habilidades e Soft skills a partir de
  `resume-analysis.md` e pergunta só os 3 campos restantes (Preferências de
  trabalho, Localização, Objetivo de carreira). Testado contra o arquivo real.
* [x] `npm run build` do frontend passa.

## Correção do link "Ver vaga" e do Scout caindo em modo simulado

Sessão executada em 2026-06-15.

Causa raiz: o Scout caía em `_simulate_opportunities`, gravando
`link="Oportunidade simulada a partir do perfil"`, e o frontend tentava abrir
esse texto como URL. O modo simulado disparava porque o subprocess do Firecrawl
falhava silenciosamente no Windows por dois motivos:

* `subprocess.run(["firecrawl", ...])` sem `shell=True` usa CreateProcess, que
  não resolve PATHEXT → `firecrawl.cmd` não era encontrado → `FileNotFoundError`
  capturado → lista vazia → modo simulado.
* Mesmo resolvendo o executável, `text=True` decodificava a saída em cp1252 e
  quebrava com `UnicodeDecodeError` na saída UTF-8 do CLI.

Correções:

* [x] `scout.py`: resolve o executável com `shutil.which("firecrawl")` (respeita PATHEXT/.cmd).
* [x] `scout.py`: subprocess com `encoding="utf-8", errors="replace"` no search e no scrape.
* [x] `scout.py`: injeta `FIRECRAWL_API_KEY` no env do subprocess via `_firecrawl_env()`.
* [x] `config.py`: `load_dotenv` aponta para `backend/.env` absoluto, independente do CWD.
* [x] `ScoutReport.normalizeLink()`: só renderiza "Ver vaga" quando o link parece domínio real (`*.tld`); texto descritivo é descartado. Defesa para vagas simuladas residuais.
* [x] Validado em PowerShell: `firecrawl search` retorna 10 vagas reais com URLs; `py_compile` de scout.py e config.py OK.

Pendências relacionadas:

* [ ] `CuratorReport` ("Abrir recurso") tem o mesmo padrão de link cru e pode reproduzir o bug — aplicar a mesma normalização.
* [ ] Reiniciar o backend para carregar as correções e revalidar "Ver vaga" abrindo URL real no navegador.

## Estabilização funcional de perfil, candidaturas e reconexão

Sessão executada em 2026-06-14, sem alterações de backend, Coach, Firecrawl,
multiusuário, deploy ou dependências.

* [x] `ProfilePanel` distingue perfil ausente de falha de leitura e oferece nova tentativa.
* [x] Upload real de currículo atualiza o perfil e inicia o diagnóstico pelo botão de continuação.
* [x] `ApplicationTracker` valida status e contrato da resposta antes de renderizar.
* [x] Candidaturas exibem estados distintos de loading, erro e vazio.
* [x] PATCH, DELETE e notas não produzem falso sucesso quando a requisição falha.
* [x] Queda durante streaming limpa loading e desbloqueia o chat para a reconexão.
* [x] Pipeline usa `resume-analysis` da API como fonte principal e remove fallback obsoleto.
* [x] Placeholder “Não analisado” não marca a etapa Vaga como concluída.
* [x] Chrome `149.0.7827.114` validado em `1366x768` e `390x844`, sem overflow horizontal.
* [x] Indisponibilidade de `/api` e `/ws` simulada no navegador com mensagens amigáveis e retry.
* [x] WebSocket reconectou automaticamente após a rede ser liberada.
* [x] Rotas de perfil, currículo, vaga, match, sugestões, PDI e candidaturas responderam `200`.
* [x] `npm run lint` passa.
* [x] `npm run build` passa.
* [x] `python -m py_compile backend/main.py` passa.
* [x] FastAPI importado com 27 rotas registradas.

Pendências mantidas:

* [ ] Executar desligamento físico do backend; o PID da porta 8000 não ficou acessível ao ambiente de teste.
* [ ] Testar diretamente match sem vaga válida e sugestões sem relatório de match.
* [ ] Revisar estados visuais dos componentes restantes em uma rodada global.

## UX pós-ação e sidebar compacta

Sessão executada em 2026-06-15, limitada ao frontend e à documentação.

* [x] Criado hook reutilizável para foco, `scrollIntoView`, redução de movimento e destaque temporário.
* [x] Currículo, vaga, match, sugestões e PDI mostram confirmação textual “Gerado agora”.
* [x] Resultados gerados recebem foco acessível e orientação curta para a próxima etapa.
* [x] PDI mantém o modal e ajusta a rolagem no container interno.
* [x] Sidebar desktop alterna entre 232 px e 76 px, com preferência persistida em `localStorage`.
* [x] Modo compacto preserva logo, navegação principal, agentes, tooltips e `aria-label`.
* [x] Mobile mantém o comportamento de painel lateral, sem aplicar o rail compacto.
* [x] Chrome validado em `1366x768`, `1280x720` e `390x844`.
* [x] Sem overflow horizontal nas três resoluções.
* [x] Foco visível e `prefers-reduced-motion` preservados.
* [x] `npm run lint` passa.
* [x] `npm run build` passa.
* [ ] Revalidar especificamente o auto-scroll para mensagens de erro em todos os fluxos.

## Automação de CI e guarda de dados

Sessão refletida pelos commits `d01b67c` e `ce92319`.

* [x] Workflow `Frontend CI` criado em `.github/workflows/ci.yml` para instalar dependências, rodar lint e gerar build do frontend.
* [x] Workflow `Backend CI` criado em `.github/workflows/backend-ci.yml` para instalar dependências, compilar arquivos Python e importar a aplicação FastAPI.
* [x] Workflow `Data Guard` criado em `.github/workflows/data-guard.yml` para bloquear arquivos sensíveis de runtime rastreados em `data/`.
* [x] Workflow `Docs Check` criado em `.github/workflows/docs-check.yml` para verificar a presença dos documentos principais.
* [x] Incluir `data/applications.json` no `.gitignore`, além do bloqueio de rastreamento já coberto pelo `Data Guard`.
  Presente no `.gitignore` raiz (`data/applications.json`).

## Visão geral

O Import Vagas está evoluindo de uma plataforma conversacional de carreira para um copiloto completo de candidatura.

A proposta é permitir que o usuário consiga:

1. Criar ou atualizar seu perfil profissional.
2. Enviar ou analisar seu currículo.
3. Buscar vagas compatíveis.
4. Colar a descrição de uma vaga específica.
5. Comparar a vaga com o currículo.
6. Identificar lacunas reais.
7. Receber sugestões seguras de melhoria no currículo.
8. Gerar um PDI personalizado para aquela vaga.
9. Treinar entrevista com base na vaga analisada.

---

# 1. O que já temos hoje

## 1.1 Estrutura geral do projeto

* [x] Frontend em React com TypeScript e Vite.
* [x] Backend em FastAPI.
* [x] Comunicação via WebSocket para chat e streaming.
* [x] Rotas REST para dados auxiliares.
* [x] Persistência local em arquivos Markdown dentro de `data/`.
* [x] Estrutura multiagente.
* [x] Interface com estética dark tech.
* [x] Painel lateral de perfil.
* [x] Componentes organizados para chat, perfil, status e entrada de mensagens.
* [x] Fallbacks locais para manter fluxos funcionando sem LLM ou Firecrawl.

---

## 1.2 Maestro

O Maestro é o orquestrador principal do sistema.

### O que temos

* [x] Inicialização do fluxo conversacional.
* [x] Leitura do estado salvo.
* [x] Quiz de perfil com sete perguntas.
* [x] Retomada de quiz incompleto.
* [x] Consolidação do perfil profissional.
* [x] Identificação de funções alvo.
* [x] Roteamento para Scout, Curator e Coach.
* [x] Controle da entrevista simulada.
* [x] Tratamento de erros completo.
  Fechado em 2026-06-24: Coach e rotas tratam erros explicitamente; a falha
  parcial/degradada do Firecrawl no Scout agora é exposta
  (`busca_degradada`/`aviso_degradacao` + banner no `ScoutReport`).
* [x] Manutenção do estado da sessão.

### O que iremos acrescentar

* [x] Roteamento para análise de descrição de vaga.
  Opção **E** do menu abre `await_job_description`: o usuário cola a vaga, o
  Maestro analisa, salva `job-description-analysis.md` e invalida downstream.
* [x] Roteamento para comparação vaga x currículo.
  Opção **F** roda `ResumeMatcher.match` e salva `resume-match-report.md`.
* [x] Roteamento para sugestões seguras de currículo.
  Opção **G** roda `ResumeTailor.generate` e salva `resume-tailoring-suggestions.md`.
* [x] Roteamento para geração de PDI por vaga.
  Opção **H** roda `PdiGenerator.generate` e salva `pdi-plan.md`.
* [x] Roteamento para entrevista baseada em uma vaga específica.
  O Coach agora despacha usando a vaga analisada (`job-description-analysis.md`)
  quando disponível, com fallback no Scout. Falta ainda o roteamento
  conversacional do Maestro para colar/analisar a vaga (item separado da auditoria).
* [x] Etapa de reconciliação entre perfil, currículo e vaga.
  Opção **I** roda `Reconciler.reconcile` e salva `reconciliation.md`.
* [ ] Mensagens mais claras quando houver conflito entre dados do usuário.
* [x] Limpar também currículo, vaga analisada, match, tailoring e PDI ao refazer o diagnóstico.
  `_reset_data_files` remove todos os artefatos dependentes (coberto por
  `test_maestro_reset.py`).

---

## 1.3 Scout

O Scout é o agente responsável pela busca de oportunidades. A análise de descrição colada, o match e o PDI são módulos separados no backend.

### O que temos

* [x] Busca de oportunidades.
* [x] Extração de requisitos.
* [x] Cálculo de aderência.
* [x] Comparação de habilidades técnicas.
* [x] Comparação de soft skills.
* [x] Identificação de requisitos recorrentes.
* [x] Priorização de candidatura.
* [x] Dicas iniciais para currículo.
* [x] Fallback com oportunidades simuladas quando a busca real não retorna resultados.

### Inteligência de vaga implementada em módulos separados

* [x] Análise de descrição de vaga colada pelo usuário.
* [x] Extração de título da vaga.
* [x] Extração de empresa, quando existir.
* [x] Extração de senioridade provável.
* [x] Extração de modalidade.
* [x] Extração de localização.
* [x] Extração de hard skills.
* [x] Extração de soft skills.
* [x] Extração de ferramentas.
* [x] Extração de responsabilidades.
* [x] Extração de requisitos obrigatórios.
* [x] Extração de requisitos desejáveis.
* [x] Extração de palavras-chave principais.
* [x] Criação de alertas sobre vaga pouco clara, vaga sênior ou requisitos críticos.
* [x] Persistência em `data/job-description-analysis.md`.
* [x] Comparar a descrição da vaga com o currículo analisado.
* [x] Separar evidências fortes, evidências parciais e requisitos ausentes.
* [x] Gerar score de aderência entre vaga e currículo.
* [x] Gerar relatório em `data/resume-match-report.md`.

---

## 1.4 Curator

O Curator é o agente responsável por trilhas de aprendizado. O PDI por vaga é gerado separadamente por `PdiGenerator`.

### O que temos

* [x] Normalização de lacunas detectadas pelo Scout.
* [x] Priorização de habilidades faltantes.
* [x] Recomendações gratuitas.
* [x] Recomendações com referências oficiais.
* [x] Sugestão de cursos pagos quando fizer sentido.
* [x] Sugestão de projetos práticos.
* [x] Organização entre “estudar agora” e “estudar depois”.
* [x] Base interna de recomendações quando o Firecrawl não está disponível.

### PDI implementado em módulo separado

* [x] Gerar PDI personalizado a partir do relatório vaga x currículo.
* [x] Separar plano por prazo:

  * [x] 7 dias;
  * [x] 30 dias;
  * [x] 60 dias.
* [x] Classificar lacunas por impacto na candidatura.
* [x] Indicar quais lacunas impedem candidatura imediata.
* [x] Indicar quais lacunas podem ser estudadas depois.
* [x] Sugerir projetos práticos para gerar evidências reais.
* [x] Sugerir entregáveis para GitHub, LinkedIn e currículo.
* [x] Salvar o PDI em `data/pdi-plan.md`.

---

## 1.5 Coach

O Coach é o agente responsável pela entrevista simulada.

### O que temos

* [x] Entrevista estruturada em cinco perguntas.
* [x] Perguntas técnicas e comportamentais.
* [x] Feedback por resposta.
* [x] Avaliação final.
* [x] Identificação de áreas de melhoria.
* [x] Fallback local quando o LLM não responde.
* [x] Persistência em `data/interview-session.md`.

### O que iremos acrescentar

* [x] Gerar entrevista a partir da descrição da vaga analisada.
  O Coach agora lê `job-description-analysis.md` (além de `job-search-results.md`
  e `course-recommendations.md`); o `interview_context` prioriza a vaga analisada.
* [x] Usar o relatório de aderência como contexto.
  `resume-match-report.md` agora é lido pelo Coach (enriquece o brief).
* [x] Criar perguntas técnicas com base nas lacunas.
  Passo 2 usa requisitos obrigatórios + hard skills da vaga; passo 4 usa
  responsabilidades da vaga + lacunas críticas do match (fallback Scout/perfil).
* [x] Criar perguntas comportamentais com base nas responsabilidades da vaga.
* [ ] Adaptar feedback ao nível de aderência do usuário.
  Pendente: o feedback ainda é genérico (calibração do LLM via brief).
* [ ] Sugerir respostas mais estratégicas com base no currículo.
* [x] Preparar roteiro de entrevista para vaga específica.
  Gate relaxado: a entrevista inicia com Scout **ou** vaga analisada.

---

# 2. O que já temos na parte de currículo

## 2.1 Análise de currículo

### O que temos

* [x] Upload de currículo em PDF, DOCX ou TXT.
* [x] Análise heurística do currículo.
* [x] Extração de habilidades técnicas.
* [x] Extração de soft skills.
* [x] Sugestão de atualização do perfil.
* [x] Persistência em `data/resume-analysis.md`.

### O que iremos acrescentar

* [x] Comparar currículo com descrição de vaga específica.
* [x] Identificar palavras-chave da vaga que já aparecem no currículo.
* [x] Identificar palavras-chave ausentes.
* [x] Identificar experiências que podem ser melhor destacadas.
* [x] Identificar informações fracas ou pouco claras.
* [x] Criar sugestões seguras de melhoria.
* [x] Criar seção “Não afirmar ainda”.
* [x] Gerar `data/resume-tailoring-suggestions.md`.

---

## 2.2 Sugestões seguras de currículo

### O que temos

* [x] Base inicial para análise de currículo.
* [x] Dados suficientes para cruzar currículo com vaga futuramente.

### O que iremos acrescentar

* [x] Sugestão de novo resumo profissional.
* [x] Sugestão de reorganização da seção de habilidades.
* [x] Sugestão de projetos a destacar.
* [x] Sugestão de experiências a reposicionar.
* [x] Sugestão de palavras-chave para inserir.
* [x] Separação entre:

  * [x] pode destacar melhor;
  * [x] pode reposicionar;
  * [x] precisa estudar primeiro;
  * [x] não afirmar ainda.
* [x] Botão para copiar sugestões.
* [x] Avisos para evitar exageros ou informações falsas no relatório de aderência.

---

# 3. O que já temos na análise de vaga

## 3.1 Analisador de descrição de vaga

### O que temos

* [x] Componente para colar descrição da vaga.
* [x] Validação de entrada mínima.
* [x] Botão para analisar descrição.
* [x] Rota `POST /api/job-description/analyze`.
* [x] Rota `GET /api/data/job-description`.
* [x] Heurísticas locais para análise.
* [x] Persistência em `data/job-description-analysis.md`.
* [x] Exibição do resultado no frontend.
* [x] Tratamento de entrada inválida com erro HTTP 400.
* [x] Validação com lint, build e backend.

### O que iremos acrescentar

* [x] Botão “Comparar com meu currículo”.
* [x] Integração com `data/resume-analysis.md`.
* [x] Geração do relatório de aderência.
* [x] Exibição de score geral.
* [x] Exibição de palavras-chave encontradas.
* [x] Exibição de palavras-chave ausentes.
* [x] Exibição de lacunas críticas.
* [x] Exibição de sugestões seguras.
* [x] Exibição da seção “Não afirmar ainda”.

---

# 4. O que iremos acrescentar na esteira de candidatura

## 4.1 Comparação vaga x currículo

### Objetivo

Criar uma etapa que mostre o quanto o currículo do usuário está aderente à vaga analisada.

### O que será acrescentado

* [x] Criar módulo de comparação entre vaga e currículo.
* [x] Ler `data/job-description-analysis.md`.
* [x] Ler `data/resume-analysis.md`.
* [x] Normalizar aliases de habilidades.
* [x] Comparar hard skills.
* [x] Comparar soft skills.
* [x] Comparar ferramentas.
* [x] Comparar palavras-chave.
* [x] Comparar senioridade e área.
* [x] Separar evidências em:

  * [x] evidência forte;
  * [x] evidência parcial;
  * [x] ausente.
* [x] Calcular score geral.
* [x] Gerar nível de prontidão.
* [x] Gerar recomendações seguras.
* [x] Gerar alertas.
* [x] Salvar resultado em `data/resume-match-report.md`.
* [x] Criar rota `POST /api/resume-match/analyze`.
* [x] Criar rota `GET /api/data/resume-match`.
* [x] Criar interface para visualizar o relatório.

---

## 4.2 Relatório de aderência

### Objetivo

Criar um documento simples e claro que explique o quanto o currículo conversa com a vaga.

### O que será acrescentado

* [x] Score geral de aderência.
* [x] Nível de prontidão.
* [x] Evidências fortes.
* [x] Evidências parciais.
* [x] Requisitos ausentes.
* [x] Palavras-chave encontradas.
* [x] Palavras-chave ausentes.
* [x] Pontos fortes para a vaga.
* [x] Lacunas críticas.
* [x] Sugestões seguras para melhorar o currículo.
* [x] Seção “Não afirmar ainda”.
* [x] Próximos passos recomendados.

---

## 4.3 Sugestões de currículo adaptado

### Objetivo

Ajudar o usuário a melhorar o currículo para uma vaga específica sem inventar experiência.

### O que será acrescentado

* [x] Gerar sugestões para resumo profissional.
* [x] Gerar sugestões para habilidades.
* [x] Gerar sugestões para projetos.
* [x] Gerar sugestões para experiências.
* [x] Mostrar palavras-chave que podem ser adicionadas com segurança.
* [x] Mostrar termos que precisam de evidência antes de entrar no currículo.
* [x] Permitir copiar sugestões.
* [x] Salvar em `data/resume-tailoring-suggestions.md`.

---

## 4.4 PDI personalizado por vaga

### Objetivo

Transformar as lacunas entre vaga e currículo em plano de desenvolvimento individual.

### O que será acrescentado

* [x] Gerar PDI com base no `resume-match-report.md`.
* [x] Separar lacunas por prioridade.
* [x] Criar plano de 7 dias.
* [x] Criar plano de 30 dias.
* [x] Criar plano de 60 dias.
* [x] Sugerir estudos gratuitos.
* [x] Sugerir documentação oficial.
* [ ] Sugerir cursos pagos apenas quando fizer sentido.
  Único sub-item do PDI ainda em aberto; hoje só há estudos gratuitos e oficiais.
* [x] Sugerir projetos práticos.
* [x] Sugerir entregáveis para portfólio.
* [x] Sugerir ajustes futuros no currículo.
* [x] Salvar em `data/pdi-plan.md`.
* [x] Integrar o componente `PdiPlan` ao fluxo visível do frontend.
* [x] Atualizar a etapa PDI da pipeline com estado, leitura e ação reais.

---

## 4.5 Entrevista baseada na vaga

### Objetivo

Fazer o Coach preparar o usuário para uma vaga real, não apenas para uma entrevista genérica.

### O que será acrescentado

* [x] Usar a descrição da vaga como contexto.
  O Coach lê `job-description-analysis.md` e o `interview_context` prioriza a
  vaga analisada (título + empresa) antes do Scout.
* [x] Usar o relatório de aderência como contexto.
  O Coach lê `resume-match-report.md` (score, nível de prontidão, lacunas).
* [x] Criar perguntas técnicas baseadas nos requisitos.
* [x] Criar perguntas comportamentais baseadas nas responsabilidades.
* [x] Criar perguntas sobre lacunas críticas.
* [ ] Gerar feedback direcionado.
  Pendente: calibração do feedback do LLM pelo nível de aderência.
* [ ] Criar plano de melhoria após a entrevista.

---

# 5. Consistência entre perfil, currículo e vaga

## O que temos

* [x] Perfil salvo em `data/user-profile.md`.
* [x] Análise de currículo salva em `data/resume-analysis.md`.
* [x] Análise de vaga salva em `data/job-description-analysis.md`.
* [x] Possibilidade de divergência entre perfil declarado e currículo analisado.

## O que iremos acrescentar

* [x] Detectar conflito entre perfil e currículo.
* [x] Detectar conflito entre currículo e vaga.
* [x] Detectar conflito entre perfil e vaga.
* [x] Permitir escolher foco da candidatura.
  `focus` em `POST /api/reconciliation/analyze` ou linha no perfil.
* [x] Permitir usar dados do currículo como base.
  `PUT /api/reconciliation/focus` com `focus="curriculo"` persiste a escolha no perfil.
* [x] Permitir usar dados do perfil como base.
  `PUT /api/reconciliation/focus` com `focus="perfil"`.
* [x] Permitir usar a vaga como foco principal.
  `PUT /api/reconciliation/focus` com `focus="vaga"` (default).
* [ ] Atualizar perfil somente com confirmação do usuário.
* [x] Normalizar habilidades antes de qualquer cálculo de aderência.

---

# 6. Governança de dados locais e privacidade

## O que temos

* [x] Persistência local em Markdown dentro de `data/`.
* [x] `data/` contém estado de execução, perfil, currículo analisado, resultados e relatórios gerados.
* [x] Risco identificado: o repositório remoto é público, então arquivos reais de `data/` podem expor informações pessoais ou dados de candidatura se forem commitados.

## O que iremos acrescentar

* [x] Definir os arquivos gerados em `data/` como estado local privado.
* [x] Adicionar `data/*.md` ao `.gitignore` para impedir novos artefatos locais no Git.
* [x] Remover do rastreamento os arquivos reais de runtime, preservando a geração local.
* [x] Manter somente `data/README.md` rastreado e permitir exemplos sanitizados `*.example.md`.
* [x] Documentar em `data/README.md` que a pasta armazena estado local e pode conter dados sensíveis.
* [x] Ignorar também `data/applications.json` e futuros formatos de runtime não Markdown.
  `data/applications.json` já está no `.gitignore`.

---

# 7. Dados reais com Firecrawl

## O que temos

* [x] Estrutura prevista para uso do Firecrawl.
* [x] Integracao externa migrada do CLI para o SDK oficial `firecrawl-py`.
* [x] Chamadas de busca e scrape executadas fora do Event Loop com `asyncio.to_thread`.
* [x] Fallback local quando Firecrawl nao retorna resultados ou fica temporariamente indisponivel.
* [x] Busca simulada funcionando.
* [x] Recomendacoes internas funcionando.
* [x] Logs estruturados de sucesso/falha com `session_id`.

## O que iremos acrescentar

* [ ] Testar busca real de cursos com o SDK em ambiente com chave valida.
* [ ] Revalidar a busca completa pelo Scout com backend reiniciado e abertura do link de vaga no navegador.
* [ ] Validar salarios.
* [ ] Validar requisitos extraidos.
* [ ] Registrar origem dos dados.
* [x] Tratar resultados parciais tambem na UX do frontend.
  Banner de busca degradada no `ScoutReport`, distinto do banner de simulação.
* [x] Tratar ausencia de resultados reais sem quebrar o fluxo por meio de fallback local.
* [x] Expor ao usuario as falhas parciais do Firecrawl em vez de descarta-las silenciosamente.
  Fechado em 2026-06-24: além da simulação total (já exposta), o Scout sinaliza
  busca degradada (`status_busca: real_degraded`, `busca_degradada: true`,
  `aviso_degradacao`) quando a query específica falha e só a ampla recupera; o
  front mostra banner próprio.

---

# 8. Testes e validacao

## O que temos

* [x] Validação atual de build.
* [x] Validação manual de lint.
* [x] Validação manual do backend.
* [x] Reexecutar teste integrado da análise de descrição de vaga.
* [x] Tratamento de entrada inválida na análise de vaga.

## O que iremos acrescentar

### Backend

* [x] Testar análise de descrição de vaga de forma reproduzível.
  `test_job_description_analyzer.py` + `test_job_description_route.py` (análise,
  round-trip Markdown, validadores e rota REST com persistência).
* [x] Testar comparação vaga x currículo de forma reproduzível.
  `test_resume_matcher.py` + `test_backend_route_prerequisites.py::test_match_*`.
* [x] Testar ausência de currículo.
  `test_match_sem_curriculo_retorna_400`.
* [x] Testar ausência de vaga.
  `test_match_sem_vaga_valida_retorna_400`.
* [x] Testar geração de Markdown.
  `*_report_roundtrip` / `*_markdown_roundtrip` no matcher, vaga e reconciliação.
* [x] Testar normalização de aliases.
  `test_reconcile_normaliza_foco_explicito_com_acento` + helpers do matcher.
* [x] Testar cálculo de score.
  `test_match_score_fica_entre_0_e_100` e `test_reconcile_score_fica_entre_0_e_100`.
* [x] Testar geração do PDI personalizado.
  `test_pdi_com_artefatos_validos_persiste_e_le_latest`.
* [x] Testar ausência de currículo, vaga, relatório de aderência e sugestões de currículo no PDI.
  `test_pdi_sem_sugestoes_retorna_400` e `test_pdi_validators.py` rejeitam entradas inválidas.
* [x] Testar leitura de `data/pdi-plan.md` pela API.
  `test_pdi_com_artefatos_validos_persiste_e_le_latest` cobre `GET /api/pdi/latest`.
* [x] Testar concorrência e atomicidade de escrita.
  `test_concurrency.py` + `test_applications.py::test_escrita_atomica_*`.
* [x] Testar isolamento multiusuário por `session_id`.
  `test_session.py` + `test_agents_paths.py`.

### Frontend

* [x] Testar renderização do analisador de vaga.
* [x] Testar botão de comparação com currículo.
* [x] Testar loading.
* [x] Testar mensagens de erro.
* [x] Testar renderização de tags.
* [x] Testar responsividade básica.

### Fluxo completo

* [x] Enviar currículo.
* [x] Analisar currículo.
* [x] Colar descrição da vaga.
* [x] Analisar vaga.
* [x] Comparar vaga com currículo.
* [x] Gerar relatório de aderência.
* [x] Gerar sugestões seguras.
* [x] Gerar PDI.
* [x] Iniciar entrevista baseada na vaga.
  O Coach consome `job-description-analysis.md` e `resume-match-report.md`
  (além do Scout/Curator). As perguntas técnicas e de cenário priorizam a vaga
  analisada e as lacunas do match; o `interview_context` prefere a vaga colada.
  Gate relaxado: inicia com Scout **ou** vaga analisada.

---

# 9. Performance e organização

## O que temos

* [x] Build funcionando.
* [x] Interface responsiva validada nos viewports prioritários.
  Validado sem scroll horizontal em 1366x768, 1440x900, 768x1024, 390x844 e 360x800.
* [ ] Lazy loading completo dos módulos principais.
  Situação atual: quiz, candidaturas, analisador de vaga e chat são lazy; pipeline e upload são carregados imediatamente.
* [x] Medição atual do bundle principal.
  Bundle principal: 357,78 kB; ChatTerminal permanece em chunk separado de 171,20 kB.

## O que iremos acrescentar

* [ ] Investigar bundle principal.
* [ ] Aplicar lazy loading em todos os módulos principais da esteira.
* [x] Separar o relatório de aderência em componente próprio.
* [ ] Evitar duplicação de tipos TypeScript.
* [ ] Revisar CSS adicionado.
* [ ] Garantir consistência visual entre módulos.
* [ ] Revisar nomes de arquivos e responsabilidades.

---

## 10. Documentação

### O que temos

* [x] README inicial do projeto.
* [x] Explicação da arquitetura multiagente.
* [x] Explicação de instalação e execução.
* [x] Explicação do fluxo atual de uso.

### O que iremos acrescentar

* [x] Atualizar a proposta do produto.
  Coberto pelo README (seção "O que é").
* [x] Documentar a esteira de candidatura.
  Coberto pelo README (Funcionalidades + Fluxo de uso A–I).
* [x] Documentar análise de descrição de vaga.
  Coberto pelo README.
* [x] Documentar comparação vaga x currículo.
  Coberto pelo README.
* [x] Documentar sugestões seguras de currículo.
  Coberto pelo README.
* [x] Documentar PDI personalizado.
  Coberto pelo README.
* [x] Documentar arquivos gerados em `data/`.
  Coberto pelo README (Estrutura do projeto + nota de privacidade).
* [ ] Documentar novas rotas REST.
* [ ] Criar seção de roadmap.
* [ ] Criar seção de decisões de arquitetura.
* [ ] Adicionar prints futuramente.
* [x] Atualizar `README.md` com currículo, filtro de data, análise de vaga, match, sugestões, PDI, candidaturas, Career Arcade Pipeline e privacidade de `data/`.
* [ ] Revisar `README.md` para alinhar versões exibidas de React/TypeScript e completar a documentação de rotas REST.
  Parcial (2026-06-26): badges e seção Tecnologias alinhados a React 19 / TypeScript 6 conforme `package.json`; falta apenas enumerar as rotas REST no README.
* [x] Atualizar `plano.md`, que ainda descreve escopo e quantidade de perguntas antigos.
  Feito em 2026-06-26: suíte 73→150 testes, quiz 5→7 perguntas, menu A–D → esteiras A–I e marcos (Docker/CI/erros 422-500) marcados.
* [x] Atualizar `docs/project-update-report.md` com os commits, validações e estado da entrevista atuais.
  Feito em 2026-06-26: novo levantamento no topo (commits 7ec128b/21fda2b/a18e469/520a931, 150 backend + 26 frontend, entrevista calibrada pela vaga).

---

## 11. Ordem prática de evolução

## Etapa atual

* [x] **Garantir geração de `resume-analysis.md` durante upload/análise de currículo.**
  Validado com upload TXT real em 2026-06-14.
* [x] Integrar o componente `PdiPlan` ao frontend visível e à pipeline.
* [x] Adicionar rota de leitura para `resume-analysis` em `data_files.py`.
* [x] Conectar a entrevista à vaga analisada e ao match.
  Coach lê `job-description-analysis.md` e `resume-match-report.md`; testes em
  `test_coach.py` cobrem brief, perguntas de fallback e gate relaxado.
* [x] Criar testes mínimos dos fluxos críticos.
  Suíte com 120 testes cobrindo agentes, rotas REST, WebSocket/estado, concorrência e isolamento.

## Base concluída

* [x] Corrigir lint do ProfilePanel.
* [x] Criar análise de descrição de vaga.
* [x] Criar rota de análise de vaga.
* [x] Criar interface para colar descrição.
* [x] Salvar análise em Markdown.

* [x] Criar comparação vaga x currículo.
* [x] Gerar `resume-match-report.md`.
* [x] Exibir relatório no frontend.
* [x] Tratar ausência de currículo ou vaga.
* [x] Validar lint, build e backend em conjunto.

## Etapas seguintes

* [x] Garantir que `resume-analysis.md` seja criado durante análise de currículo.
* [x] Adicionar rota GET para `resume-analysis` em `data_files.py`.
* [x] Disponibilizar visualização do PDI no frontend.
* [x] Conectar Coach à vaga analisada e ao relatório de aderência.
* [x] Resolver divergência entre perfil, currículo e vaga.
  Agente `reconciliation.py` + rota `/api/reconciliation/*` (detecta conflitos nos
  três pares e respeita o foco da candidatura).
* [x] Configurar dados reais com Firecrawl (`FIRECRAWL_API_KEY`).
* [x] Separar arquivos locais de `data/` do que deve ser versionado (privacidade).
* [x] Criar testes mínimos automatizados.
  120 testes em `backend/tests/`.
* [ ] Atualizar documentação (README, plano.md, project-update-report.md).
  2026-06-26: `plano.md` e `docs/project-update-report.md` atualizados; README com versões React/TS alinhadas — resta enumerar as rotas REST no README.

---

## 12. Definição de pronto

Uma etapa só deve ser considerada pronta quando:

* [ ] A funcionalidade aparece no frontend.
* [x] A rota backend está registrada corretamente.
* [x] O arquivo Markdown correspondente é gerado.
* [x] Os erros comuns de pré-requisitos são tratados nas novas rotas.
* [x] O lint passa.
* [x] O build passa.
* [x] O backend importa ou compila corretamente.
* [ ] Existe uma forma clara de testar manualmente.
* [ ] Nenhum fluxo anterior foi quebrado.
* [ ] A documentação foi atualizada quando necessário.

---

## 13. Career Arcade Pipeline

## Identidade e jornada

* [x] Criar tokens de cor para a identidade arcade retrô-futurista.
* [x] Aplicar fundo sutil com referência a labirinto e pellets.
* [x] Criar pipeline visual com Currículo, Vaga, Match, Sugestões, PDI e Entrevista.
* [x] Exibir status com texto para não depender apenas de cor.
* [x] Liberar a ação do PDI somente após a conclusão das sugestões seguras.
* [x] Mostrar PDI como concluído quando `/api/data/pdi` contém um plano válido.
* [x] Padronizar botões primários, secundários e estados de alerta.
* [x] Criar cards e tags reutilizáveis para os relatórios.
* [x] Padronizar loading, erro e sucesso.
* [x] Melhorar microcopy da análise de vaga, match e sugestões seguras.
* [x] Atualizar o ProfilePanel para usar tags semânticas.

## Responsividade e QA

* [x] Preparar pipeline horizontal para desktop.
* [x] Preparar pipeline em grade para notebook e tablet.
* [x] Preparar pipeline vertical para mobile.
* [x] Reduzir intensidade do fundo arcade no mobile.
* [x] Criar `docs/frontend-qa-checklist.md`.
* [x] Aplicar lazy loading ao terminal de chat.
* [x] Executar checklist visual completo em navegadores reais.
* [x] Executar a rodada final de QA visual e acessibilidade em Chrome e Edge.
* [x] Corrigir a sidebar para manter navegação fixa e perfil rolável sem cortes.
* [x] Validar ausência de scroll horizontal nos cinco viewports prioritários.

---

## Status de Implementação Detalhado

## Arquitetura completa validada

### Backend (FastAPI + Python)

* [x] 30 endpoints HTTP, 1 WebSocket e 4 rotas automáticas de documentação registrados
* [x] 9 agentes especializados implementados
* [x] WebSocket para chat em tempo real
* [x] Persistência em arquivos Markdown
* [x] Tratamento de erros HTTP estruturado
* [x] Normalização de habilidades e aliases
* [x] Fallbacks locais para Firecrawl

### Frontend (React 19 + TypeScript + Vite)

* [x] 15+ componentes implementados
* [x] Pipeline visual Career Arcade
* [x] Sistema responsivo validado (8 resoluções)
* [x] Acessibilidade (WCAG) validada
* [x] Lazy loading do terminal de chat
* [x] Temas dark tech aplicados
* [x] Tratamento de estados (loading, erro, sucesso)

### Fluxos principais implementados

* [x] Diagnóstico de perfil com quiz
* [x] Upload e análise de currículo
* [x] Análise de descrição de vaga
* [x] Comparação vaga x currículo (match)
* [x] Sugestões seguras de currículo
* [x] Geração de PDI personalizado
* [x] Entrevista simulada com Coach
* [x] Busca de vagas com Scout
* [x] Trilhas de aprendizado com Curator

## Bloqueadores críticos para produção

### 1. ~~Arquivo `resume-analysis.md` não é gerado~~ ✅ RESOLVIDO

**Status:** RESOLVIDO em 2026-06-14

**Descoberta:**

- O código JÁ gerava o arquivo corretamente em `resume.py` linha 548
- O problema era a **ausência da rota de leitura** em `data_files.py`

**Correções aplicadas:**

* ✅ Adicionado endpoint `GET /api/data/resume-analysis` em `data_files.py`
* ✅ Pipeline atualizada para ler o arquivo via API
* ✅ API passou a ser a fonte principal; `localStorage` obsoleto é removido quando o artefato não existe
* ✅ Validado: lint e build passando sem erros

### 2. ~~Firecrawl estava dependente de CLI~~ RESOLVIDO

**Status:** RESOLVIDO em 2026-06-17

**Descoberta:**

* O CLI funcionava em alguns ambientes, mas criava fragilidade operacional por depender de `subprocess`, PATH/PATHEXT e instalacao global.
* No Windows, essa dependencia podia gerar travamentos ou fallback silencioso.
* O SDK oficial `firecrawl-py` ja estava disponivel no backend.

**Correcoes aplicadas:**

* [x] Criado `backend/firecrawl_client.py` com `FirecrawlApp`.
* [x] `Scout` e `Curator` migrados para o SDK, sem chamadas de sistema.
* [x] `search` e `scrape` rodam com `asyncio.to_thread`, preservando o Event Loop.
* [x] Falhas de API/rede sao logadas com `session_id` e reempacotadas como falhas controladas.
* [x] Fallbacks locais continuam funcionando.
* [x] Validado com `pytest`: 73 testes passando.

### 3. ~~Componente PDI nao esta integrado a interface~~ RESOLVIDO

**Status:** RESOLVIDO em 2026-06-14

**Correções aplicadas:**

* `PdiPlan.tsx` é carregado sob demanda em um modal acessível.
* Pipeline libera a ação do PDI após a conclusão das sugestões seguras.
* Plano salvo é recuperado por `GET /api/pdi/latest`.
* Geração bem-sucedida atualiza imediatamente o estado da pipeline.

**Validações executadas:**

* [x] `npm run lint`
* [x] `npm run build`
* [x] `py_compile` e importação do FastAPI com 27 rotas.
* [x] Round-trip automatizado entre dados estruturados e `pdi-plan.md`.
* [x] Validar o modal e a geração completa no Chrome em `1366x768` e `390x844`.
* [x] Validar estado vazio, erro de geração, persistência e ausência de overflow horizontal.

### 4. ~~Rota de leitura para resume-analysis ausente~~ ✅ RESOLVIDO

**Status:** RESOLVIDO em 2026-06-14 (mesmo commit do item 1)

## Melhorias recomendadas (não bloqueantes)

### Privacidade e dados locais

* [x] Adicionar `data/*.md` ao `.gitignore` (evitar commit de dados pessoais)
* [x] Remover arquivos de runtime do rastreamento do Git
* [x] Manter `data/README.md` e permitir exemplos sanitizados `*.example.md`
* [x] Documentar em `data/README.md` que `data/` contém estado local potencialmente sensível

### Testes automatizados

* [x] Criar testes unitarios para agentes principais
  Scout, Curator, matcher, validadores de PDI/tailor e reconciliação (120 testes).
* [x] Criar testes de integracao para rotas criticas
  `test_backend_route_prerequisites.py` cobre upload, match, tailoring e PDI via TestClient.
* [ ] Criar testes E2E para fluxo completo de candidatura
* [ ] Adicionar validação de schemas dos arquivos Markdown

### Documentação

* [x] Atualizar `README.md` com funcionalidades, artefatos e privacidade atuais
* [x] Atualizar `plano.md` com escopo e perguntas corretos (2026-06-26: 7 perguntas, menu A–I, 150 testes)
* [x] Atualizar `docs/project-update-report.md` com commits recentes (2026-06-26)
* [ ] Criar diagramas de fluxo de dados
* [ ] Documentar estrutura dos arquivos Markdown em `data/`

### Performance

* [ ] Aplicar lazy loading em todos os módulos principais
* [ ] Revisar tamanho do bundle (atual: 357,78 kB principal + 171,20 kB chat)
* [ ] Evitar duplicação de tipos TypeScript
* [ ] Otimizar imports e tree-shaking

### Configuração externa

* [x] Configurar `FIRECRAWL_API_KEY` no ambiente
* [x] Migrar busca de vagas do Firecrawl CLI para o SDK oficial
* [ ] Testar busca real de cursos com Firecrawl
* [ ] Revalidar o fluxo Scout/backend e a abertura da vaga no navegador
* [x] Expor falhas parciais do Firecrawl ao usuário (atualmente silenciosas)
  Fechado em 2026-06-24: simulação total + busca degradada sinalizadas com banner próprio no `ScoutReport`.

## Próximas features planejadas

### Coach conectado à vaga

* [x] Usar descrição da vaga como contexto
* [x] Usar relatório de aderência como contexto
* [x] Criar perguntas técnicas baseadas nos requisitos
* [x] Criar perguntas comportamentais baseadas nas responsabilidades
* [ ] Gerar feedback direcionado às lacunas identificadas
  Pendente: o brief já leva as lacunas ao LLM, mas o feedback ainda não é
  calibrado pelo nível de aderência.

### Reconciliação de dados

* [x] Detectar conflito entre perfil declarado e currículo analisado
* [x] Detectar conflito entre currículo e vaga
* [x] Detectar conflito entre perfil e vaga
* [x] Permitir escolher foco da candidatura (perfil vs currículo vs vaga)
* [ ] Atualizar perfil somente com confirmação do usuário

### Isolamento multiusuário

* [x] Implementar sessions ou user IDs
  `session_id` anônimo via header `X-Session-Id` e query string do WebSocket.
* [x] Separar dados por usuário em `data/sessions/{id}/`
  `SessionPaths` isola todos os artefatos por sessão.
* [x] Evitar sobrescrita de dados entre usuários simultâneos
  Coberto por `test_session.py` e `test_agents_paths.py`.
* [x] Adicionar lock em operações read-modify-write (ex: applications.json)
  `get_session_lock` + escrita atômica; `test_applications.py` valida.

---

## Auditoria de backend — 2026-06-23

Revisão que cruzou cada item `[ ]` do checklist contra o código real em
`backend/` e a suíte de testes (`112 passed`). Resultado:

### Concluído nesta auditoria (marcado `[ ]` → `[x]`)

* [x] Suíte automatizada de testes (16 arquivos em `backend/tests/`, 112 testes).
* [x] Cobertura da seção 8 (Backend): análise de vaga, match, ausência de
  currículo/vaga, round-trip Markdown, normalização de aliases, cálculo de
  score, PDI, leitura de `pdi-plan.md`, concorrência e isolamento.
* [x] `data/applications.json` no `.gitignore` (já estava).
* [x] Isolamento multiusuário (`session.py`) e lock/escrita atômica de
  `applications.json`.
* [x] CI roda a suíte na nuvem (`backend-ci.yml`, pipeline bloqueante).
* [x] Reset do Maestro limpa currículo, vaga, match, tailoring e PDI.
* [x] Reconciliação (detecção de conflitos nos três pares + foco).

### Realmente pendente (mantido `[ ]`)

**Gap funcional principal:**

* [x] **Coach conectado à vaga** — agora lê
  `job-description-analysis.md` e `resume-match-report.md` (além de Scout/Curator),
  prioriza a vaga analisada no `interview_context` e relaxa o gate para iniciar
  com Scout **ou** vaga analisada. Fechado em 2026-06-23 (spec do plano já
  removida; ver histórico do git); `test_coach.py` cobre a lógica pura.
* [x] **Roteamento conversacional do Maestro** para análise de vaga, match,
  tailoring, PDI e reconciliação — hoje só acessíveis por botões/REST.
  Fechado em 2026-06-23: opções **E**–**I** no menu (seção "Esteira de
  Candidatura"); `_handle_job_description_paste` + `_dispatch_resume_match` /
  `_dispatch_resume_tailoring` / `_dispatch_pdi` / `_dispatch_reconciliation` em
  `maestro.py`; `await_job_description` reconhecido em `chat.py`; cards E–I em
  `ChatInput.tsx`; `test_maestro_routing.py` cobre menu, gating e cadeia.

**Robustez / dados reais:**

* [x] Expor falhas parciais do Firecrawl ao usuário (hoje silenciosas).
  Fechado em 2026-06-24: a simulação total já era exposta ponta-a-ponta; agora o
  Scout também sinaliza busca **degradada** (`busca_degradada`/`aviso_degradacao`,
  `status_busca: real_degraded`) quando a query específica falha (erro/timeout) e
  só a ampla recupera, com banner próprio no `ScoutReport`.
* [ ] Validar salários e requisitos extraídos; registrar origem dos dados.
* [ ] Sugerir cursos pagos no PDI quando fizer sentido.
* [x] Leitura do foco pelos agentes match/tailor/PDI para pesar resultados.
  Fechado em 2026-06-24: os agentes recebem `focus` e priorizam o `next_steps`
  conforme a fonte (precedência body > perfil > "vaga" via `resolve_focus`).
* [x] Endpoint PUT/PATCH para setar o foco da candidatura.
  Fechado em 2026-06-24: `PUT /api/reconciliation/focus`.
* [ ] Migração de dados legados `data/*.md` → sessão.
* [ ] Normalizar links do `CuratorReport` (mesmo bug já corrigido no Scout).

**Infraestrutura:**

* [x] Dockerização (backend, frontend e `docker-compose.yml`).
* [ ] Testes do caminho real de LLM (tudo cai em fallback hoje).
* [ ] Testes E2E do fluxo completo + validação de schemas dos Markdown.
* [x] Atualizar `plano.md` e `project-update-report.md`.
  Feito em 2026-06-26.

## Coach conectado à vaga analisada — 2026-06-23

Sessão executada em 2026-06-23 implementando o item 1 da auditoria de backend
(spec do plano já removida; ver histórico do git). Conecta o Coach à descrição
da vaga analisada e ao relatório de aderência, fechando a "entrevista baseada na vaga".

* [x] `coach.py` lê `job-description-analysis.md` e `resume-match-report.md`
  (via parsers canônicos `analysis_from_markdown` / `match_report_from_markdown`).
* [x] `_build_interview_brief` reflete vaga (título, empresa, senioridade,
  responsabilidades, requisitos obrigatórios, hard skills, ferramentas) + match
  (score, nível de prontidão, lacunas críticas, requisitos ausentes, evidências).
  Fallback Scout/perfil intacto quando os artefatos faltam.
* [x] `_question_for_step` (passos 2 e 4) prioriza requisitos/responsabilidades da
  vaga e lacunas do match; cai no Scout/perfil quando os campos estão vazios.
* [x] `QUESTION_PLAN` dos passos 2 e 4 atualizado para citar vaga/match.
* [x] Maestro lê os dois artefatos em `_dispatch_coach_start` e `_handle_coach` e
  os repassa nas três chamadas a `coach.run`.
* [x] `interview_context` prioriza vaga analisada > Scout > funções alvo > default.
* [x] Gate relaxado: a entrevista inicia com Scout **ou** vaga analisada.
* [x] `test_coach.py` novo (8 testes) + fixture `match_markdown` no `conftest.py`.
* [x] `python -m py_compile` OK; `import main` OK; `pytest` em **120 passed**
  (era 112; +8 do Coach), sem regressões.

## Roteamento conversacional do Maestro — 2026-06-23

Sessão executada em 2026-06-23 implementando o item 2 da auditoria de backend
(`docs/plano-roteamento-maestro.md`). Expõe pelo chat os cinco agentes que
antes só eram acessíveis por botão/REST (análise de vaga, match, tailoring,
PDI e reconciliação), fechando o loop conversacional iniciado com o Coach.

* [x] `MENU_TEXT` reescrito em duas seções (Esteira de Carreira A–D e Esteira
  de Candidatura E–I), mantendo o estilo de moldura.
* [x] Imports dos cinco agentes + serializadores + validadores em `maestro.py`
  (aliases para evitar colisão dos `validate_*` repetidos entre módulos).
* [x] Novo branch `await_job_description` em `run()` e ramos E–I em `_handle_menu`.
* [x] Fluxo **E** (`_prompt_job_description` + `_handle_job_description_paste`):
  valida mínimo de 40 chars, analisa, salva o artefato, invalida downstream
  (match/tailoring/PDI, espelhando `routers/job_description.py`), resume no
  chat; "menu" cancela.
* [x] Dispatchers **F**–**I** (`_dispatch_resume_match`, `_dispatch_resume_tailoring`,
  `_dispatch_pdi`, `_dispatch_reconciliation`): validam pré-requisitos com os
  `validate_*` reusados, rodam o agente síncrono, persistem o artefato com o
  serializador `*_to_markdown` e resumem o resultado no chat.
* [x] `chat.py`: `await_job_description` incluído no conjunto que fixa
  `active_agent = "Maestro"` em `_apply_state_update`.
* [x] Frontend: `'await_job_description'` na união `SessionMode` (`types.ts`);
  `ChatInput.tsx` com duas seções e 9 cards E–I (ícones do `lucide-react`,
  acentos `match`/`tailor`/`pdi`/`recon`); composer aparece no modo colar com
  placeholder dedicado; `MODE_STATUS`/`MODE_LABEL` em `App.tsx`/`StatusBar.tsx`
  cobrem o novo modo.
* [x] `test_maestro_routing.py` (11 testes): menu E, vaga curta, vaga válida com
  invalidação, "menu" cancela, F/G/H/I bloqueando sem pré-requisitos, reconciliação
  completa e cadeia E→F→G→H→I de ponta a ponta.
* [x] `python -m py_compile` OK; `import main` OK; `pytest` em **135 passed**
  (era 124; +11 do roteamento), sem regressões.
* [x] `npm run lint` e `npm run build` passam.

## Dockerização — 2026-06-24

Sessão executada em 2026-06-24 implementando a containerização (item de
infraestrutura da auditoria de backend). Empacota backend, frontend e mock para
rodar com um comando, sem instalar Python/Node na máquina.

* [x] `backend/Dockerfile`: `python:3.12-slim`, deps de `requirements.txt` (wheels
  cp312, sem compilação), usuário `appuser` sem privilégios, `HEALTHCHECK` em
  `/health` e `uvicorn main:app --host 0.0.0.0`. Contexto de build na raiz do
  repo para incluir `personas/` e `skills/` (resolvidos por `config.py` em
  PROJECT_ROOT); `DATA_DIR`/`PERSONAS_DIR`/`SKILLS_DIR`/`LOG_DIR` fixados em `/app/*`.
* [x] `frontend/Dockerfile`: multi-stage `node:22-alpine` (`npm ci && npm run
  build`) → `nginx:1.27-alpine` servindo `dist/`.
* [x] `frontend/nginx.conf.template`: SPA com fallback para `index.html` + proxy
  reverso de `/api` e `/ws` (com upgrade de WebSocket) para `${BACKEND_UPSTREAM}`,
  resolvido em runtime pelo DNS do Docker (127.0.0.11). `NGINX_ENVSUBST_FILTER=^BACKEND_`
  preserva as variáveis nativas do Nginx (`$host`, `$uri`, etc.).
* [x] `docker-compose.yml`: serviços `backend` (API :8000, volume `backend-data`
  em `/app/data`, `env_file` opcional `backend/.env`), `frontend` (Nginx :8080) e
  `mock` (profile `mock`, :8001). `docker compose up --build` sobe o site em
  http://localhost:8080.
* [x] `.dockerignore` na raiz e em `frontend/` (excluem `.venv`, `node_modules`,
  `data/`, `logs/`, `**/.env` e caches; mantêm `personas/` e `skills/`).
* [x] README: nova seção "Rodar com Docker" (real e modo mock).
* [x] Validação possível sem Docker neste ambiente: `docker-compose.yml` parseado
  como YAML válido (3 serviços + volume `backend-data`); `npm run build` do
  frontend conclui (`vite build` → `dist/`, mesma etapa da imagem); suíte do
  backend em **135 passed**.
* [ ] Pendente: rodar `docker compose up --build` numa máquina com Docker para
  validar o build das imagens e o runtime ponta a ponta (Docker indisponível no
  ambiente desta sessão).

## Falha degradada do Firecrawl + foco da candidatura — 2026-06-24

Sessão executada em 2026-06-24 implementando a "Parte 2" do roadmap de backend:
(A) expor as falhas parciais do Firecrawl e (B) endpoint de foco da candidatura +
leitura do foco por match/tailor/PDI.

### Parte A — falha degradada do Firecrawl

Constatado que a **simulação total** já era exposta ponta-a-ponta (Scout emite
`fallback_simulado`/`fallback_reason`/`fallback_message`; o `ScoutReport` já
mostrava banner). O gap real era a **busca degradada-mas-real**: quando a query
específica falhava (erro/timeout) e só a query ampla recuperava vagas, o
`search_status` virava `real_success` silenciosamente.

* [x] `scout.py`: novo `status_busca: real_degraded` + `busca_degradada`/
  `aviso_degradacao` (dict `DEGRADED_MESSAGES`) quando a query específica falha
  por erro/timeout e a ampla recupera; `response_state` também vira "parcial".
* [x] Frontend: `parseScoutData` (ChatMessage.tsx) extrai `busca_degradada`/
  `aviso_degradacao`; `ScoutReport.tsx` mostra um banner de degradação distinto
  do banner de simulação (reusa as classes existentes, sem CSS novo).
* [x] `test_scout.py` (+2): busca degradada sinalizada; sucesso limpo não marca
  degradação.

### Parte B — foco da candidatura

* [x] `reconciliation.py`: `upsert_focus_line(profile, focus)` (+`FOCUS_PROFILE_KEY`)
  insere/atualiza a linha "Foco da candidatura:" no perfil sem duplicar.
* [x] `routers/common.py`: `resolve_focus(profile, explicit)` — precedência
  explícito > perfil > "vaga" (importa `normalize_focus`/`parse_focus`; sem ciclo).
* [x] `routers/reconciliation.py`: `PUT /api/reconciliation/focus` (valida via
  `normalize_focus` → 422 se inválido; perfil ausente/vazio → 400; escrita atômica
  sob lock de sessão).
* [x] `resume_matcher.py`, `resume_tailor.py`, `pdi_generator.py`: assinatura passa
  a aceitar `focus="vaga"`; helper `_focus_{match,tailor,pdi}_step` prepende uma
  linha focus-aware ao `next_steps` (aditivo — não mexe no score nem nos
  serializadores; round-trip intacto).
* [x] Routers `resume_match`/`resume_tailoring`/`pdi`: `focus` opcional no corpo;
  leem o perfil best-effort; `resolve_focus`; passam `focus` ao agente.
* [x] `test_focus.py` (novo, 13): `upsert_focus_line` (add/replace/inválido),
  `resolve_focus` (precedência), `PUT /focus` (200/422/400) e variação do
  `next_steps` por foco em match/tailor/PDI + rota de match com foco no corpo.

### Validação

* [x] `import main` OK (35 rotas; +1 `PUT /api/reconciliation/focus`).
* [x] `pytest` em **150 passed** (era 135; +15), sem regressões.
* [x] Frontend: `npm run lint` limpo, `npm run build` OK, `npm run test` em
  **25 passed** (ScoutReport/ChatMessage sem regressão).

## Foco da candidatura: loop fechado no frontend — 2026-06-24

Complemento da sessão da Parte 2. O seletor "Escolher o foco da candidatura"
(`ResumeMatchReport.tsx`) agora **persiste** a escolha no perfil via
`PUT /api/reconciliation/focus` (best-effort) ao clicar — então match/tailoring/
PDI passam a honrar o foco nas execuções seguintes (via `resolve_focus`). Antes,
o foco só ia para a reconciliação por requisição e não chegava aos outros agentes.

* [x] `handleFocusChange` em `ReconciliationStep` chama `PUT /focus` ao escolher
  (falha silenciosa: a reconciliação ainda envia o foco por requisição).
* [x] `main-flow.test.tsx`: novo teste garante que escolher o foco dispara o
  `PUT /api/reconciliation/focus` com `{focus}` correto.
* [x] Validado: `npm run lint` limpo, `npm run build` OK, `npm run test` em
  **26 passed** (+1).
