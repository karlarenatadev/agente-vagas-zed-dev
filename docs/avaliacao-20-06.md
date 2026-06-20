## 1. Visão geral do diagnóstico

O projeto **"import vagas"** é uma plataforma multi-agente bem arquitetada para suportar jornada de desenvolvimento de carreira. O backend apresenta **hardening avançado** com logging estruturado, persistência atômica e tratamento robusto de erros. O frontend tem **interface visual polida** com suporte a responsividade e acessibilidade. Porém, o projeto tem **lacunas críticas de testes**, **risco moderado em segurança de dados**, **falta de integração clara entre componentes** e **ausência de padrão de erro normalizado no frontend**. Estado geral: **MVP funcional mas frágil para escala**.

---

## 2. Pontos fortes

### Backend

- ✅ **Logging estruturado em JSON** centralizado (`logging_config.py`) com contexto de sessão em todos os eventos
- ✅ **Persistência atômica** com locks por sessão e `write_text_atomic_async` evitando corrupção em escritas concorrentes
- ✅ **Estado do WebSocket recuperável** em `data/sessions/{id}/chat_state.json` com restauração automática após reconexão
- ✅ **Tratamento global de exceções** no FastAPI (422 validation, 500 internal) sem expor stack traces
- ✅ **Firecrawl SDK oficial** migrado de CLI/subprocess para execução segura fora do Event Loop
- ✅ **Upload de currículo endurecido** com limite de tamanho (5MB), validação de Content-Type e Magic Numbers
- ✅ **73 testes automatizados** incluindo stress test de 50 escritas concorrentes

### Frontend

- ✅ **Responsividade em múltiplas telas** com breakpoints claros (mobile/tablet/desktop)
- ✅ **Acessibilidade básica forte**: modal focus trap, aria-labels, keyboard navigation (Tab, Escape)
- ✅ **Lazy loading de componentes** com Suspense boundaries reduzindo bundle inicial
- ✅ **Animações fluidas** com Framer Motion (fade-in, pulse, expansão suave) sem impacto perceptível
- ✅ **Pipeline visual intuitivo** (Career Arcade) com 6 fases recolhíveis e barra de progresso
- ✅ **WebSocket com streaming token a token** mantendo UX fluida durante processamento LLM

### Arquitetura

- ✅ **Separação clara de responsabilidades**: Maestro (orquestrador), Scout (vagas), Curator (cursos), Coach (entrevista)
- ✅ **Fluxo de dados transparente**: currículo → perfil → vaga → match → sugestões → PDI → entrevista
- ✅ **Estado local em Markdown legível** sem banco de dados (simplicidade operacional)
- ✅ **Configuração centralizada** via `.env` e `config.py` com fallbacks sensatos

### Produto

- ✅ **Proposta de valor clara**: encontrar vagas, aprender, praticar entrevistas em um fluxo conversacional
- ✅ **Jornada do usuário bem mapeada**: 7-pergunta quiz → menu → ação especializada → resultado
- ✅ **Mock server funcional** (`mock_server.py`) para testes sem API keys
- ✅ **Documentação estruturada**: personas, skills, plano técnico, README detalhado

---

## 3. Pontos críticos

### 🔴 Críticos (Impedem produção)

1. **Falta de testes E2E**: sem testes de fluxo completo (upload currículo → quiz → scout → match → PDI)
2. **Contrato de erro incoerente no frontend**: não há tratamento visual consistente de erros 422/500
3. **Persistência de dados sensíveis sem encriptação**: currículo em plaintext em `/data/*.md`
4. **Ausência de validação de integridade em rotas críticas**: match e tailoring não validam que análise de vaga existe antes de processar
5. **Estado do app não sincroniza entre abas**: múltiplas abas podem sobrescrever estado em `chat_state.json`

### 🟠 Importantes (Prejudicam confiabilidade)

1. **Lógica de agentes duplicada**: Curator e Coach têm parsing LLM inline sem abstração reutilizável
2. **Sem retry automático em falhas de LLM**: timeouts não têm backoff exponencial
3. **Routers sem validação em cascata**: `job_description.py` não valida se já existe análise antes de sobrescrever
4. **Performance de Scout pode travar UI**: busca de vagas pode levar >10s sem feedback de progresso
5. **Mock server desincronizado do real**: dados mock não refletem contratos reais da API

### 🟡 Moderados (Reduzem UX/estabilidade)

1. **Responsividade do modal de upload**: CSS não cobre dispositivos muito pequenos (<320px)
2. **Sem cache de análises**: reanalisar mesma vaga gera nova chamada LLM
3. **Controle de concorrência fraco**: múltiplas requisições simultâneas podem causar race conditions em leitura de perfil
4. **Instruções de personas muito longas**: Maestro.py (46KB) e Curator.py (47KB) com lógica espalhada
5. **Falta de CI/CD**: sem pipeline GitHub Actions para validar testes antes de merge

---

## 4. Problemas por área

### Backend

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| Sem validação de cascata em rotas | 🔴 | `resume_match.py` processa match sem verificar se análise de vaga foi salva |
| Lógica LLM duplicada entre agentes | 🟠 | Coach.py e Curator.py fazem parsing de JSON do LLM sem abstração compartilhada |
| Sem retry em falhas externas | 🟠 | Firecrawl ou OpenAI timeout não têm backoff exponencial |
| Logs não incluem tempo de latência | 🟡 | Eventos de agente não registram duração (importante para debug de performance) |
| Erro de LLM genérico demais | 🟡 | `LLMProviderError` não diferencia rate limit, timeout, auth error |
| SQL injection em paths não relevante mas prática ruim | 🟡 | Construção de caminhos deveria usar `Path` mais rigorosamente |

### Frontend

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| Sem tratamento visual de erro 422 | 🔴 | Validação falha sem feedback ao usuário (apenas console.error) |
| Múltiplas abas = estado corrompido | 🔴 | Duas abas abertas podem sobrescrever `chat_state.json` causando perda de contexto |
| Spinner de carregamento faltando em Scout | 🟠 | Busca de vagas pode levar >10s mas UI só mostra "Maestro em execução" |
| Modal não fecha em erro | 🟠 | Se upload falha, modal fica aberto sem opção de fechar ou tentar novamente |
| Sem persistência de filtro de data | 🟡 | Usuário seleciona "7 dias" mas ao recarregar volta para "Todas" |
| TypeScript `any` em tipos críticos | 🟡 | `Session`, `Message` usam `Record<string, any>` perdendo type safety |
| Sem teste de acessibilidade automático | 🟡 | Aria-labels presentes mas sem axe-core ou similar em CI |

### Agentes

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| Curator parsing JSON inline | 🟠 | 47KB de lógica sem separação entre orquestração e análise |
| Coach não valida entrada do usuário | 🟡 | Aceita respostas vazias sem re-perguntar |
| Scout sem fallback em vaga ruim | 🟡 | Se Firecrawl retorna vaga sem requisitos, Scout não trata gracefully |
| Maestro muito grande | 🟡 | 46KB de orquestração, menu, quiz tudo em um arquivo |
| Sem agente de error recovery | 🟡 | Se qualquer agente falha, Maestro repete a última ação em loop |

### Dados e Persistência

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| Dados sensíveis em plaintext | 🔴 | Currículo, perfil pessoal em `/data/*.md` sem encriptação |
| Sem validação de schema ao carregar | 🟠 | Se JSON de perfil é corrompido, carregamento não valida estrutura esperada |
| Sem versionamento de arquivos | 🟡 | Histórico de mudanças perdido (sem git tracking de `/data`) |
| Sem backup automático | 🟡 | Se `/data` apaga, tudo se perde |
| Concorrência em leitura fraca | 🟡 | Múltiplas requests podem ler perfil desincronizado |

### Segurança

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| API keys em `.env` não ofuscado em logs | 🟠 | Se admin faz `echo $OPENAI_API_KEY`, pode vazar em histórico |
| Sem rate limiting na API | 🟠 | Usuário malicioso pode fazer 1000 requests/s causando DOS |
| Upload de currículo sem antivirus | 🟡 | Arquivo .docx malicioso não é verificado |
| CORS permite localhost:3000/5174 | 🟡 | Em produção, localhost não deve estar listado |
| Sem HTTPS/TLS em transporte | 🟡 | Se backend e frontend não estão em HTTPS, tokens em plaintext |
| .env.example vazio | 🟡 | Novo desenvolvedor não sabe que chaves são obrigatórias |

### Testes

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| Sem testes E2E | 🔴 | Nenhum teste de fluxo completo (quiz → scout → match → pdi) |
| Sem testes de integração frontend-backend | 🔴 | WebSocket apenas testado via manual |
| Testes apenas em backend | 🟠 | 73 testes para Python mas zero para TypeScript/React |
| Sem testes de recuperação de estado | 🟠 | Restauração de `chat_state.json` não é testada sistematicamente |
| Sem testes de concorrência no frontend | 🟡 | Múltiplas abas/workers não testados |
| Mocks desincronizados | 🟡 | Mock server não reflete mudanças reais na API |

### UX/UI

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| Sem indicador de que busca está em andamento | 🟠 | Scout pode demorar 15s e UI só mostra "Maestro" genérico |
| Pergunta do quiz pode ser cortada em mobile | 🟡 | Texto longo em tela pequena não quebra bem |
| Sem atalho claro para "voltar ao menu" | 🟡 | Usuário em Scout precisa digitar "D" sem orientação |
| Sem histórico de conversas | 🟡 | Recarregar perde chat (apenas estado persiste, não mensagens) |
| Tooltip ausente em ícones da topbar | 🟡 | Icon button sem label em hover |
| Sem dark mode toggle (assume sempre dark) | 🟡 | Tema hardcoded, sem opção do usuário |

### Produto

| Problema | Severidade | Descrição |
|----------|-----------|-----------|
| MVP sente incompleto sem testes | 🔴 | Demo não é segura para apresentar (pode falhar em vivo) |
| Sem documentação de casos de uso | 🟠 | Como um usuário real deveria usar o sistema? Workflow não documentado |
| Sem analytics | 🟡 | Não sabemos se Scout está encontrando vagas boas ou se Coach é efetivo |
| Feature de "salvar candidatura" não está integrada | 🟡 | Tracker existe mas não persiste dados entre sessões |
| Sem onboarding claro | 🟡 | Usuário novo não sabe por onde começar além de "responder quiz" |

---

## 5. Priorização

| P | Problema | Impacto | Esforço | Recomendação |
|---|----------|--------|--------|---------------|
| **P0** | Sem testes E2E | Alto: demo pode falhar | Alto (5-7d) | Criar 5-7 testes de fluxo crítico com Playwright |
| **P0** | Múltiplas abas = estado corrompido | Crítico: dados perdidos | Médio (2-3d) | Usar `sessionStorage` + warning se múltiplas abas abertas |
| **P0** | Contrato de erro incoerente | Alto: UX ruim em falha | Médio (2-3d) | Criar toast/banner global para 422/500, testar em todos routers |
| **P0** | Dados sensíveis sem encriptação | Crítico: privacidade | Médio (3-4d) | Encriptar `/data/*.md` com chave local (libsodium) |
| **P1** | Sem validação de cascata | Médio: consistência | Baixo (1-2d) | Adicionar schema validation com Pydantic em match/tailoring |
| **P1** | Lógica agente duplicada (JSON parsing) | Médio: manutenção | Médio (2-3d) | Extrair `parse_llm_json()` em `backend/utils/llm.py` |
| **P1** | Sem retry em LLM | Médio: confiabilidade | Médio (2-3d) | Implementar backoff exponencial com tenacity |
| **P1** | Sem rate limiting | Médio: segurança | Baixo (1d) | Adicionar `slowapi` ao FastAPI |
| **P1** | Sem CI/CD | Médio: qualidade | Médio (2-3d) | Criar `.github/workflows/test.yml` com pytest + coverage |
| **P2** | Mock server desincronizado | Baixo: dev experience | Médio (2d) | Autogerar mocks de schema OpenAPI |
| **P2** | Performance Scout sem feedback | Baixo: UX | Baixo (1d) | Adicionar status "Procurando vagas..." com spinner |
| **P2** | Instruções de personas muito grandes | Baixo: manutenção | Médio (3d) | Refatorar Maestro.py e Curator.py em módulos menores |
| **P3** | Sem cache de análises | Muito baixo: nice-to-have | Médio (2d) | Redis cache opcional para análises frequentes |
| **P3** | Sem histórico de conversas | Muito baixo: nice-to-have | Médio (2d) | Persist messages array em JSON além de WebSocket state |
| **P3** | CORS permite localhost | Baixo: produção | Muito baixo (<1d) | Parametrizar CORS via `.env` |

---

## 6. Próximas 3 rodadas recomendadas

### 🎯 Rodada 1: Estabilização Crítica (1-2 semanas)

**Objetivo**: Tornar o MVP seguro para demo/produção básica.

**Arquivos prováveis envolvidos**:

- `backend/routers/chat.py` (estado de múltiplas abas)
- `frontend/src/hooks/useWebSocket.ts` (sessionStorage)
- `backend/utils/error.py` (novo)
- `frontend/src/lib/toast.tsx` (novo)
- `.github/workflows/test.yml` (novo)

**O que fazer**:

1. ✅ Implementar detecção de múltiplas abas com `sessionStorage` + aviso ao usuário
2. ✅ Criar tratador global de erro (422/500) no frontend com toast/banner
3. ✅ Adicionar validação de schema Pydantic em `resume_match.py` e `resume_tailoring.py`
4. ✅ Implementar encriptação de `/data/*.md` com chave local (libsodium Python)
5. ✅ Criar CI/CD básico (pytest + coverage report)
6. ✅ Escrever 5-7 testes E2E críticos (quiz → scout → match → pdi) com Playwright

**O que NÃO fazer**:

- ❌ Refatorar arquitetura de agentes (economia de tempo)
- ❌ Implementar features novas (foco em estabilidade)
- ❌ Migrar para banco de dados (mantém simplicidade local)

**Critério de aceite**:

- [ ] 0 erros em testes E2E
- [ ] Todo erro 422/500 exibe mensagem amigável ao usuário
- [ ] Currículo encriptado em repouso
- [ ] CI verde em merge (pytest + Playwright)
- [ ] Documentação de "Como executar testes"

---

### 🎯 Rodada 2: Confiabilidade e Performance (2-3 semanas)

**Objetivo**: Reduzir erros em produção e melhorar feedback ao usuário.

**Arquivos prováveis envolvidos**:

- `backend/agents/base.py` (retry logic)
- `backend/utils/llm.py` (novo - parse compartilhado)
- `backend/agents/coach.py`, `curator.py` (refatoração)
- `frontend/src/components/ChatTerminal.tsx` (loading states)
- `backend/main.py` (rate limiter)

**O que fazer**:

1. ✅ Extrair `parse_llm_json()` reutilizável em `backend/utils/llm.py`
2. ✅ Refatorar Coach e Curator para usar função compartilhada
3. ✅ Implementar retry com backoff exponencial (tenacity) em chamadas LLM
4. ✅ Adicionar rate limiting (slowapi) na API
5. ✅ Melhorar feedback visual: "Procurando vagas...", spinner em Scout
6. ✅ Implementar logging de latência em eventos de agente

**O que NÃO fazer**:

- ❌ Mover para Redis/cache complexo
- ❌ Implementar versionamento de dados
- ❌ Mudar persistência para banco de dados

**Critério de aceite**:

- [ ] Retry automático em Firecrawl/OpenAI timeout com backoff exponencial
- [ ] Rate limiter respondendo 429 em >100 req/min
- [ ] Latência de agente aparecendo em logs
- [ ] Scout mostrando "Procurando vagas..." de forma visual
- [ ] Testes E2E com falhas simuladas passando

---

### 🎯 Rodada 3: Qualidade e Manutenibilidade (2-3 semanas)

**Objetivo**: Código mais legível, testável e preparado para escala.

**Arquivos prováveis envolvidos**:

- `backend/agents/maestro.py` (splitting)
- `backend/agents/curator.py` (splitting)
- `frontend/src/types.ts` (melhorar type safety)
- `backend/tests/` (novos testes integração)
- `docs/TESTING.md` (novo)

**O que fazer**:

1. ✅ Dividir Maestro.py (46KB) em módulos: `orchestrator.py`, `quiz.py`, `menu.py`
2. ✅ Dividir Curator.py (47KB) em módulos: `course_finder.py`, `skill_analyzer.py`
3. ✅ Remover `any` de tipos críticos em frontend (Session, Message)
4. ✅ Criar testes de integração backend-frontend (WebSocket state sync)
5. ✅ Documentar fluxo de teste em `docs/TESTING.md`
6. ✅ Autogerar mocks de OpenAPI para desincronizar do real

**O que NÃO fazer**:

- ❌ Reescrever frontend em outro framework
- ❌ Implementar auth/login
- ❌ Adicionar features de payment

**Critério de aceite**:

- [ ] Cada arquivo <2KB (agentes modularizados)
- [ ] Zero `any` em tipos de Session/Message
- [ ] 85%+ code coverage em backend (foi 73%)
- [ ] Testes de integração WebSocket passando
- [ ] Documentação de testes clara

---

## 7. Checklist de estabilização

### ✅ Testes

- [ ] 5-7 testes E2E (Playwright) cobrindo fluxo completo
- [ ] Testes unitários para funções críticas (match, tailoring, PDI scoring)
- [ ] Testes de recuperação de estado (restaurar `chat_state.json`)
- [ ] Testes de concorrência (múltiplas escritas simultâneas)
- [ ] CI/CD rodando em push com pytest + Playwright

### ✅ Segurança

- [ ] Dados sensíveis (`*.md` em `/data`) encriptados em repouso
- [ ] `.env.example` preenchido com variáveis obrigatórias
- [ ] CORS parametrizado (não hardcoded localhost)
- [ ] Rate limiting ativo (429 em >100 req/min)
- [ ] Sem API keys em logs (masking)

### ✅ Confiabilidade

- [ ] Retry com backoff em Firecrawl e OpenAI
- [ ] Detecção e aviso de múltiplas abas
- [ ] Validação de schema em cascata (match, tailoring, PDI)
- [ ] Todas as rotas retornam 422 em validação e 500 em erro interno
- [ ] Logs estruturados com latência em eventos críticos

### ✅ UX/UI

- [ ] Erro 422/500 exibe toast/banner ao usuário
- [ ] Scout mostra "Procurando vagas..." com spinner
- [ ] Modal fecha gracefully em erro
- [ ] Quiz não corta texto em dispositivos pequenos
- [ ] Atalho para "Voltar ao menu" está documentado

### ✅ Performance

- [ ] Scout não trava UI (max 15s com feedback visual)
- [ ] Lazy loading de componentes ativo (ChatTerminal, PdiPlan)
- [ ] Gzip habilitado no FastAPI
- [ ] Bundle do frontend <300KB (gzipped)

### ✅ Documentação

- [ ] README atualizado com seção "Troubleshooting"
- [ ] `docs/TESTING.md` explicando como rodar testes
- [ ] Diagrama de fluxo de estado (Maestro → agentes)
- [ ] Schema de arquivos `/data/*.md` documentado
- [ ] `.env.example` comentado

### ✅ Código

- [ ] Zero `TODO` ou `FIXME` não rastreado em issues
- [ ] Sem `console.log()` em produção (remover ou usar logger)
- [ ] Sem imports unused
- [ ] Sem `any` em tipos críticos
- [ ] Linter (ESLint, Pylint) rodando sem warnings

### ✅ Operacional

- [ ] Mock server sincronizado com real
- [ ] Deploy local funciona: `cd backend && python run.py` + `cd frontend && npm run dev`
- [ ] Sem dependências de sistema não documentadas
- [ ] Logs podem ser rotacionados (max size configurável)
- [ ] Sem estado persistido fora de `/data` (isolamento)

---

## 8. Riscos antes de publicar no GitHub ou portfólio

### 🔴 Críticos

1. **Currículo em plaintext**
   - **Risco**: Dados sensíveis expostos se repo é clonado/forked
   - **Impacto**: Violação de privacidade, reputação prejudicada
   - **Ação**: Encriptar `/data/*.md` com libsodium ANTES de qualquer publicação
   - **Validação**: Verificar que arquivo `.md` não é legível sem chave

2. **Sem testes E2E documentados**
   - **Risco**: Revisor tenta rodar, sistema falha em vivo
   - **Impacto**: Credibilidade perdida no portfolio
   - **Ação**: Criar `docs/TESTING.md` com instruções step-by-step
   - **Validação**: Testar em máquina limpa (sem cache, sem histórico)

3. **Múltiplas abas = estado corrompido**
   - **Risco**: Reviewer abre em 2 abas, sistema quebra
   - **Impacto**: Aparenta ser bugado
   - **Ação**: Implementar bloqueio/aviso de múltiplas abas ANTES de publicar
   - **Validação**: Testar abrir em 3 abas simultâneas

4. **API keys expostas em git**
   - **Risco**: Se houver algum `.env` commitado, chaves vazadas
   - **Impacto**: Abuso da conta, custos inesperados
   - **Ação**: Verificar `.git log` e `.gitignore`, remover histórico se necessário
   - **Validação**: `git log --full-history -- .env` deve estar vazio

### 🟠 Importantes

5. **Sem CI/CD visível**
   - **Risco**: Revisor não vê testes rodando
   - **Impacto**: Aparenta projeto "ad hoc"
   - **Ação**: Adicionar `.github/workflows/test.yml` que rode pytest + coverage
   - **Validação**: Badge de status no README

6. **Mock server desincronizado**
   - **Risco**: Instruções dizem "teste sem API keys" mas mock falha
   - **Impacto**: Novo usuário não consegue explorar
   - **Ação**: Validar mock against real API responses
   - **Validação**: Rodar testes com mock_server.py

7. **CORS hardcoded com localhost**
   - **Risco**: Se repo é deployado em outro domínio, CORS quebra
   - **Impacto**: Frontend não fala com backend em staging/produção
   - **Ação**: Parametrizar CORS via `.env`
   - **Validação**: Testar com `ALLOWED_ORIGINS=https://example.com`

8. **Documentação de personas muito técnica**
   - **Risco**: Revisor não entende fluxo sem ler 50KB de instruções
   - **Impacto**: Projeto pareça complexo demais
   - **Ação**: Criar `docs/ARCHITECTURE.md` resumido (1-2 páginas)
   - **Validação**: Alguém sem contexto consegue ler e entender?

9. **Sem versionamento de arquivo**
   - **Risco**: Versão commitada de `*.md` em `/data` pode vazar dados
   - **Impacto**: Privacidade
   - **Ação**: Verificar `.gitignore` está correto e rodado `git rm -r --cached data/`
   - **Validação**: `git log --full-history -- data/*.md` deve estar vazio

### 🟡 Moderados

10. **Sem onboarding visual**
    - **Risco**: Usuário novo não sabe por onde começar
    - **Impacto**: Abandono rápido
    - **Ação**: Adicionar step-by-step na tela inicial ou tooltip
    - **Validação**: Testador novo consegue completar fluxo sem ajuda?

11. **Erro genérico "Erro no processamento"**
    - **Risco**: Usuário não sabe o que deu errado
    - **Impacto**: Frustração
    - **Ação**: Diferenciar tipos de erro em mensagens (timeout, API limit, validation)
    - **Validação**: Cada tipo de erro tem mensagem específica

12. **Sem analytics / tracking**
    - **Risco**: Não sabe se produto está sendo usado efetivamente
    - **Impacto**: Impossível iterar baseado em dados
    - **Ação**: Adicionar eventos básicos (quiz completed, scout ran, etc.)
    - **Validação**: Dashboard simples mostrando funnel

13. **Sem HTTPS/TLS em documentação**
    - **Risco**: Demo em HTTP expõe tokens em plaintext
    - **Impacto**: Não seguro para dados reais
    - **Ação**: Documentar que produção DEVE usar HTTPS
    - **Validação**: README tem seção de "Security Considerations"

14. **Sem tratamento de token expirado**
    - **Risco**: Se session_id expira, usuário fica sem feedback
    - **Impacto**: UX ruim
    - **Ação**: Implementar session timeout com re-auth
    - **Validação**: Testar deixar inativo >1 hora

---

## Sumário Executivo

### Estado atual

Projeto bem arquitetado com **backend robusto** mas **lacunas críticas** em testes, segurança de dados e sincronização de estado. **MVP funcional** mas **não pronto para produção/portfólio** sem as correções listadas.

### Caminho para MVP estável (3-4 semanas)

1. **Semana 1**: Testes E2E, encriptação de dados, CI/CD
2. **Semana 2**: Validação em cascata, retry automático, melhor feedback visual
3. **Semana 3**: Refatoração de agentes, documentação, review final

### Esforço estimado

- **P0 críticos**: 5-7 dias
- **P1 importantes**: 8-10 dias
- **P2/P3**: 5-7 dias
- **Total**: 3-4 semanas com 1-2 engenheiros

### Risco mais alto

**Dados sensíveis em plaintext** — deve ser encriptado ANTES de qualquer publicação ou demo.
