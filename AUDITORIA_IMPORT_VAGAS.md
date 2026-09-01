# Auditoria completa — Import Vagas

## Diagnóstico executivo

### 1. O que o Import Vagas é hoje?

É uma aplicação de desenvolvimento de carreira com IA, não um importador tradicional de vagas.

O fluxo principal é:

```text
Usuário
  ↓
Frontend React/TypeScript
  ↓
WebSocket ou REST
  ↓
Backend FastAPI
  ↓
Maestro
  ├── Scout: busca e matching de vagas
  ├── Curator: recomendações de aprendizado
  └── Coach: simulação de entrevista
  ↓
Arquivos Markdown/JSON por sessão
  ↓
Relatórios e componentes do frontend
```

Evidências:

- `README.md`
- `backend/main.py`
- `backend/agents/maestro.py`
- `backend/agents/scout.py`
- `backend/routers/chat.py`
- `frontend/src/App.tsx`

Não existe uma rotina específica de importação em lote de vagas, banco de vagas ou endpoint para ingestão de arquivos de vagas.

### 2. O que já está funcionando?

Confirmado pelo código e por execução:

- Backend FastAPI inicializa.
- `/health` responde `200`.
- Perfil e status do quiz possuem endpoints.
- WebSocket `/ws/chat` existe.
- Quiz conversacional existe.
- Upload de currículo PDF, DOCX e TXT existe.
- Análise de currículo existe.
- Análise de descrição de vaga existe.
- Match currículo × vaga existe.
- Sugestões de currículo existem.
- PDI existe.
- Reconciliação perfil × currículo × vaga existe.
- Tracker de candidaturas possui CRUD.
- Persistência por sessão existe.
- Escrita atômica e locks existem.
- Manifesto de artefatos e invalidação de dependências existem.
- Mock server funciona.
- Docker Compose é válido.
- Lint frontend passa.
- TypeScript passa.
- Data Guard principal passa.
- `test_concurrency.py` passa isoladamente.

### 3. O que está parcialmente implementado?

- Busca real de vagas depende de Firecrawl e de créditos externos.
- LLM depende de OpenAI ou provedor compatível.
- Sem credenciais, o Scout degrada para LLM ou vagas simuladas.
- Persistência é local em arquivos, não em banco.
- Sessões são anônimas e baseadas em `localStorage`.
- O tracker representa candidaturas, mas não é integrado automaticamente ao resultado do Scout.
- O currículo pode sugerir atualização do perfil, mas depende de confirmação explícita.
- O frontend possui estados de erro/loading, porém os fluxos ainda dependem fortemente do WebSocket e de arquivos locais.
- O build frontend não foi validado com sucesso no ambiente atual.
- A suíte completa de backend não concluiu dentro de 120 segundos.

### 4. O que ainda falta?

- Autenticação real.
- Autorização e isolamento baseado em usuário.
- Banco de dados produtivo.
- Armazenamento persistente e seguro de currículos.
- Backup e recuperação.
- Rate limiting.
- Métricas e monitoramento.
- Pipeline de deploy.
- Deduplicação persistente de vagas.
- Identificadores externos de vagas.
- Expiração e atualização de vagas.
- Importação em lote de vagas.
- Teste E2E real com frontend, backend e serviços externos.
- Garantia de build frontend em ambiente limpo.

---

# 1. Mapa da estrutura

## Stack

Backend:

- Python 3.11+
- FastAPI
- Uvicorn
- WebSockets
- Pydantic
- OpenAI SDK
- Firecrawl SDK
- `pypdf`
- `python-docx`
- Markdown/JSON como persistência

Frontend:

- React 19
- TypeScript
- Vite
- Tailwind CSS 4
- Framer Motion
- React Markdown
- Vitest
- ESLint

Infraestrutura:

- Dockerfiles separados
- Docker Compose
- Nginx como proxy reverso
- GitHub Actions para CI
- Sem banco relacional
- Sem provedor de storage
- Sem pipeline de deploy

## Organização principal

- `backend/main.py`: aplicação FastAPI, CORS, handlers globais e health check.
- `backend/config.py`: configuração e variáveis de ambiente.
- `backend/session.py`: isolamento de sessões e persistência atômica.
- `backend/routers/`: endpoints REST e WebSocket.
- `backend/agents/`: lógica dos agentes.
- `backend/artifacts.py`: manifesto, hashes e dependências entre artefatos.
- `backend/firecrawl_client.py`: integração com Firecrawl.
- `frontend/src/App.tsx`: composição principal da interface.
- `frontend/src/components/`: telas e componentes de produto.
- `frontend/src/hooks/useWebSocket.ts`: conexão, streaming e reconexão.
- `frontend/src/lib/api.ts`: cliente HTTP e tratamento de erros.
- `data/`: estado runtime, ignorado pelo Git.
- `docs/`: decisões, checklists e relatórios.
- `.github/workflows/`: CI backend, frontend, Data Guard e documentação.

---

# 2. Fluxo real do usuário

## Diagnóstico

1. Frontend abre o WebSocket.
2. Backend recupera o estado da sessão.
3. Maestro apresenta o quiz ou menu.
4. Usuário responde via WebSocket.
5. Maestro persiste:
   - `personality-quiz.md`
   - `user-profile.md`
   - `chat_state.json`

## Busca de vagas

1. Usuário escolhe `A`.
2. Maestro aciona o Scout.
3. Scout lê o perfil.
4. Scout monta consultas.
5. Firecrawl busca resultados quando disponível.
6. O Scout extrai, normaliza e calcula match de habilidades.
7. Caso a busca falhe:
   - tenta fallback com LLM;
   - eventualmente usa dados simulados.
8. Resultado é salvo em `job-search-results.md`.
9. Frontend renderiza `ScoutReport`.

## Análise de candidatura

A cadeia E–I está implementada:

```text
E — análise da descrição
  ↓
F — match currículo × vaga
  ↓
G — sugestões de currículo
  ↓
H — PDI
  ↓
I — reconciliação e foco
```

A cadeia possui validação de pré-requisitos e marcação de artefatos obsoletos.

## O que não existe nesse fluxo

- Importação CSV/Excel.
- Upload de múltiplas vagas.
- Banco de vagas.
- Deduplicação persistente.
- Atualização automática de vagas.
- Expiração automática.
- Catálogo pesquisável de empresas.
- Identificador externo de vaga.
- Pipeline agendado de coleta.

---

# 3. Inventário de funcionalidades

Como solicitado pelas instruções da persona do projeto, o inventário está em lista estruturada, não em tabela Markdown.

## Perfil e quiz

1. Funcionalidade: quiz de perfil  
   Frontend: `QuizPanel.tsx`  
   Backend: `MaestroAgent`, `chat.py`  
   Banco: arquivos Markdown  
   Integração: WebSocket  
   Status: ✅ Funcional

2. Funcionalidade: criação de perfil  
   Frontend: `ProfilePanel.tsx`  
   Backend: `profile.py`, `maestro.py`  
   Banco: `user-profile.md`  
   Status: ✅ Funcional

3. Funcionalidade: preenchimento por currículo  
   Frontend: `ResumeUpload.tsx`, `ProfileSuggestionConfirm.tsx`  
   Backend: `resume.py`  
   Status: ✅ Funcional, com confirmação explícita

## Vagas

4. Funcionalidade: busca de vagas  
   Frontend: `ChatInput.tsx`, `ScoutReport.tsx`  
   Backend: `agents/scout.py`  
   Integração: Firecrawl  
   Status: ⚠️ Dependente de serviço externo e fallback

5. Funcionalidade: filtro de recência  
   Frontend: `ProfilePanel.tsx`  
   Backend: WebSocket e Scout  
   Status: ✅ Implementado

6. Funcionalidade: importação de vagas  
   Frontend: inexistente  
   Backend: inexistente  
   Status: Não implementado

7. Funcionalidade: deduplicação de vagas  
   Status: Não implementado como persistência de produto

8. Funcionalidade: favoritos  
   Frontend/backend: representado pelo status `salva` no tracker  
   Status: Parcial

## Candidatura

9. Funcionalidade: tracker de candidaturas  
   Frontend: `ApplicationTracker.tsx`  
   Backend: `applications.py`  
   Banco: `applications.json`  
   Status: ✅ Funcional localmente

10. Funcionalidade: atualização de status  
    Status: ✅ Funcional

11. Funcionalidade: vínculo automático com vaga encontrada  
    Status: Não implementado

## Currículo e análise

12. Upload de currículo  
    Status: ✅ Funcional, com limite de 5 MB e validação de assinatura

13. Extração PDF/DOCX/TXT  
    Status: ✅ Implementada

14. Match currículo × vaga  
    Status: ✅ Funcional com pré-requisitos

15. Sugestões de currículo  
    Status: ✅ Funcional

16. Geração de PDI  
    Status: ✅ Funcional

17. Reconciliação  
    Status: ✅ Funcional

## Entrevista

18. Entrevista simulada  
    Frontend: `ChatTerminal.tsx`  
    Backend: `CoachAgent`  
    Status: ✅ Implementada via WebSocket

19. Persistência e replay da entrevista  
    Status: ✅ Implementada

---

# 4. Endpoints existentes

## Saúde e WebSocket

1. `GET /health`  
   Finalidade: health check  
   Autenticação: nenhuma  
   Status: ✅ Funcional

2. `WS /ws/chat`  
   Finalidade: chat, streaming e orquestração  
   Autenticação: nenhuma  
   Status: ✅ Implementado

## Perfil

3. `GET /api/profile/`
4. `GET /api/profile/quiz-status`

Status: ✅ Funcionais.

## Arquivos e relatórios

5. `GET /api/data/jobs`
6. `GET /api/data/courses`
7. `GET /api/data/interview`
8. `GET /api/data/resume-analysis`
9. `GET /api/data/job-description`
10. `GET /api/data/resume-match`
11. `GET /api/data/reconciliation`
12. `GET /api/data/resume-tailoring`
13. `GET /api/data/pdi`

Status: ✅ Implementados, dependentes da existência de artefatos válidos.

## Currículo

14. `GET /api/resume/latest`
15. `POST /api/resume/upload`
16. `POST /api/resume/apply-profile`

Status: ✅ Funcionais.

## Descrição da vaga

17. `GET /api/job-description/latest`
18. `POST /api/job-description/analyze`

Status: ✅ Funcionais.

## Match

19. `GET /api/resume-match/latest`
20. `POST /api/resume-match/analyze`

Status: ✅ Funcionais com validação de pré-requisitos.

## Tailoring

21. `GET /api/resume-tailoring/latest`
22. `POST /api/resume-tailoring/generate`

Status: ✅ Funcionais com validação de cadeia.

## PDI

23. `GET /api/pdi/latest`
24. `POST /api/pdi/generate`

Status: ✅ Funcionais com validação de cadeia.

## Reconciliação

25. `GET /api/reconciliation/latest`
26. `POST /api/reconciliation/analyze`
27. `PUT /api/reconciliation/focus`

Status: ✅ Funcionais.

## Candidaturas

28. `GET /api/applications/`
29. `POST /api/applications/`
30. `PATCH /api/applications/{app_id}`
31. `DELETE /api/applications/{app_id}`
32. `GET /api/applications/stats`

Status: ✅ Funcionais localmente.

Não há autenticação em nenhum endpoint.

---

# 5. Código incompleto e sinais de protótipo

## CRÍTICO

- Ausência total de autenticação.
- Sessão baseada somente em ID armazenado no navegador.
- Currículos e perfis são dados sensíveis.
- Persistência em volume local não é adequada para múltiplas instâncias.
- Não existe proteção contra abuso de endpoints caros de IA.
- Deploy público permitiria acesso anônimo aos fluxos de processamento.

Evidências:

- `backend/main.py:59-69`
- `backend/session.py:239-245`
- `frontend/src/lib/session.ts`
- `README.md`, seção de privacidade

## ALTO

- CORS configurado somente para origens locais em `backend/main.py:59-69`.
- Não há readiness check verificando Firecrawl, LLM ou storage.
- Sem métricas, tracing ou request ID.
- Sem backup automático.
- Sem banco relacional.
- Sem pipeline de deploy.
- Docker Compose usa persistência local, mas não estratégia de backup.
- Build frontend não foi validado neste ambiente.
- Suíte backend completa excedeu 120 segundos.

## MÉDIO

- `frontend/src/index.css` possui mais de 6.700 linhas e sinais de evolução incremental.
- Existem vários blocos de tokens e estilos sobrepostos.
- Fallback simulado pode gerar uma percepção de dado real se a UI não destacar claramente a origem.
- Erros do frontend são enviados a `console.error`, sem telemetria central.
- Estado de sessão depende de `localStorage`, que pode ser limpo ou bloqueado.
- Sem paginação ou busca real no tracker.

## BAIXO

- `README.md` ainda contém referências antigas de estrutura e números de testes.
- `frontend/README.md` ainda é essencialmente o README padrão do Vite.
- O nome do produto sugere importação, mas a aplicação atual é mais ampla e conversacional.
- Há comentários e textos com encoding inconsistente em algumas saídas do terminal.

---

# 6. Testes

## Quantidade confirmada

- Backend: 303 testes coletados pelo `pytest --collect-only`.
- Frontend: 45 testes identificados nos seis arquivos de teste.

O README menciona 250 testes backend e 56 frontend, portanto essa documentação está desatualizada.

## Resultados executados

1. Backend completo  
   Resultado: não concluído.  
   O processo ultrapassou 120 segundos e chegou aproximadamente a 59% antes do timeout.

2. `tests/test_concurrency.py`  
   Resultado: ✅ 1 teste aprovado em 4,87s.

3. Frontend lint  
   Resultado: ✅ aprovado.

4. TypeScript `tsc -b`  
   Resultado: ✅ aprovado.

5. Frontend Vitest  
   Resultado: ❌ não iniciou devido ao binding nativo do Tailwind/Oxide e erro `spawn EPERM`.

6. Frontend build  
   Resultado: ❌ falhou no bundling pelo mesmo problema nativo do Tailwind/Oxide.

7. Data Guard CLI  
   Resultado: ✅ aprovado: 164 arquivos verificados.

8. Testes isolados do Data Guard  
   Resultado: ❌ falharam durante criação de repositórios temporários por restrição de `git init` e permissões da pasta temporária do ambiente.

## Cobertura existente

Boa cobertura unitária para:

- Sessões.
- Persistência atômica.
- Corrupção de artefatos.
- Reconciliação.
- Match.
- Upload.
- Validação de arquivos.
- Candidaturas.
- WebSocket.
- Fallbacks do Scout.
- Agentes.

Cobertura ausente ou insuficiente:

- E2E real frontend + backend.
- Navegador real.
- Deploy em ambiente limpo.
- Autenticação.
- Autorização.
- Backup/restauração.
- Concorrência entre múltiplos processos/containers.
- Firecrawl real.
- OpenAI real.
- Teste de carga.
- Segurança de sessão.
- Expiração e deduplicação de vagas.

---

# 7. Auditoria do frontend

## Pontos positivos

- Componentização razoável.
- Lazy loading de telas mais pesadas.
- Tratamento de loading, erro e estados vazios em vários componentes.
- Reconexão automática do WebSocket.
- Foco e navegação por teclado em modais.
- `aria-label` em vários controles.
- Suporte responsivo com breakpoints.
- `prefers-reduced-motion`.
- Cliente HTTP com timeout.
- Mensagens de erro amigáveis.
- Estado visual da pipeline de candidatura.

Arquivos:

- `frontend/src/App.tsx`
- `frontend/src/hooks/useWebSocket.ts`
- `frontend/src/lib/api.ts`
- `frontend/src/components/ui/FeedbackState.tsx`

## Problemas

- A aplicação depende muito de WebSocket para o fluxo principal.
- Não existe rota de frontend tradicional; a navegação é controlada por modais e estado.
- A sessão não é uma identidade real.
- Não há recuperação de conta ou sincronização entre dispositivos.
- O frontend não diferencia de forma estrutural suficiente:
  - vaga real;
  - vaga sugerida por IA;
  - vaga simulada.
- O tracker não recebe automaticamente os resultados do Scout.
- O CSS é grande e possui provável duplicação/overrides.
- Não existe teste visual automatizado.
- Build depende de binding nativo problemático no ambiente atual.
- Não foi possível validar a interface em navegador real nesta execução.

## Avaliação de UX

A direção visual é consistente com a proposta “dark tech/career arcade”:

- Ciano, rosa, verde e amarelo são usados como estados e agentes.
- A pipeline visual é uma assinatura adequada ao produto.
- O chat é o centro da experiência.
- A navegação lateral concentra perfil e ações.

Riscos:

- Excesso de neon, glow e animações pode reduzir legibilidade.
- A interface tem muitas funções para um fluxo centrado em chat.
- O usuário pode não entender a diferença entre “analisar vaga”, “buscar vagas” e “candidaturas”.
- O produto ainda precisa de uma hierarquia mais clara entre:
  - descobrir;
  - avaliar;
  - candidatar;
  - desenvolver habilidades.

---

# 8. Auditoria do backend

## Pontos positivos

- Separação entre routers, agentes e utilitários.
- Validação Pydantic.
- Tratamento global de 422 e 500.
- Persistência atômica.
- Locks por sessão.
- Manifesto de artefatos.
- Detecção de artefatos obsoletos.
- Validação de PDF/DOCX por assinatura.
- Limite de upload.
- Erros controlados para artefatos corrompidos.
- Logging JSON estruturado.

## Problemas

- A arquitetura ainda é monolítica.
- Os agentes acessam diretamente arquivos de estado.
- Não existe camada de repositório persistente abstrata.
- Não existe autenticação/autorização.
- Não existe rate limit.
- Não existe fila para tarefas longas.
- Chamadas de LLM e scraping podem consumir recursos da própria instância.
- Não há cache persistente.
- Não há política de retenção.
- Não há controle de custos por usuário.
- Não há idempotência formal para operações externas.

---

# 9. Banco de dados

## Estado atual

Não há banco de dados.

Não existem:

- `database/`
- `migrations/`
- `seeds/`
- SQLAlchemy
- Prisma
- PostgreSQL
- SQLite
- Redis

A persistência ocorre em:

- Markdown para perfil, análises e relatórios.
- JSON para candidaturas.
- JSON para estado do chat.
- Volume Docker `backend-data`.

## Entidades atuais

1. Sessão
   - ID anônimo
   - estado do chat
   - artefatos associados

2. Perfil
   - área
   - nível
   - preferências
   - localização
   - skills
   - objetivo

3. Currículo
   - análise extraída
   - sugestões para perfil

4. Descrição de vaga
   - título
   - empresa
   - modalidade
   - senioridade
   - skills
   - alertas

5. Match
   - score
   - evidências
   - lacunas

6. Tailoring
   - sugestões por seção

7. PDI
   - planos de 7, 30 e 60 dias

8. Reconciliação
   - conflitos
   - foco
   - score de consistência

9. Candidatura
   - vaga
   - empresa
   - status
   - notas
   - data

## Avaliação

Adequado para protótipo local ou demonstração single-instance.

Não adequado para produção pública com:

- múltiplos usuários;
- múltiplas réplicas;
- consultas;
- auditoria;
- backup;
- relatórios;
- retenção;
- recuperação de dados.

---

# 10. Auditoria do fluxo de vagas

## Pipeline implementado

1. Origem  
   Firecrawl, LLM ou dados simulados.

2. Coleta  
   Scout em `backend/agents/scout.py`.

3. Validação  
   Validação de payload e proveniência.

4. Normalização  
   Conversão para estrutura de vaga.

5. Matching  
   Comparação com habilidades do perfil.

6. Persistência  
   `job-search-results.md`.

7. Apresentação  
   `ScoutReport.tsx`.

## Pipeline ausente

- ID externo confiável.
- Hash de vaga.
- Deduplicação entre buscas.
- Empresa normalizada.
- Histórico de alterações.
- Expiração.
- Atualização periódica.
- Status “vaga encerrada”.
- Banco pesquisável.
- Importação por CSV/Excel.
- Fila de processamento.
- Reprocessamento controlado.

## Conclusão

O produto coleta e apresenta oportunidades, mas não mantém um catálogo de vagas. O termo “Import Vagas” atualmente descreve mais a intenção do produto do que sua implementação literal.

---

# 11. Segurança

## Pontos positivos

- Nenhum segredo aparece rastreado pelo Git.
- `.env.example` usa placeholders.
- Data Guard verifica arquivos rastreados.
- Upload possui limite de 5 MB.
- PDF e DOCX possuem validação de magic number.
- Links de candidatura aceitam apenas HTTP/HTTPS ou vazio.
- IDs de sessão são sanitizados.
- Escrita concorrente é protegida.

## Problemas críticos

### Ausência de autenticação

Todos os endpoints usam apenas o header `X-Session-Id`, fornecido pelo cliente.

Esse ID:

- fica no `localStorage`;
- pode ser substituído;
- não prova identidade;
- não possui expiração;
- não possui rotação;
- não possui autorização.

Para um produto público com currículo e perfil profissional, isso é insuficiente.

### CORS

`backend/main.py:59-69` libera origens locais específicas. Para produção será necessário configurar a origem real.

O mock server usa CORS aberto em `backend/mock_server.py`.

### Abuso

Não há:

- rate limiting;
- limite por usuário;
- proteção contra spam no WebSocket;
- limite de custo de LLM;
- proteção contra scraping abusivo;
- fila ou quota.

### Segredos locais

Existe um `backend/.env` local não rastreado, detectado indiretamente pela expansão do Docker Compose. Os valores não foram exibidos. Isso é correto para o repositório, mas deve ser substituído por secrets do ambiente no deploy.

---

# 12. Configuração

Variáveis encontradas em `backend/.env.example`:

1. `OPENAI_API_KEY`  
   Obrigatória para LLM real.  
   Produção: secret gerenciado.  
   Presença no exemplo: sim.

2. `FIRECRAWL_API_KEY`  
   Obrigatória para busca real.  
   Produção: secret gerenciado.  
   Presença no exemplo: sim.

3. `LLM_MODEL`  
   Modelo utilizado.  
   Produção: sim.

4. `LLM_BASE_URL`  
   Provedor OpenAI-compatible alternativo.  
   Produção: opcional.

5. `DATA_DIR`  
   Estado dos usuários.  
   Produção: volume persistente ou storage externo.

6. `PERSONAS_DIR`  
   Personas dos agentes.  
   Produção: sim.

7. `SKILLS_DIR`  
   Skills do sistema.  
   Produção: sim.

8. `WS_MAX_MESSAGE_CHARS`  
   Limite de mensagem WebSocket.  
   Produção: sim.

9. `LOG_LEVEL`  
   Nível de logging.  
   Produção: sim.

10. `LOG_TO_FILE`  
    Logs em arquivo.  
    Produção: preferencialmente logs enviados à plataforma.

11. `LOG_DIR`  
    Diretório de logs.  
    Produção: opcional.

12. `LOG_FILE`  
    Arquivo de logs.  
    Produção: opcional.

13. `LOG_MAX_BYTES`  
    Rotação de logs.  
    Produção: sim se logs locais forem usados.

14. `LOG_BACKUP_COUNT`  
    Quantidade de backups.  
    Produção: sim se logs locais forem usados.

Variáveis que faltam para produção:

- `ALLOWED_ORIGINS`
- `SESSION_SECRET`
- `DATABASE_URL`
- `STORAGE_BUCKET`
- `ENVIRONMENT`
- `SENTRY_DSN` ou equivalente
- `RATE_LIMIT_*`
- `MAX_USERS`
- `RETENTION_DAYS`

---

# 13. Logs e observabilidade

## Existente

- Logging JSON em `backend/logging_config.py`.
- Logs de startup/shutdown.
- Logs de validação.
- Logs de exceções.
- Logs de sessão.
- Logs de Firecrawl.
- Rotação de arquivo opcional.
- `/health`.

## Ausente

- Request ID global.
- Readiness check.
- Métricas Prometheus.
- Latência por endpoint.
- Custo por chamada de LLM.
- Taxa de erro do Firecrawl.
- Número de sessões ativas.
- Alertas.
- Rastreamento distribuído.
- Painel operacional.

## Necessário antes de produção

- Logs stdout estruturados.
- Request ID.
- Sentry ou equivalente.
- Métricas de erro e latência.
- Monitoramento de disco.
- Monitoramento de custo das APIs.
- Alertas de indisponibilidade.

---

# 14. Docker

## Pontos positivos

- Backend usa Python slim.
- Frontend usa build multi-stage.
- Backend roda com usuário não-root.
- Healthcheck existe.
- Volume persistente existe.
- Nginx faz proxy REST e WebSocket.
- `docker compose config` passou.
- Compose suporta mock.

## Problemas

- Não existe arquivo de produção separado.
- Não há backup do volume.
- Não há secrets Docker dedicados.
- `depends_on` do frontend espera apenas o início do backend, não health.
- Uma única réplica é assumida.
- O armazenamento local impede escala horizontal segura.
- Não há política de limpeza de arquivos.
- O build Docker não foi executado porque o Buildx do ambiente retornou acesso negado ao lock local.

---

# 15. CI/CD

## Existente

1. Backend CI  
   Instala dependências e executa pytest.

2. Frontend CI  
   Executa:
   - npm ci
   - testes
   - lint
   - build

3. Data Guard  
   Valida segredos e arquivos de estado.

4. Docs Check  
   Confirma documentos essenciais.

## Parcial

- Testes existem.
- Build é exigido no CI.
- Segurança é limitada ao Data Guard.
- Não existe scanning de dependências.
- Não existe Docker build no CI.

## Inexistente

- Deploy automático.
- Staging.
- Smoke test pós-deploy.
- Rollback automático.
- Migrações.
- Backup.
- Verificação de secrets no ambiente de produção.

---

# 16. Pode ser publicado hoje?

## Classificação

**Não está pronto para produção pública.**

Pode ser publicado como:

- demonstração;
- protótipo fechado;
- ambiente interno;
- MVP local;
- teste com dados fictícios.

Não deve ser publicado ainda para usuários reais com currículos e dados pessoais.

## Motivos principais

1. Sem autenticação.
2. Sem autorização.
3. Sem banco produtivo.
4. Sem backup.
5. Sem rate limiting.
6. Sem monitoramento.
7. Build frontend ainda não confirmado em ambiente limpo.
8. Suíte backend completa não concluiu.
9. Dependência de APIs pagas sem controle de custo.
10. Sem deploy automatizado.

---

# Bloqueadores de Deploy

## P0 — bloqueia deploy público

1. Autenticação e autorização inexistentes.
2. Proteção insuficiente de currículos e perfis.
3. Persistência baseada em volume local sem backup.
4. Ausência de rate limiting.
5. Ausência de controle de custos para OpenAI/Firecrawl.
6. Build frontend não validado com sucesso.
7. Suíte backend completa não concluída.
8. CORS ainda não parametrizado para domínio real.

## P1 — necessário antes de produção

1. Banco PostgreSQL ou equivalente.
2. Storage seguro para currículos.
3. Variáveis de ambiente de produção.
4. Logs centralizados.
5. Monitoramento e alertas.
6. Health/readiness checks.
7. Docker build no CI.
8. Smoke tests pós-deploy.
9. Política de retenção de dados.
10. Backup automatizado.
11. Testes E2E.
12. Documentação de operação.

## P2 — pode ser feito depois

1. Busca avançada.
2. Dashboard analítico.
3. Recomendações personalizadas.
4. Notificações.
5. Ranking de vagas.
6. Integrações com ATS.
7. Atualização automática de vagas.
8. Escala horizontal.

---

# 17. Estratégias de deploy

## Opção 1 — Docker em uma VM

Arquitetura:

```text
VM
 ├── Nginx/frontend
 ├── FastAPI/backend
 ├── volume persistente
 └── backup externo
```

Complexidade: baixa/média  
Custo inicial: baixo  
Escalabilidade: baixa  
Indicação: melhor para demonstração e MVP fechado.

Risco: operação, segurança e backup ficam sob responsabilidade do projeto.

## Opção 2 — Plataforma gerenciada com dois serviços

```text
Frontend estático
        ↓
Backend FastAPI com WebSocket
        ↓
PostgreSQL gerenciado
        ↓
Object Storage para currículos
```

Complexidade: média  
Custo inicial: baixo/médio  
Escalabilidade: média  
Indicação: melhor MVP público.

É a opção recomendada para evolução imediata.

## Opção 3 — AWS

```text
CloudFront/S3
      ↓
ALB
      ↓
ECS/Fargate ou App Runner
      ↓
RDS PostgreSQL
      ↓
S3
```

Complexidade: alta  
Custo inicial: médio/alto  
Escalabilidade: alta  
Indicação: produto com requisitos empresariais.

## Opção 4 — Backend em serviço gerenciado e frontend em CDN

Frontend:

- build estático em CDN.

Backend:

- container FastAPI com suporte a WebSocket.

Dados:

- PostgreSQL gerenciado.
- Storage de objetos.

Complexidade: média  
Custo inicial: baixo/médio  
Escalabilidade: média/alta  
Indicação: melhor equilíbrio entre simplicidade e crescimento.

## Melhor deploy para MVP

Um backend FastAPI em container, frontend estático servido por CDN/Nginx, PostgreSQL gerenciado e storage de objetos.

Para a primeira versão, manter uma única instância do backend e evitar escala horizontal até substituir a persistência local.

## Melhor arquitetura futura

Frontend CDN + API stateless + workers assíncronos + PostgreSQL + Redis/fila + storage de objetos + observabilidade centralizada.

---

# 18. Arquitetura recomendada

```text
                         Internet
                            │
                            ▼
                    CDN / HTTPS / WAF
                            │
                 ┌──────────┴──────────┐
                 ▼                     ▼
          Frontend React          API FastAPI
                                      │
                       ┌──────────────┼──────────────┐
                       ▼              ▼              ▼
                 PostgreSQL       Object Storage   Redis/Fila
                 perfis/vagas     currículos       jobs longos
                       │              │              │
                       └──────────────┼──────────────┘
                                      ▼
                           Agentes Maestro/Scout/
                           Curator/Coach
                              │          │
                              ▼          ▼
                         OpenAI       Firecrawl
```

Para o MVP fechado, Redis/fila pode ser adiado.

---

# 19. Checklist de publicação

- [ ] Definir domínio.
- [ ] Configurar HTTPS.
- [ ] Configurar `ALLOWED_ORIGINS`.
- [ ] Remover dependência de `X-Session-Id` como segurança.
- [ ] Adicionar autenticação.
- [ ] Adicionar autorização por usuário.
- [ ] Migrar dados para PostgreSQL.
- [ ] Mover currículos para storage privado.
- [ ] Configurar secrets do ambiente.
- [ ] Configurar backup.
- [ ] Criar política de retenção.
- [ ] Adicionar rate limiting.
- [ ] Adicionar controle de custo de LLM.
- [ ] Adicionar readiness check.
- [ ] Adicionar request ID.
- [ ] Centralizar logs.
- [ ] Adicionar monitoramento.
- [ ] Executar backend completo sem timeout.
- [ ] Executar frontend test/build em ambiente limpo.
- [ ] Rodar Docker build no CI.
- [ ] Criar smoke test pós-deploy.
- [ ] Validar WebSocket atrás do proxy.
- [ ] Testar upload de PDF, DOCX e TXT.
- [ ] Testar isolamento entre usuários.
- [ ] Testar restauração de backup.
- [ ] Definir rollback.
- [ ] Configurar pipeline de deploy.

---

# 20. Notas de qualidade arquitetural

1. Arquitetura: 6/10  
   Boa separação inicial, mas forte acoplamento à persistência em arquivos.

2. Organização: 7/10  
   Estrutura clara entre routers, agentes, frontend e infraestrutura.

3. Backend: 7/10  
   Validação, erros, locks e artefatos estão bem tratados.

4. Frontend: 7/10  
   Componentizado e responsivo, mas grande, complexo e dependente do WebSocket.

5. Banco: 3/10  
   Não existe banco produtivo.

6. Testes: 7/10  
   Boa quantidade e foco em regras críticas, mas execução completa ainda não está confiável.

7. Segurança: 4/10  
   Há hardening de arquivos e uploads, porém não há identidade nem autorização.

8. UX: 7/10  
   Direção visual forte, mas há risco de complexidade e sobrecarga cognitiva.

9. Observabilidade: 5/10  
   Logging é bom, métricas e alertas inexistem.

10. Deploy readiness: 4/10  
    Docker e CI existem, mas faltam segurança, persistência e validação final.

11. Documentação: 6/10  
    README é detalhado, mas contém divergências e ainda descreve aspectos que não refletem totalmente o estado atual.

---

# 21. Dívida técnica

## Dívida técnica real

1. Persistência em arquivos  
   Impacto: baixa capacidade de consulta, backup e escala.  
   Urgência: alta.  
   Arquivos: `backend/session.py`, `backend/artifacts.py`, `backend/routers/*.py`.  
   Solução: camada de persistência e PostgreSQL.

2. Sessão sem identidade  
   Impacto: risco de exposição de dados.  
   Urgência: crítica.  
   Arquivos: `frontend/src/lib/session.ts`, `backend/session.py`.  
   Solução: autenticação, sessão assinada e autorização.

3. Falta de rate limiting  
   Impacto: abuso e custos inesperados.  
   Urgência: alta.  
   Arquivos: `backend/main.py`, routers e WebSocket.  
   Solução: limite por usuário/IP e quotas.

4. Testes completos lentos ou pendentes  
   Impacto: baixa confiança no CI local.  
   Urgência: alta.  
   Arquivos: suíte backend, especialmente fluxos Scout/LLM.  
   Solução: identificar testes lentos, adicionar timeout e isolar chamadas externas.

5. CSS excessivamente grande  
   Impacto: manutenção e regressões visuais.  
   Urgência: média.  
   Arquivo: `frontend/src/index.css`.  
   Solução: consolidar tokens e estilos duplicados.

6. Falta de E2E  
   Impacto: contratos frontend/backend podem quebrar sem detecção.  
   Urgência: alta.  
   Solução: Playwright ou equivalente.

## Melhorias opcionais

- Dashboard mais sofisticado.
- Notificações.
- Ranking.
- Recomendações automáticas.
- Integrações com ATS.
- Atualização contínua das vagas.
- Analytics avançado.

---

# 22. Melhorias de produto

## Essencial

1. Busca e filtros persistentes.
2. Salvar vaga diretamente no tracker.
3. Status de candidatura com histórico.
4. Explicação clara da origem da vaga.
5. Busca por palavra-chave, empresa, modalidade e senioridade.
6. Histórico de análises.
7. Exclusão/exportação dos dados do usuário.

## Alto valor

1. Deduplicação de vagas.
2. Página de detalhes de vaga.
3. Matching vaga × currículo mais visual.
4. Alertas de novas vagas.
5. Dashboard de candidaturas.
6. Filtros por salário e localização.
7. Histórico de evolução do perfil.

## Evolução futura

1. Matching personalizado recorrente.
2. Integração com LinkedIn/ATS, respeitando termos de uso.
3. Ranking de oportunidades.
4. Recomendação baseada em histórico.
5. Calendário de entrevistas.
6. Estatísticas de conversão.

## Ideias experimentais

1. Agente que acompanha uma candidatura.
2. Simulação de entrevista adaptativa.
3. Feedback sobre clareza do currículo.
4. Comparação entre várias vagas.
5. Alertas de skills recorrentes no mercado.

---

# 23. Evolução com IA

1. Extração de skills  
   Valor: alto.  
   Complexidade: baixa/média.  
   LLM: útil, mas regras e taxonomia podem resolver parte.  
   Estado: parcialmente existente.

2. Normalização de cargos e tecnologias  
   Valor: alto.  
   Complexidade: média.  
   LLM: útil para casos ambíguos.  
   Alternativa: dicionário e embeddings.

3. Classificação de senioridade  
   Valor: médio/alto.  
   Complexidade: baixa.  
   LLM: não necessariamente necessário.  
   Alternativa: regras e scores.

4. Match currículo × vaga  
   Valor: muito alto.  
   Complexidade: média.  
   LLM: útil para evidências semânticas.  
   Estado: já existe uma versão baseada em análise estruturada.

5. Score de compatibilidade  
   Valor: alto.  
   Complexidade: média.  
   LLM: deve complementar regras, não substituí-las.  
   Estado: já implementado.

6. Resumo de vaga  
   Valor: médio.  
   Complexidade: baixa.  
   LLM: útil.  
   Alternativa: extração estruturada.

7. Recomendação personalizada  
   Valor: alto.  
   Complexidade: alta.  
   LLM: útil somente com histórico suficiente.  
   Deve ser fase posterior.

8. Geração de currículo  
   Valor: alto, mas risco elevado.  
   Complexidade: alta.  
   Necessário controle rigoroso para não inventar experiência.  
   Estado: o projeto já adota uma abordagem mais segura de sugestões.

---

# 24. Roadmap

## Fase 0 — Correções críticas

1. Prioridade: P0  
   Complexidade: alta  
   Dependência: decisão de modelo de usuário  
   Resultado: autenticação e isolamento real.

2. Prioridade: P0  
   Complexidade: média  
   Dependência: plataforma de deploy  
   Resultado: CORS, secrets e configuração produtiva.

3. Prioridade: P0  
   Complexidade: média  
   Dependência: diagnóstico dos testes  
   Resultado: backend e frontend com execução determinística.

4. Prioridade: P0  
   Complexidade: média  
   Dependência: infraestrutura  
   Resultado: rate limiting e controle de custos.

## Fase 1 — Deploy MVP

1. PostgreSQL.
2. Storage privado de currículos.
3. Backup.
4. Logs centralizados.
5. Monitoramento.
6. Docker build no CI.
7. Smoke tests.
8. Deploy em uma instância.
9. WebSocket validado atrás de HTTPS.

## Fase 2 — Produto

1. Salvar vaga diretamente no tracker.
2. Deduplicação.
3. Busca e filtros.
4. Histórico de candidaturas.
5. Dashboard.
6. Expiração de vagas.
7. Exportação e exclusão de dados.
8. Melhor distinção entre vaga real, IA e simulada.

## Fase 3 — Evolução

1. Jobs assíncronos.
2. Cache.
3. Alertas.
4. Matching recorrente.
5. Recomendações.
6. Taxonomia de skills.
7. Integrações externas.

## Fase 4 — Escala

Somente se houver demanda real:

1. Réplicas da API.
2. Redis.
3. Workers dedicados.
4. Fila de scraping/LLM.
5. Observabilidade distribuída.
6. Separação de serviços.

---

# ⚡ Quick Wins

1. Melhorar o README e corrigir números de testes.  
   Esforço: baixo.  
   Impacto: médio.

2. Adicionar `ALLOWED_ORIGINS` ao `.env.example`.  
   Esforço: baixo.  
   Impacto: alto.

3. Adicionar request ID aos logs.  
   Esforço: baixo.  
   Impacto: alto.

4. Destacar sempre a origem da vaga: real, IA ou simulada.  
   Esforço: baixo.  
   Impacto: alto.

5. Integrar botão “salvar vaga” diretamente ao tracker.  
   Esforço: baixo/médio.  
   Impacto: alto.

6. Adicionar timeout explícito para cada teste de integração.  
   Esforço: baixo.  
   Impacto: alto.

7. Adicionar build Docker ao CI.  
   Esforço: baixo.  
   Impacto: alto.

8. Adicionar smoke test para `/health`, upload e WebSocket.  
   Esforço: baixo/médio.  
   Impacto: alto.

---

# Não implementar agora

- Microsserviços.
- Kubernetes.
- Event sourcing.
- Multi-região.
- Data lake.
- Fine-tuning próprio.
- Sistema complexo de agentes autônomos.
- Recomendação com embeddings antes de haver histórico.
- Scraping em larga escala.
- Marketplace de cursos.
- Integrações com dezenas de plataformas.
- Arquitetura serverless fragmentada.
- Analytics avançado antes de resolver identidade e persistência.

Essas iniciativas adicionariam complexidade antes de o produto resolver os bloqueadores básicos de segurança, dados e publicação.

---

# 25. Arquivos mais importantes

1. `backend/main.py`  
   Responsabilidade: aplicação, CORS, erros e health check.  
   Problemas: sem autenticação, CORS fixo, sem readiness.  
   Importância: crítica.

2. `backend/session.py`  
   Responsabilidade: sessões, paths e escrita atômica.  
   Problemas: sessão anônima e persistência local.  
   Importância: crítica.

3. `backend/agents/maestro.py`  
   Responsabilidade: fluxo principal e roteamento.  
   Problemas: alto acoplamento a arquivos e estado conversacional.  
   Importância: crítica.

4. `backend/agents/scout.py`  
   Responsabilidade: busca, fallback e matching de vagas.  
   Problemas: dependência externa e ausência de catálogo persistente.  
   Importância: crítica para o produto.

5. `backend/artifacts.py`  
   Responsabilidade: proveniência e invalidação de artefatos.  
   Problemas: ainda baseado em arquivos.  
   Importância: alta.

6. `backend/routers/resume.py`  
   Responsabilidade: upload e análise de currículo.  
   Problemas: dados sensíveis ainda ficam em storage local.  
   Importância: crítica.

7. `backend/routers/applications.py`  
   Responsabilidade: candidaturas.  
   Problemas: JSON não escala e não há vínculo automático com vagas.  
   Importância: alta.

8. `backend/routers/chat.py`  
   Responsabilidade: WebSocket, replay e persistência do estado.  
   Problemas: fluxo central sem autenticação.  
   Importância: crítica.

9. `frontend/src/App.tsx`  
   Responsabilidade: shell e composição da aplicação.  
   Problemas: muitos fluxos concentrados em modais/estado.  
   Importância: alta.

10. `frontend/src/hooks/useWebSocket.ts`  
    Responsabilidade: conexão, streaming e reconexão.  
    Problemas: dependência central do produto.  
    Importância: crítica.

11. `frontend/src/lib/session.ts`  
    Responsabilidade: identidade anônima.  
    Problemas: não é mecanismo de segurança.  
    Importância: crítica.

12. `frontend/src/index.css`  
    Responsabilidade: todo o sistema visual.  
    Problemas: tamanho e possíveis overrides duplicados.  
    Importância: média/alta.

13. `docker-compose.yml`  
    Responsabilidade: execução local e composição dos serviços.  
    Problemas: sem backup, sem produção real, escala única.  
    Importância: alta.

14. `.github/workflows/*.yml`  
    Responsabilidade: CI.  
    Problemas: não há deploy, security scan ou Docker build.  
    Importância: alta.

---

# Conclusão final

O Import Vagas é um protótipo avançado, com uma base técnica considerável e diversos fluxos realmente implementados. O backend possui mais maturidade do que um protótipo comum: há validações, persistência atômica, isolamento de sessão, contratos de erro e testes de regras importantes.

Porém, ele ainda não é um produto pronto para produção pública. O maior problema não é falta de funcionalidades de IA; é segurança, identidade, persistência e operação.

O caminho mais simples é:

1. corrigir a execução completa dos testes;
2. garantir build limpo do frontend;
3. adicionar autenticação;
4. migrar dados críticos para PostgreSQL e storage privado;
5. adicionar rate limiting, logs e monitoramento;
6. publicar uma única instância Docker;
7. só depois evoluir busca, alertas e matching.

A próxima atividade recomendada é uma implementação separada de “Fase 0 — preparação para deploy”, começando por autenticação, persistência e validação automatizada.
