# Roteiro de Validação Manual — Firecrawl com chave e créditos reais

> Spec: `.kiro/specs/firecrawl-validacao-real` — Requisito 11 (tarefa 8.1).
> Este documento é **versionado** e deve ser executado por um validador a cada
> mudança relevante na integração com o Firecrawl (Scout/Curator/Firecrawl_Client).

## Objetivo

Confirmar, de ponta a ponta e consumindo **créditos reais** do Firecrawl, que:

- A busca de vagas (Scout) sinaliza corretamente o `status_busca` e a origem
  (`source`) de cada vaga.
- A busca de cursos (Curator) distingue recurso de **busca real** de
  **recomendação interna**.
- Salários, requisitos e atributos de curso vêm normalizados, com os marcadores
  de "não informado" quando ausentes.
- Apenas links de vagas **reais** com URL `http(s)` válida são clicáveis e abrem
  no navegador com segurança.
- Os casos de **sem créditos**, **erro** e **timeout** produzem o resultado
  esperado e visível ao usuário.

Esta validação é **manual e guiada** por depender de chave, créditos e serviço
externo. Os caminhos determinísticos (classificação, normalização, validação de
link) já são cobertos pelos testes automatizados (`backend/tests/`,
`frontend/src/components/ScoutReport.test.tsx`).

## Como registrar a execução

Preencha a data, o ambiente e o resultado de cada item ao final do documento, na
seção **Registro de execução**. Use ✅ (aprovado), ❌ (reprovado) ou ⏭️ (não
aplicável), e cole evidências (trechos do bloco `### dados`, prints e linhas de
log) quando o critério pedir.

---

## 1. Pré-requisitos — chave e créditos do Firecrawl

> _Requisito 11.1_

1. **Conta e créditos**
   - [ ] Conta no Firecrawl com **créditos disponíveis** (confirmar saldo > 0 no
     painel da conta antes de começar).
   - [ ] Anotar o saldo inicial de créditos para comparar com o saldo final.

2. **Chave de API**
   - [ ] Copiar `backend/.env.example` para `backend/.env` (se ainda não existir).
   - [ ] Definir `FIRECRAWL_API_KEY` em `backend/.env` com a chave **real**
     (nunca commitar a chave — `backend/.env` é ignorado pelo Git).
   - [ ] Definir `OPENAI_API_KEY` (ou `LLM_BASE_URL` + chave compatível) válidos,
     pois o fallback de vagas via LLM depende do provedor LLM.

3. **Parâmetros opcionais de busca** (em `backend/.env`, valores padrão entre
   parênteses):
   - [ ] `FIRECRAWL_TIMEOUT_SECONDS` (padrão `15`) — tempo limite por busca.
   - [ ] `FIRECRAWL_MAX_RESULTS` (padrão definido no Scout) — limite de resultados.

4. **Subir a aplicação**
   - [ ] Backend: a partir de `backend/`, executar `python run.py`
     (sobe em `http://127.0.0.1:8000`).
   - [ ] Frontend: a partir de `frontend/`, executar `npm run dev` e abrir a URL
     informada pelo Vite no navegador (Chrome ou Edge).
   - [ ] Confirmar `GET http://127.0.0.1:8000/health` → `200`
     `{"status":"online","agent":"Maestro"}`.

5. **Observabilidade**
   - [ ] Deixar o terminal do backend visível para acompanhar os logs JSON
     (procurar `event=firecrawl_search_success` no sucesso e logs de erro com
     `session_id` + tipo de erro na falha). Se preferir arquivo, ligar
     `LOG_TO_FILE=true` e acompanhar `logs/backend.log`.

**Critério de pré-requisito atendido:** backend e frontend no ar, `/health`
respondendo, chave real carregada e saldo de créditos anotado.

---

## 2. Busca completa de vagas (Scout) — registrar `status_busca`

> _Requisito 11.2_

### Passos

1. No chat do Maestro, garantir que há um perfil disponível (responder o quiz ou
   usar perfil já existente em `data/`).
2. Acionar a **esteira de busca de vagas** (Scout) pelo menu do chat e disparar
   uma busca com um filtro **específico e realista** (ex.: cargo + nível +
   localização que devem retornar vagas).
3. Aguardar o relatório do Scout ser renderizado no `ScoutReport`.
4. Localizar o bloco `### dados` da resposta do Scout e **registrar os campos**:
   - `status_busca:` (esperado neste cenário feliz: `real_success`)
   - `source` de cada vaga (esperado: `real`)
   - `fallback_simulado:`, `fallback_llm:`, `busca_degradada:`
   - `cache_hit:`, `max_resultados:`
5. Repetir com um filtro **propositalmente raro/inexistente** para observar
   `status_busca: real_empty` (nenhuma vaga real, sem erro).
6. (Opcional) Repetir uma busca idêntica para observar `cache_hit: true`.

### Valores possíveis de `status_busca` (registrar o observado)

| `status_busca`   | Quando ocorre                                                            |
|------------------|--------------------------------------------------------------------------|
| `real_success`   | Busca específica retornou vagas reais do Firecrawl                       |
| `real_empty`     | Nenhuma vaga real encontrada, sem erro/timeout/créditos                  |
| `real_degraded`  | Específica falhou (erro/timeout) e a busca ampla recuperou vagas reais   |
| `no_credits`     | Firecrawl sem créditos (`FirecrawlCreditError`)                          |
| `external_error` | Falha do provedor sem indicação de créditos (`FirecrawlProviderError`)  |
| `timeout`        | Busca excedeu `FIRECRAWL_TIMEOUT_SECONDS`                                |

**Registrar:** o `status_busca` observado em cada execução e os campos do bloco
`### dados`. Confirmar nos logs do backend o evento `firecrawl_search_success`
com `session_id` e contagem de resultados nos casos de sucesso.

---

## 3. Busca real de cursos (Curator) — registrar a origem dos recursos

> _Requisito 11.3_

### Passos

1. No chat, acionar a **esteira do Curator** (trilha de cursos/aprendizado) a
   partir de um perfil/lacunas de habilidades já existentes.
2. Aguardar o relatório de cursos ser renderizado.
3. Para **cada recurso** apresentado, registrar a origem:
   - **Busca real** (resultado do Firecrawl), ou
   - **Recomendação interna** (base `INTERNAL_RECOMMENDATIONS`, sinalizada na
     seção `### avisos` do relatório quando a cobertura externa é insuficiente).
4. Conferir nos logs do backend o evento `firecrawl_search_success` para as
   buscas de curso bem-sucedidas; em caso de falha de busca, conferir que o
   motivo foi registrado (campo `error` do `SearchOutcome`) e que a trilha foi
   complementada pela base interna.

**Registrar:** a contagem de recursos por origem (real vs. interno) e a presença
do aviso de recomendação interna quando houver complemento.

---

## 4. Critérios objetivos de aprovação

> _Requisito 11.4_

### 4.1 Salários e requisitos das vagas (Scout)

- [ ] Vagas reais **com** salário/benefícios na descrição exibem o valor extraído.
- [ ] Vagas **sem** salário exibem exatamente **"Não informado na descrição"** no
  campo `salario`.
- [ ] Vagas **sem** benefícios exibem exatamente **"Não informado na descrição"**
  no campo `beneficios`.
- [ ] `habilidades_correspondentes` e `habilidades_faltantes` listam as
  habilidades por vírgula, ou exibem **"Nenhuma"** quando vazias.
- [ ] `score_aderencia` de cada vaga é um inteiro entre **0 e 100**.
- [ ] `contagem_correspondencia` está no formato "X de Y habilidades correspondem".
- [ ] O relatório apresenta os **requisitos mais recorrentes** com a **contagem de
  ocorrências** de cada um.

**Aprovação:** todos os itens acima verdadeiros para a amostra inspecionada.

### 4.2 Exibição da origem dos dados

- [ ] Toda vaga tem `source ∈ {real, llm, simulated}` (exatamente um valor).
- [ ] Vagas `real` **não** exibem mensagem/badge de fallback
  (`fallback_reason`/`fallback_message` vazios).
- [ ] Vagas `llm` exibem badge **"Sugerida por IA"** e mensagem de "não
  verificada".
- [ ] Vagas `simulated` exibem badge **"Simulada"** e a mensagem de fallback
  correspondente.
- [ ] No Curator, cada recurso permite distinguir **busca real** de
  **recomendação interna** (aviso visível quando há complemento interno).

**Aprovação:** a origem de cada item é inequívoca na interface e coerente com o
bloco `### dados`.

### 4.3 Abertura de links reais no navegador

- [ ] Vaga `real` com URL `http(s)` válida exibe **link clicável**.
- [ ] Clicar no link **abre a URL real no navegador**, em **nova aba**, com
  `rel="noopener noreferrer"` (verificar no DOM via DevTools).
- [ ] Vagas `llm` e `simulated` **não** exibem link clicável (o `link` aparece
  como texto não navegável, ex.: "Sugestao gerada por IA (nao verificada)").
- [ ] Vaga `real` cujo `link` **não** seja `http(s)` válida **não** exibe link
  clicável.

**Aprovação:** somente vagas reais com URL válida são clicáveis e abrem o destino
real com segurança; nenhuma URL de IA/simulada é clicável.

---

## 5. Resultado esperado — sem créditos, erro e timeout

> _Requisito 11.5_

Para forçar cada cenário, use uma das estratégias indicadas. Após cada teste,
**restaure** a configuração original.

### 5.1 Ausência de créditos (`no_credits`)

- **Como forçar:** usar uma conta/chave **sem créditos** (saldo zerado) ou esgotar
  a cota; o Firecrawl deve sinalizar exaustão de créditos.
- **Resultado esperado:**
  - [ ] `status_busca: no_credits` no bloco `### dados`.
  - [ ] `fallback_reason: firecrawl_no_credits`.
  - [ ] A interface exibe vagas de fallback (LLM `source: llm`, com
    `fallback_llm: true`; ou simuladas `source: simulated`,
    `fallback_simulado: true` se o LLM também falhar) — **nunca** vagas reais
    inexistentes.
  - [ ] Log de erro no backend com `session_id` e o tipo do erro (crédito).
  - [ ] Nenhuma vaga de fallback aparece como link clicável.

### 5.2 Erro externo (`external_error`)

- **Como forçar:** usar uma `FIRECRAWL_API_KEY` **inválida**, ou cortar a
  conectividade de rede durante a busca (provoca falha do provedor sem indicação
  de créditos).
- **Resultado esperado:**
  - [ ] `status_busca: external_error`.
  - [ ] `fallback_reason: firecrawl_error` e
    `fallback_message: "Nao conseguimos buscar vagas reais agora..."`.
  - [ ] Fallback via LLM ou simulação acionado conforme disponibilidade.
  - [ ] Log JSON de erro no backend com `session_id` e tipo do erro.
  - [ ] Nenhuma vaga de fallback é clicável.

### 5.3 Timeout (`timeout`)

- **Como forçar:** reduzir `FIRECRAWL_TIMEOUT_SECONDS` para um valor muito baixo
  (ex.: `0.01`) em `backend/.env` e reiniciar o backend, de modo que a busca
  exceda o tempo limite.
- **Resultado esperado:**
  - [ ] `status_busca: timeout`.
  - [ ] `fallback_reason: firecrawl_timeout` e mensagem de tempo limite excedido.
  - [ ] Fallback via LLM ou simulação acionado.
  - [ ] Nenhuma vaga de fallback é clicável.
  - [ ] Restaurar `FIRECRAWL_TIMEOUT_SECONDS` ao valor original após o teste.

### 5.4 (Complementar) Busca degradada (`real_degraded`)

- **Como observar:** quando a busca específica falha por erro/timeout, mas a busca
  ampla recupera vagas **reais**.
- **Resultado esperado:**
  - [ ] `status_busca: real_degraded` e `busca_degradada: true`.
  - [ ] `aviso_degradacao` preenchido (alerta de que as vagas vêm de busca ampla).
  - [ ] `fallback_simulado: false` (as vagas são reais).
  - [ ] Links das vagas reais permanecem clicáveis quando a URL é válida.

---

## Registro de execução

| Item | Cenário                         | Resultado | Evidência / observação |
|------|---------------------------------|-----------|------------------------|
| 1    | Pré-requisitos (chave/créditos) |           |                        |
| 2    | Scout `real_success`            |           | `status_busca:`        |
| 2    | Scout `real_empty`              |           | `status_busca:`        |
| 3    | Curator origem dos recursos     |           | reais: __ / internos: __ |
| 4.1  | Salários e requisitos           |           |                        |
| 4.2  | Exibição da origem              |           |                        |
| 4.3  | Links reais no navegador        |           |                        |
| 5.1  | Sem créditos (`no_credits`)     |           |                        |
| 5.2  | Erro (`external_error`)         |           |                        |
| 5.3  | Timeout (`timeout`)             |           |                        |
| 5.4  | Degradada (`real_degraded`)     |           |                        |

- **Data da execução:** ____/____/______
- **Validador:** __________________________
- **Ambiente:** SO __________ / Navegador __________ / Commit ______________
- **Saldo de créditos:** inicial ______ → final ______
- **Resultado geral:** ☐ Aprovado ☐ Reprovado
- **Notas:**
