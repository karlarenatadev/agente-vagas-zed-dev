# Checklist consolidado — Import Vagas

Última consolidação: 2026-06-27

Referência do código analisado: `d14e2d1`

Validação atual: backend **229 passed** (`pytest -q`, rodadas P0 locais sobre `d14e2d1`, ainda não commitadas); frontend **48 passed** (`npm run test -- --run`, reexecutada na rodada de UI de confirmação de perfil); lint e build sem erros.

> Verificação de rodada — privacidade de `data/` e `applications.json`: confirmado que a pasta `data/` já está protegida no `.gitignore` (apenas `data/README.md` versionado, sem dados sensíveis) e que `applications.json` já trata JSON inválido/corrompido com HTTP 409, cria backup do arquivo corrompido, preserva o original e usa escrita atômica. Coberto por `backend/tests/test_applications.py`. Nenhuma mudança de comportamento foi necessária nesta rodada. Também foi removido um import morto em `ScoutReport.tsx` (`normalizeSafeHttpLink`, nunca usado) que quebrava o `tsc -b`; o `npm run build` voltou a passar.

Este arquivo substitui o histórico acumulado de checklists. Itens repetidos foram
unificados, entregas antigas foram agrupadas por domínio e as pendências foram
ordenadas por impacto.

# 1. Pendências priorizadas

## P0 — Críticas para produção

* [ ] **Bloqueado (ambiente externo — depende de chave/créditos do Firecrawl).** Validar o Firecrawl em condições reais, com chave e créditos:
  * executar busca completa de vagas pelo Scout;
  * executar busca real de cursos pelo Curator;
  * validar salários e requisitos extraídos;
  * registrar e exibir a origem dos dados;
  * confirmar a abertura de links reais de vagas no navegador.
* [ ] **Pendente (sem estrutura E2E e sem ambiente validado).** Criar testes E2E automatizados para a esteira completa:
  currículo → vaga → match → sugestões → PDI → entrevista → candidatura.
* [ ] **Parcial.** Validação de artefatos Markdown endurecida no consumo:
  ausente/vazio → HTTP 400; corrompido/binário/não-UTF-8 → HTTP 409 controlado
  (sem traceback, sem sobrescrita do arquivo), via helper reutilizável
  (`read_required` / `read_optional_text`) aplicado a match, sugestões, PDI e
  reconciliação (`/analyze` e `/latest`). A validação estrutural por tipo já
  existia (`validate_*` / `*_from_markdown`). Coberto por
  `backend/tests/test_artifact_corruption.py`. Pendente: validação de schema
  mais profunda e a matriz completa de falhas E2E.
* [ ] **Parcial.** Matriz de falhas coberta por testes automatizados:
  pré-requisitos REST ausentes (match sem vaga/currículo, sugestões sem match,
  PDI sem match/sugestões → HTTP 400 controlado) e artefatos corrompidos (→ 409)
  já cobertos; WebSocket agora coberto em
  `backend/tests/test_chat_websocket_failures.py` (state inicial + welcome
  conclui sem travar; JSON inválido → erro controlado; estado corrompido →
  fallback para sessão inicial; reconexão sem `replay` não reemite welcome;
  `replay=1` reemite o prompt sem avançar/duplicar estado; desconexão persiste
  estado sem estourar). Pendente (exige rede/processo real, não unitário):
  interrupção física do backend e reconexão real sob streaming longo — validar
  manualmente.
* [x] **Concluído (descarte lógico).** A sessão default agora usa
  `data/sessions/_default/`; artefatos de runtime ficam em
  `data/sessions/{session_id}/`. `data/*.md` soltos na raiz são tratados como
  legado e NÃO são consumidos automaticamente (exigem regeração na sessão);
  nenhum arquivo legado é apagado e `data/README.md` é preservado. Coberto por
  `backend/tests/test_session.py` e `backend/tests/test_session_default_isolation.py`.
* [x] **Confirmação de perfil (backend) concluída.** O upload de currículo não
  atualiza mais o perfil silenciosamente: retorna um preview não destrutivo
  (`profile_suggestions`, com `current_value`/`suggested_value`/`conflict`) e
  exige `POST /api/resume/apply-profile` com `confirm: true` para gravar apenas
  os campos aprovados. Análise de vaga e `reconciliation/analyze` não escrevem o
  perfil; `reconciliation/focus` segue como ação explícita do usuário. Coberto
  por `backend/tests/test_resume_profile_confirmation.py`. UI de confirmação
  implementada no frontend (`ProfileSuggestionConfirm`), exibida após a análise
  do currículo, com seleção por campo, estados de loading/sucesso/erro e opção
  de ignorar; coberta por
  `frontend/src/components/ProfileSuggestionConfirm.test.tsx`.

## P1 — Alta prioridade funcional

* [x] **Concluído.** Feedback calibrado: os prompts de avaliação e a avaliação final passam a citar score/nível de prontidão, conectar os pontos a melhorar às lacunas críticas e requisitos ausentes do match, e diferenciar problema técnico/comportamental/evidência; a resposta melhorada é ancorada apenas em evidências reais do currículo (sem inventar). Coberto por `backend/tests/test_coach.py`.
* [x] **Concluído.** Resposta melhorada ancorada em evidências reais e plano de preparação final priorizado pelas lacunas críticas/requisitos ausentes (com fallback local contextual quando o LLM falha). Quando não há match, o Coach não finge personalização e recomenda rodar o match. Coberto por `backend/tests/test_coach.py`.
* [x] **Concluído.** Helper compartilhado `frontend/src/lib/links.ts`
  (`normalizeHttpLink`) valida URLs http(s) e bloqueia
  `javascript:`/`data:`/`file:`/`mailto:`/`ftp:`/sem-esquema/vazio.
  `ScoutReport` (com gate de origem) e `CuratorReport` usam o MESMO helper; o
  Curator mostra “Link não disponível” para link inseguro/inválido e nunca
  renderiza `<a href>` inseguro. Cobertura: `frontend/src/lib/links.test.ts`,
  `frontend/src/components/CuratorReport.test.tsx`,
  `frontend/src/components/ScoutReport.test.tsx`.
* [ ] Criar teste automatizado para o pré-preenchimento do quiz a partir da
  análise do currículo.
* [ ] Melhorar as mensagens de conflito entre perfil, currículo e vaga,
  explicando qual fonte prevalece e por quê.
* [ ] Permitir cursos pagos no PDI somente quando agregarem valor e identificá-los
  claramente como opção complementar.
* [ ] Revalidar o auto-scroll para mensagens de erro e revisar os estados
  loading, vazio, erro e sucesso dos componentes restantes.

## P2 — Qualidade técnica e manutenção

* [ ] Eliminar checagens defensivas de mojibake espalhadas pelo Curator e Coach
  depois de garantir UTF-8 na origem e na persistência.
* [ ] Acompanhar o `PendingDeprecationWarning` emitido pelo Starlette por
  `import multipart` e migrar para `python_multipart` quando a cadeia de
  dependências permitir.
* [ ] Concluir o lazy loading dos módulos principais ainda carregados no bundle
  inicial.
* [ ] Revisar o tamanho do build atual:
  * bundle principal: 376,81 kB;
  * chunk do chat: 174,29 kB.
* [ ] Otimizar imports e tree-shaking.
* [ ] Eliminar duplicações de tipos TypeScript.
* [ ] Revisar CSS, nomes de arquivos e responsabilidades dos componentes para
  manter consistência visual e estrutural.

## P3 — Documentação e acabamento

* [ ] Enumerar no `README.md` as rotas REST atuais.
* [ ] Sincronizar `plano.md` com a recuperação visual de sessão já concluída e
  com a contagem atual de 221 testes backend.
* [ ] Documentar decisões arquiteturais relevantes:
  isolamento por sessão, escrita atômica, fallback de provedores e foco da
  candidatura.
* [ ] Criar um diagrama do fluxo de dados entre frontend, rotas, agentes e
  artefatos Markdown.
* [ ] Documentar os schemas atuais dos arquivos em `data/`.
* [ ] Adicionar capturas de tela atualizadas quando houver uma versão visual
  estável para publicação.

# 2. Entregas concluídas

## Atualizacao de Roadmap Tecnico (2026-06-17)

O backend passou por uma etapa de hardening e agora opera com contratos mais proximos de producao:

* [x] Logging estruturado centralizado em `backend/logging_config.py`.
* [x] Tratamento global de excecoes no FastAPI para respostas JSON seguras.
* [x] Falhas de LLM e provedores externos encapsuladas em erros de dominio controlados.
* [x] Persistencia local protegida por locks, escrita atomica e I/O delegado para thread quando necessario.
* [x] Sessoes isoladas por `session_id`, com estado do WebSocket salvo em `data/sessions/{id}/chat_state.json`.
* [x] Firecrawl migrado de CLI/subprocess para SDK oficial `firecrawl-py`.
* [x] Upload de curriculos endurecido com limite de tamanho e Magic Numbers.
* [x] Suite atual: 221 testes no backend (inclui stress test de 50 escritas concorrentes) e 26 no frontend.

Proximos marcos arquiteturais (atualizado em 2026-06-26 — em sua maioria entregues):

* [x] Frontend consumir os contratos padronizados de erro 422/500 com toasts ou banners amigaveis.
  Helper `frontend/src/lib/api.ts` (`apiRequest`) normaliza 422/500, corpo vazio, HTML/texto inesperado, falha de rede e timeout; todos os fluxos REST migrados.
* [ ] Frontend refletir visualmente a recuperacao de estado do WebSocket apos reconexao.
  Estado e' restaurado no handshake do WebSocket; falta repintar quiz/Coach no primeiro load sem expor a reconexao ao usuario.
* [x] Dockerizar backend e frontend.
  `backend/Dockerfile`, `frontend/Dockerfile` (build Vite servido por Nginx) e `docker-compose.yml` (com profile `mock`) — `docker compose up --build`.
* [x] Criar GitHub Actions com pipeline bloqueante para testes de contrato e concorrencia.
  `.github/workflows/backend-ci.yml` roda a suite completa (inclui `test_concurrency.py`) em PRs/pushes para `main`.

## 2.1 Arquitetura, backend e resiliência

* [x] Backend FastAPI estruturado com rotas REST, WebSocket e agentes
  especializados.
* [x] Logging JSON centralizado em `backend/logging_config.py`, com eventos de
  WebSocket, agentes, LLM e integrações associados ao `session_id`.
* [x] Exceções de domínio e respostas seguras para erros 422, 500, LLM e
  Firecrawl, sem exposição de traceback ao usuário.
* [x] Chamadas bloqueantes de disco e SDK externo movidas para
  `asyncio.to_thread`.
* [x] Persistência protegida por locks, escrita temporária e `os.replace`.
* [x] Operações read-modify-write de candidaturas protegidas contra concorrência.
* [x] Isolamento multiusuário por `session_id` em `data/sessions/{id}/`.
* [x] Rotas REST recebem `SessionPaths`; WebSocket e agentes usam os mesmos
  caminhos isolados.
* [x] Upload de currículo protegido por limite de tamanho, `Content-Type`, Magic
  Numbers e resposta 413 para arquivo excessivo.
* [x] Firecrawl migrado do CLI/subprocess para o SDK oficial `firecrawl-py`.
* [x] `LLM_BASE_URL` permite provedores compatíveis com a API OpenAI.
* [x] `openai.APIError` é convertido em `LLMProviderError` controlado em chamadas
  normais e streaming.

## 2.2 Estado e WebSocket

* [x] Estado do chat persistido atomicamente em
  `data/sessions/{session_id}/chat_state.json`.
* [x] Quiz, modo atual, passo do Coach e contexto recente são restaurados no
  handshake.
* [x] Envio de mensagem com socket fechado retorna falha e libera loading e
  streaming.
* [x] Reconexão automática implementada sem duplicar respostas.
* [x] Recuperação visual no primeiro load concluída no commit `d14e2d1`:
  `replay=1` repinta quiz, menu, Coach ou prompt de vaga sem gravar arquivos,
  avançar etapa ou emitir `__STATE__`.
* [x] Reconexões transitórias permanecem silenciosas porque não enviam
  `replay=1`.

## 2.3 Maestro e jornada conversacional

* [x] Quiz de sete perguntas com retomada, validação e consolidação do perfil.
* [x] Diagnóstico pode aproveitar área, nível e habilidades encontrados no
  currículo e perguntar apenas os campos ausentes.
* [x] Menu dividido em duas esteiras:
  * Carreira: A–D;
  * Candidatura: E–I.
* [x] Roteamento conversacional implementado para busca de vagas, cursos,
  entrevista, novo diagnóstico, análise de vaga, match, tailoring, PDI e
  reconciliação.
* [x] Fluxo master/detail do menu implementado no rodapé do chat.
* [x] Reset do diagnóstico limpa perfil e artefatos dependentes.
* [x] Pré-requisitos dos fluxos são validados antes do despacho ou da execução.

## 2.4 Scout e Curator

* [x] Scout calcula aderência, habilidades correspondentes, lacunas, soft skills,
  requisitos recorrentes e prioridade de candidatura.
* [x] Filtro de data das vagas integrado entre frontend, WebSocket, Maestro e
  Scout.
* [x] Busca degradada do Firecrawl é sinalizada quando a consulta específica
  falha e a busca ampla recupera vagas reais.
* [x] Falta de créditos é diferenciada de rate limit por
  `FirecrawlCreditError`.
* [x] Cadeia de fallback do Scout implementada:
  Firecrawl → LLM → simulação determinística.
* [x] Sugestões do LLM usam `source="llm"`, não têm link clicável e aparecem
  como “Sugerida por IA” e “não verificada”.
* [x] Curator normaliza lacunas, classifica nível, duração, plataforma e preço e
  organiza uma trilha priorizada.
* [x] Base interna de cursos e recomendações oficiais mantém o fluxo disponível
  quando a busca externa falha.

## 2.5 Currículo e esteira de candidatura

* [x] Upload e análise de currículo em PDF, DOCX e TXT.
* [x] Geração e leitura de `resume-analysis.md`.
* [x] Análise estruturada de descrição de vaga e persistência em
  `job-description-analysis.md`.
* [x] Match entre vaga e currículo com score de 0 a 100, aliases normalizados,
  lacunas e próximos passos.
* [x] Geração e leitura de `resume-match-report.md`.
* [x] Sugestões seguras por seção do currículo, sem inventar experiências.
* [x] Geração e exibição de PDI de 7, 30 e 60 dias.
* [x] Pipeline de candidaturas com criação, edição, exclusão e estatísticas.
* [x] Reconciliação dos pares perfil↔currículo, perfil↔vaga e currículo↔vaga.
* [x] Score de consistência e recomendações por foco implementados.
* [x] Foco da candidatura configurável como perfil, currículo ou vaga.
* [x] Foco persistido via `PUT /api/reconciliation/focus` e consumido por match,
  tailoring e PDI.

## 2.6 Coach

* [x] Entrevista simulada estruturada em cinco perguntas com feedback por etapa.
* [x] Contexto prioriza vaga analisada, relatório de aderência, resultados do
  Scout e funções alvo.
* [x] Perguntas técnicas usam requisitos e lacunas do match.
* [x] Perguntas comportamentais usam responsabilidades da vaga.
* [x] Fallback local mantém a entrevista disponível quando o LLM falha.
* [x] Sessão de entrevista é persistida e pode ser retomada.

## 2.7 Frontend, UX e acessibilidade

* [x] Frontend React 19, TypeScript 6 e Vite com tema dark tech e Career Arcade
  Pipeline.
* [x] Helper `apiRequest` centraliza timeout, falha de rede, corpo vazio,
  HTML/texto inesperado e erros 400, 413, 422 e 500.
* [x] Fluxos REST principais migrados para `apiRequest`.
* [x] Estados anteriores são preservados quando uma leitura ou mutação falha.
* [x] Componentes de perfil, currículo, vaga, match, sugestões, PDI, Scout,
  Curator e candidaturas integrados à interface.
* [x] Pipeline visual implementada para desktop, notebook, tablet e mobile.
* [x] Responsividade validada em oito resoluções, sem overflow horizontal.
* [x] Sidebar, barra de escrita, barra de progresso recolhida e ordem das
  mensagens estabilizadas.
* [x] QA visual e funcional executado em Chrome e Edge.
* [x] Controles touch com área mínima, foco de teclado visível, modais com
  `Escape`, estados com texto e ícone e suporte a redução de movimento.
* [x] Fallback de cópia implementado para ambientes com Clipboard API restrita.

## 2.8 Privacidade, infraestrutura e entrega

* [x] Arquivos de runtime e dados pessoais em `data/` ignorados pelo Git.
* [x] `data/README.md` documenta o caráter local e sensível dos artefatos.
* [x] Somente documentação e exemplos sanitizados permanecem versionáveis em
  `data/`.
* [x] Backend Docker em imagem Python leve, com usuário sem privilégios e
  healthcheck.
* [x] Frontend Docker com build Vite e Nginx.
* [x] Nginx configurado para SPA, proxy `/api` e upgrade `/ws`.
* [x] `docker-compose.yml` orquestra frontend, backend, volume de dados e mock
  opcional.
* [x] Stack Docker validada ponta a ponta: build, healthcheck, SPA, API e
  WebSocket.
* [x] GitHub Actions executa a suíte backend em push e pull request para `main`.
* [x] Testes de concorrência e contrato fazem parte da pipeline bloqueante.

## 2.9 Testes e validações concluídas

* [x] Suíte backend com **229 testes passando**.
* [x] Stress test com 50 escritas concorrentes sem perda.
* [x] Cobertura de agentes, sessão, isolamento, rotas, validação de
  pré-requisitos, candidaturas, reconciliação, foco, Firecrawl e replay.
* [x] Caminhos `call_llm` e `stream_llm` validados com provedor compatível.
* [x] Frontend com **48 testes passando**.
* [x] `npm run lint` sem erros.
* [x] `npm run build` sem erros.
* [x] Fluxo manual currículo → vaga → match → sugestões → PDI validado com
  backend real.
* [x] Quiz, candidaturas, upload, análise, cópia, responsividade e acessibilidade
  validados em navegador.

## 2.10 Documentação concluída

* [x] README documenta proposta, instalação, execução local, Docker, arquitetura,
  funcionalidades, fluxo de uso, artefatos e privacidade.
* [x] `data/README.md` documenta a finalidade e a sensibilidade dos dados locais.
* [x] `docs/frontend-qa-checklist.md` registra a validação visual.
* [x] `docs/project-update-report.md` consolidado até o commit `d14e2d1`.
* [x] Este checklist foi reorganizado em pendências priorizadas e entregas
  concluídas, sem duplicações de histórico.
