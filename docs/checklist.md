# Checklist técnico consolidado — Recoloca IA

Última avaliação: 2026-06-27

Branch e referência analisadas: `main` em `75c7fa1`

Escopo revisto: backend FastAPI, frontend React, WebSocket, agentes, persistência
Markdown/JSON, integração Firecrawl, Docker, workflows de CI e documentação.

## 1. Diagnóstico executivo

O projeto está em um estágio de **MVP local funcional e bem testado**, com boa
separação de agentes, isolamento lógico por sessão, escrita atômica e tratamento
de vários cenários de falha.

O projeto **ainda não está pronto para exposição pública com dados reais**. Os
principais bloqueadores são:

1. ausência de autenticação e autorização sobre dados pessoais;
2. artefatos derivados podem permanecer válidos visualmente após a alteração das
   entradas que os originaram;
3. ausência de limites, rate limiting, expiração e descarte completo por sessão;
4. ausência de E2E automatizado e validação real do Firecrawl;
5. proteções de CI ainda incompletas para testes frontend.

Decisão de release: manter como aplicação local/controlada até concluir os itens
P0. Para publicação, o cabeçalho `X-Session-Id` não pode ser tratado como
mecanismo de identidade ou autorização.

## 2. Validação reproduzida nesta avaliação

1. Backend
   - Estado: aprovado.
   - Comando: `backend/.venv/Scripts/python.exe -m pytest backend/tests -q`.
   - Resultado: **250 passed**, 1 warning, em 47,48 s.
   - Warning: `PendingDeprecationWarning` do Starlette para `import multipart`.

2. Frontend
   - Estado: aprovado.
   - Comando: `npm run test -- --run`.
   - Resultado: **6 arquivos e 56 testes passando**.
   - Comando: `npm run lint`.
   - Resultado: sem erros.
   - Comando: `npm run build`.
   - Resultado: sem erros.
   - Bundle principal: **379,67 kB**; gzip: **119,68 kB**.
   - Chunk do chat: **174,28 kB**; gzip: **52,40 kB**.

3. Dependências Python
   - Estado: aprovado.
   - Comando: `python -m pip check`.
   - Resultado: nenhuma dependência quebrada.

4. Cobertura
   - Estado: não mensurada.
   - Erro: o ambiente virtual atual não tem `pytest-cov` instalado, embora a
     dependência esteja declarada em `backend/requirements-dev.txt`; o pytest
     rejeitou `--cov`.
   - Risco: não existe limiar de cobertura bloqueante no CI.

5. Docker
   - Estado: não reproduzido nesta máquina.
   - Erro: executável `docker` indisponível no ambiente atual.
   - Observação: Dockerfiles, `.dockerignore`, Nginx e Compose foram revisados
     estaticamente; o `.dockerignore` raiz exclui `backend/.env`, `data/` e logs.

6. Firecrawl e LLM reais
   - Estado: bloqueado por ambiente externo.
   - `OPENAI_API_KEY`, `FIRECRAWL_API_KEY` e `LLM_BASE_URL` não estão configurados
     com valores utilizáveis neste ambiente.
   - O roteiro está em `docs/firecrawl-validacao-manual.md`.

7. Repositório e privacidade atual
   - O worktree contém as entregas M0-01/M0-02 ainda não commitadas, sem
     artefatos de runtime staged ou rastreados.
   - Apenas `data/README.md` está rastreado em `data/`.
   - `backend/.env` está ignorado pelo Git.
   - Não foi encontrado `TODO`, `FIXME`, `XXX` ou `HACK` no código rastreado.

8. Data Guard
   - Estado: aprovado.
   - Comando: `python -m unittest discover -s scripts/tests -p "test_*.py" -v`.
   - Resultado: **8 testes passando**.
   - Comando: `python scripts/validate_data_guard.py`.
   - Resultado: **153 arquivos rastreados/staged verificados**, sem violação.
   - Verificação adicional: **14 arquivos novos/modificados** da rodada
     inspecionados pelo mesmo scanner, sem violação.

## 3. Critério de criticidade

1. P0 — bloqueia publicação ou pode expor dados, permitir abuso, quebrar a
   integridade da jornada ou apresentar resultado obsoleto como atual.
2. P1 — lacuna funcional relevante ou ausência de teste/contrato que reduz
   significativamente a confiabilidade do MVP.
3. P2 — qualidade, desempenho, observabilidade e manutenção.
4. P3 — documentação e acabamento sem impacto imediato na execução.

## 4. Pendências priorizadas

### P0 — Bloqueadores de produção

#### P0-01 — Implementar identidade, autenticação e autorização

- [ ] Estado: não iniciado.
- Evidência:
  - todas as rotas REST confiam em `X-Session-Id` fornecido pelo cliente;
  - o WebSocket recebe `session_id` pela query string;
  - não existe autenticação, vínculo de propriedade ou autorização;
  - chamadas sem ID compartilham `data/sessions/_default/`;
  - IDs inválidos são transformados em vez de rejeitados, permitindo colisões
    como IDs diferentes que resultam no mesmo nome sanitizado;
  - o WebSocket aceita a conexão antes de validar identidade ou origem.
- Risco: conhecimento ou colisão de um ID permite leitura e mutação dos
  artefatos daquela sessão; a sessão default pode misturar clientes sem header.
- Critérios de aceite:
  - identidade emitida e validada no servidor;
  - autorização aplicada a todas as rotas REST e ao WebSocket;
  - sessão default desabilitada em ambiente público;
  - IDs inválidos rejeitados, sem normalização que produza colisão;
  - validação de `Origin` no WebSocket;
  - testes negativos provando que uma identidade não acessa outra;
  - modo local anônimo, se mantido, explicitamente separado por configuração.

#### P0-02 — Corrigir linhagem e invalidação de artefatos derivados

- [ ] Estado: falha funcional confirmada por inspeção.
- Evidência:
  - reanalisar currículo ou vaga remove match, tailoring e PDI, mas preserva
    `reconciliation.md` e entrevista;
  - recalcular match não invalida reconciliação, tailoring, PDI ou entrevista;
  - aplicar sugestões ao perfil e alterar o foco não invalida relatórios
    dependentes;
  - `ApplicationPipeline` considera uma etapa concluída principalmente pela
    existência/conteúdo do arquivo, sem provar que ele deriva das entradas atuais.
- Risco: a interface pode apresentar score, foco, sugestões ou PDI antigos como
  atuais depois que perfil, currículo, vaga ou match mudaram.
- Critérios de aceite:
  - definir a matriz de dependência:
    - perfil → vagas, cursos, match, reconciliação, tailoring, PDI e entrevista;
    - currículo → match, reconciliação, tailoring, PDI e entrevista;
    - vaga → match, reconciliação, tailoring, PDI e entrevista;
    - match/foco → reconciliação, tailoring, PDI e entrevista;
    - tailoring → PDI;
  - centralizar a invalidação em um único serviço;
  - registrar versão, timestamp e hash das entradas em cada artefato derivado;
  - impedir leitura/exibição de artefato cujo hash de origem não corresponda;
  - cobrir cada transição com testes de rota e de pipeline frontend.

#### P0-03 — Limitar abuso de recursos e definir ciclo de vida dos dados

- [ ] Estado: não iniciado.
- Evidência:
  - não há rate limiting para REST, upload, LLM, Firecrawl ou WebSocket;
  - mensagens WebSocket não têm schema nem limite explícito de tamanho;
  - payload JSON que não seja objeto, ou `content` que não seja string, pode
    gerar exceção fora dos casos controlados;
  - listas de campos aprovados e outros inputs ainda não têm limites globais;
    candidaturas já receberam limites na M0-01;
  - qualquer cliente pode criar IDs de sessão e diretórios indefinidamente;
  - `_session_locks` cresce por ID e não remove locks inativos;
  - não há TTL, quota por sessão, coleta de sessões antigas ou exclusão completa
    dos dados pelo usuário.
- Critérios de aceite:
  - schema estrito e tamanho máximo para mensagens WebSocket;
  - limites de texto/listas em todos os modelos Pydantic;
  - rate limit e quota por identidade/sessão;
  - timeout e cancelamento propagados para operações externas;
  - política de retenção, limpeza de locks e diretórios expirados;
  - ação explícita para exportar e apagar todos os dados da pessoa;
  - testes de payload excessivo, flood, sessão expirada e descarte.

#### P0-04 — Fechar a validação de links no tracker de candidaturas

- [x] Estado: concluído em 2026-06-27 pela tarefa M0-01.
- Implementação:
  - backend usa enum fechado para os sete status aceitos;
  - criação aceita apenas link `http`, `https` ou vazio;
  - `javascript:`, `data:`, URL sem esquema e status desconhecido retornam 422
    antes de qualquer persistência;
  - título, empresa, localização, link, salário, habilidades, contagem, notas e
    data de aplicação possuem limites explícitos;
  - update inválido não altera o arquivo existente;
  - registros legados não são apagados ou reescritos automaticamente;
  - frontend normaliza registros legados, sinaliza status/data inválidos e usa
    `normalizeHttpLink`, sem renderizar `<a>` para link inseguro.
- Evidência:
  - `backend/tests/test_applications.py`: 32 testes direcionados;
  - `frontend/src/components/ApplicationTracker.test.tsx`: 8 testes novos;
  - suíte completa: backend 250; frontend 56; lint e build aprovados.

#### P0-05 — Tornar a proteção de dados do CI baseada em allowlist

- [x] Estado: concluído em 2026-06-27 pela tarefa M0-02.
- Implementação:
  - `scripts/validate_data_guard.py` verifica índice Git e conteúdo atual de
    arquivos rastreados;
  - allowlist de `data/` restrita a `data/README.md` e
    `data/*.example.md` sanitizado;
  - qualquer caminho sob `data/sessions/` é bloqueado, inclusive com `git add -f`;
  - `.env`, variações perigosas, chaves privadas, API/access keys, tokens, JWT e
    credenciais atribuídas em texto claro são bloqueados;
  - placeholders, referências a variáveis e `.env.example` sanitizado são
    permitidos para reduzir falsos positivos;
  - cada erro informa o arquivo e, para segredo, a linha responsável;
  - o workflow executa os testes do guard e o mesmo comando disponível localmente.
- Evidência:
  - 8 testes `unittest` com repositórios Git temporários;
  - execução local aprovada sobre 153 arquivos rastreados/staged;
  - 14 arquivos novos/modificados da rodada verificados separadamente;
  - `data/README.md` segue como único arquivo atualmente rastreado em `data/`;
  - arquivos locais existentes em `data/` foram preservados.

#### P0-06 — Criar E2E automatizado do caminho crítico e de recuperação

- [ ] Estado: não iniciado.
- Escopo mínimo:
  - currículo → confirmação de perfil → vaga → match → foco/reconciliação →
    tailoring → PDI → entrevista → candidatura;
  - reload durante quiz e entrevista;
  - queda física do backend durante streaming e reconexão;
  - falha 400/409/422/500, timeout e resposta vazia;
  - invalidação visual após alterar perfil, currículo, vaga e match;
  - isolamento entre dois contextos de navegador.
- Critérios de aceite:
  - suíte Playwright ou equivalente executada contra processos reais;
  - dados isolados em diretório temporário;
  - artefatos, estado visual e ausência de vazamento entre sessões verificados;
  - execução bloqueante no CI.

#### P0-07 — Validar Firecrawl com chave e créditos reais

- [ ] Estado: bloqueado por credenciais/créditos externos.
- Já concluído no código:
  - origem formalizada para vagas: `real`, `llm` ou `simulated`;
  - origem formalizada para cursos: `real` ou `interna`;
  - estados de sucesso, vazio, degradado, sem créditos, erro e timeout;
  - normalização de salário, benefícios e requisitos;
  - links do Scout/Curator protegidos por validação `http(s)`;
  - roteiro manual versionado e testes determinísticos.
- Falta executar:
  - Scout real com resultados e busca vazia;
  - Curator real e complemento interno;
  - salários, benefícios e requisitos em amostra real;
  - links reais no navegador;
  - cenários sem crédito, erro, timeout e busca degradada;
  - preencher o registro de execução em
    `docs/firecrawl-validacao-manual.md`.

### P1 — Alta prioridade funcional e de confiabilidade

#### P1-01 — Completar a criação de candidaturas na interface

- [ ] Estado: backend pronto, frontend ausente.
- Evidência: existe `POST /api/applications/`, mas não há chamada POST para essa
  rota no frontend e o `ScoutReport` não oferece ação de salvar.
- Critérios de aceite:
  - botão “Salvar candidatura” apenas para vaga real;
  - feedback de salvamento, duplicidade e erro;
  - atualização imediata do tracker;
  - teste integrado Scout → salvar → tracker.

#### P1-02 — Endurecer schemas e leitura de todos os artefatos

- [ ] Estado: parcial.
- Já coberto:
  - match, tailoring, PDI e reconciliação tratam ausente/vazio e parte dos casos
    corrompidos por `read_required`/`read_optional_text`;
  - validações estruturais específicas existem para os principais relatórios.
- Lacunas:
  - `profile`, `data_files`, `job-description/latest` e `resume/latest` não usam
    o mesmo contrato de corrupção;
  - alguns artefatos inválidos retornam 404, outros 400/409;
  - o Markdown não tem versão de schema nem migração;
  - leituras raw de `data_files` não validam estrutura.
- Critérios de aceite:
  - schema versionado por tipo de artefato;
  - parser único com erro consistente: ausente, vazio, incompatível e corrompido;
  - nenhum artefato inválido tratado como “não encontrado”;
  - matriz de testes cobrindo todas as rotas de leitura e geração.

#### P1-03 — Corrigir e ampliar o CI

- [ ] Estado: parcial.
- Evidência:
  - frontend CI usa `npm install`, roda lint/build, mas não roda Vitest;
  - backend CI cobre apenas `main`; outros workflows cobrem `main` e `develop`;
  - `pytest-cov` está declarado, mas nenhuma meta de cobertura é aplicada;
  - não há E2E no CI.
- Critérios de aceite:
  - usar `npm ci`;
  - executar os 56+ testes frontend;
  - unificar branches e eventos;
  - medir cobertura backend/frontend com limiar inicial realista e crescente;
  - publicar relatórios de falha e duração.

#### P1-04 — Cobrir fluxos frontend hoje sem teste dedicado

- [ ] Testar `useWebSocket`: streaming, erro, queda, reconexão, replay e cleanup.
- [ ] Testar `apiRequest`: timeout, rede, 400, 409, 413, 422, 500, HTML e vazio.
- [ ] Testar `ApplicationTracker`: links, status, notas, exclusão e estado inválido.
- [ ] Testar pré-preenchimento do quiz a partir da análise do currículo.
- [ ] Testar auto-scroll em sucesso e erro.
- [ ] Testar loading, vazio, erro e sucesso dos componentes restantes.

#### P1-05 — Explicar conflitos e precedência de fontes

- [ ] Estado: comportamento existe, comunicação insuficiente.
- Critérios de aceite:
  - explicar quando prevalece perfil, currículo ou vaga;
  - mostrar efeito da escolha sobre match, tailoring, PDI e entrevista;
  - pedir confirmação antes de trocar foco;
  - rejeitar foco inválido de forma consistente, em vez de fallback silencioso
    em algumas rotas;
  - recalcular ou invalidar derivados após a confirmação.

#### P1-06 — Refinar o PDI e cursos pagos

- [ ] Permitir opção paga somente quando houver ganho explícito sobre alternativas
  gratuitas.
- [ ] Identificar claramente preço/origem e manter alternativa gratuita.
- [ ] Não promover curso interno como resultado real do Firecrawl.
- [ ] Cobrir a regra com testes do Curator e do PDI.

#### P1-07 — Definir suporte de concorrência do deploy

- [ ] Estado: seguro apenas no processo atual.
- Evidência: locks são mantidos em memória e não coordenam múltiplos processos ou
  réplicas.
- Critérios de aceite:
  - declarar e impor execução com um worker, ou
  - migrar coordenação/persistência para mecanismo multiprocesso;
  - testar concorrência entre processos antes de escalar horizontalmente.

### P2 — Qualidade técnica e manutenção

- [ ] Instalar e validar o ambiente de desenvolvimento a partir de
  `requirements-dev.txt`; evitar ambiente local divergente.
- [ ] Remover pacotes `extraneous` de `frontend/node_modules` com instalação
  limpa e reproduzível.
- [ ] Concluir lazy loading; o bundle principal cresceu de 376,81 kB para
  379,68 kB e o chat de 174,29 kB para 174,47 kB.
- [ ] Definir orçamento de bundle no CI e revisar imports/tree-shaking.
- [ ] Mover leituras e `unlink` síncronos restantes para helpers assíncronos ou
  thread, especialmente em rotas `async`.
- [ ] Eliminar checagens defensivas de mojibake após garantir UTF-8 na entrada e
  persistência.
- [ ] Acompanhar o warning `python_multipart` da cadeia Starlette/FastAPI.
- [ ] Eliminar duplicações de tipos TypeScript e validar respostas REST em
  runtime antes de fazer cast.
- [ ] Revisar responsabilidades de componentes e o CSS monolítico.
- [ ] Remover locks inativos e definir limite/rotação para backups de corrupção.
- [ ] Adicionar readiness check separado de liveness, incluindo diretório de
  dados gravável e estado dos provedores sem expor segredos.
- [ ] Tornar CORS, hosts confiáveis e headers de segurança configuráveis por
  ambiente; documentar terminação TLS no proxy de produção.
- [ ] Avaliar varredura de dependências no CI; segredos já são cobertos pelo
  Data Guard da M0-02.

### P3 — Documentação e acabamento

- [ ] Reescrever `plano.md`: ele descreve apenas a persona/MoE original e não a
  arquitetura FastAPI + React + WebSocket + sessões atual.
- [x] README atualizado para 250 testes backend e 56 testes frontend após M0-01.
- [ ] Enumerar no README as rotas REST e o contrato do WebSocket.
- [ ] Corrigir a afirmação de criação de candidaturas na UI enquanto P1-01 não
  estiver concluído.
- [ ] Consolidar ou marcar `docs/avaliacao-20-06.md` e as seções históricas de
  `docs/project-update-report.md` como snapshots, pois contêm achados já
  resolvidos e contagens antigas.
- [ ] Criar ADRs para isolamento por sessão, escrita atômica, fallback de
  provedores, foco da candidatura e linhagem de artefatos.
- [ ] Criar diagrama do fluxo frontend → rotas → agentes → artefatos.
- [ ] Documentar schemas, versões e dependências de todos os arquivos em `data/`.
- [ ] Adicionar capturas de tela apenas após estabilização visual.

## 5. Entregas confirmadas no código

### Backend e resiliência

- [x] FastAPI com rotas REST, WebSocket e agentes especializados.
- [x] Logging JSON e tratamento global seguro de 422/500.
- [x] Erros de LLM e Firecrawl convertidos em falhas de domínio.
- [x] Escrita atômica, locks por sessão e stress test de 50 escritas.
- [x] Isolamento de caminhos em `data/sessions/{session_id}/`.
- [x] Tentativas de path traversal não escapam do diretório base.
- [x] `applications.json` corrompido gera 409, backup e preservação do original.
- [x] Upload limitado a 5 MB, com extensão, Content-Type e Magic Number.
- [x] Confirmação explícita antes de aplicar sugestões do currículo ao perfil.
- [x] Candidaturas validam enum de status, links `http(s)` e limites de texto
  antes de persistir.

### Jornada e agentes

- [x] Quiz de sete perguntas com retomada e perfil consolidado.
- [x] Menu e roteamento A–I.
- [x] Scout com match, filtro de data, proveniência e fallback em camadas.
- [x] Curator com trilha, proveniência e base interna identificada.
- [x] Coach com cinco perguntas, feedback contextual e retomada.
- [x] Análise de vaga, match, reconciliação, tailoring e PDI.
- [x] Foco de candidatura persistido e consumido pelas etapas derivadas.

### Frontend

- [x] React 19, TypeScript 6 e Vite.
- [x] Helper central de API com timeout e mensagens amigáveis.
- [x] Recuperação visual no primeiro load via `replay=1`.
- [x] Reconexão transitória sem duplicar o prompt.
- [x] Confirmação seletiva das sugestões de perfil.
- [x] Links do Scout e Curator restritos a `http(s)`.
- [x] Tracker normaliza links e registros legados sem renderizar URL insegura.
- [x] Responsividade, navegação por teclado, redução de movimento e fallback de
  cópia documentados na rodada de QA.

### Infraestrutura e testes

- [x] Dockerfiles para backend/frontend, Nginx e Compose com mock opcional.
- [x] `.dockerignore` impede inclusão de `.env`, dados e logs na imagem backend.
- [x] GitHub Actions para backend, frontend, documentação e proteção de dados.
- [x] Data Guard baseado em allowlist, reutilizável localmente e no CI.
- [x] Backend: 250 testes passando nesta avaliação.
- [x] Frontend: 56 testes, lint e build passando nesta avaliação.

## 6. Ordem recomendada de execução

1. Segurança e integridade imediatas
   - P0-01 identidade/autorização;
   - P0-02 linhagem/invalidação;
   - P0-03 limites/retenção;

2. Gate de release
   - P0-06 E2E;
   - P0-07 Firecrawl real;
   - P1-03 CI com testes frontend e cobertura.

3. Fechamento funcional
   - P1-01 salvar candidatura;
   - P1-02 schemas;
   - P1-04 cobertura frontend;
   - P1-05 precedência;
   - P1-06 PDI;
   - P1-07 concorrência de deploy.

4. Sustentação
   - itens P2;
   - sincronização documental P3.

## 7. Definição de pronto para publicação

- [ ] Todos os P0 concluídos ou formalmente removidos do escopo público.
- [ ] Nenhum dado de uma identidade acessível por outra.
- [ ] Nenhum artefato obsoleto exibido como atual.
- [ ] Limites, rate limiting, retenção e exclusão de dados operacionais.
- [ ] E2E crítico e CI completos passando.
- [ ] Firecrawl real validado e evidenciado.
- [ ] Backup, restauração e observabilidade testados.
- [ ] Política de privacidade e operação com dados pessoais revisadas antes de
  receber currículos reais em ambiente público.
