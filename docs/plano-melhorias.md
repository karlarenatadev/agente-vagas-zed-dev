# Plano de melhorias — Recoloca IA

Criado em: 2026-06-27

Referência inicial: `main` em `75c7fa1`

Fonte de requisitos: `docs/checklist.md`

## 1. Objetivo

Evoluir o projeto de MVP local funcional para uma aplicação que possa receber
currículos e outros dados pessoais em ambiente público com controles adequados
de segurança, integridade, disponibilidade e rastreabilidade.

O plano não substitui o checklist:

1. `docs/checklist.md` registra estado, evidências e pendências.
2. `docs/plano-melhorias.md` define sequência, dependências e execução.
3. Cada entrega concluída deve atualizar os dois documentos no mesmo pull
   request.

## 2. Resultado esperado

Ao final do plano, o sistema deve:

1. vincular todos os dados a uma identidade autenticada e autorizada;
2. impedir que relatórios antigos sejam apresentados como atuais;
3. limitar abuso de API, WebSocket, armazenamento e provedores externos;
4. tratar entradas e artefatos com schemas consistentes e versionados;
5. cobrir a jornada crítica com testes E2E executados no CI;
6. validar Scout e Curator contra o Firecrawl real;
7. completar o fluxo de candidaturas na interface;
8. possuir documentação coerente com a arquitetura executada.

## 3. Premissas e limites

1. O objetivo de referência é **publicação pública com dados reais**.
2. O modo local sem autenticação pode continuar existindo, mas deve ser ativado
   explicitamente e nunca ser o padrão de produção.
3. A persistência em arquivos pode ser mantida durante as primeiras fases.
4. A adoção de banco de dados deve ocorrer somente se autenticação, concorrência,
   busca, auditoria ou retenção mostrarem que arquivos deixaram de atender aos
   requisitos.
5. Mudanças de segurança e integridade devem ser entregues antes de novas
   funcionalidades não essenciais.
6. Nenhuma fase deve depender de credenciais reais em testes unitários.
7. Testes com Firecrawl real ficam separados dos testes determinísticos e devem
   ter execução controlada por custo.

## 4. Regras de execução

Cada tarefa deve seguir este fluxo:

1. Confirmar o comportamento atual com teste de caracterização.
2. Implementar a menor mudança que feche o critério de aceite.
3. Adicionar testes positivos, negativos e de regressão.
4. Executar backend, frontend, lint e build conforme o escopo.
5. Atualizar `docs/checklist.md`.
6. Registrar decisão arquitetural quando houver mudança de contrato.
7. Evitar misturar refatoração ampla com correção de segurança no mesmo pull
   request.

Validação mínima para qualquer entrega:

```text
Backend: python -m pytest backend/tests -q
Frontend: npm run test -- --run
Lint: npm run lint
Build: npm run build
```

## 5. Sequência de implementação

### Fase 0 — Contenção imediata

Objetivo: fechar riscos pequenos com impacto alto antes das mudanças
arquiteturais.

Dependências: nenhuma.

#### M0-01 — Validar links e status de candidaturas

Prioridade: P0

Status: concluída em 2026-06-27.

Arquivos principais:

- `backend/routers/applications.py`
- `backend/tests/test_applications.py`
- `frontend/src/components/ApplicationTracker.tsx`
- `frontend/src/lib/links.ts`
- novo teste dedicado do tracker

Execução:

1. Criar enum backend para os status aceitos.
2. Aplicar limites de tamanho a título, empresa, localização, salário, notas e
   campos de habilidades.
3. Validar `link` como URL `http(s)` ou valor vazio.
4. Tratar registros legados inválidos sem quebrar o painel.
5. Aplicar `normalizeHttpLink` antes de renderizar o link no tracker.
6. Não renderizar `<a>` quando o link for inválido.
7. Cobrir `javascript:`, `data:`, URL sem esquema, status desconhecido e texto
   excessivo.

Critérios de aceite:

- [x] Nenhuma nova mutação persiste esquema diferente de `http`/`https`, e
  nenhum link legado inseguro é renderizado; registros legados são preservados
  sem reescrita automática.
- [x] Status inválido retorna 422 controlado sem alterar persistência.
- [x] Registro legado inválido não derruba o componente.
- [x] Testes backend e frontend passam.

Validação:

- backend direcionado: 32 testes passando;
- frontend direcionado: 13 testes passando, incluindo o helper de links;
- backend completo: 250 testes passando;
- frontend completo: 56 testes passando;
- lint e build: aprovados.

#### M0-02 — Endurecer o guard de dados

Prioridade: P0

Status: concluída em 2026-06-27.

Arquivos principais:

- `.github/workflows/data-guard.yml`
- `.gitignore`
- `.dockerignore`
- documentação de contribuição, se criada

Execução:

1. Trocar a denylist por allowlist.
2. Permitir em `data/` somente:
   - `data/README.md`;
   - arquivos `*.example.md` comprovadamente sanitizados.
3. Bloquear qualquer conteúdo sob `data/sessions/`.
4. Bloquear `.env` e padrões conhecidos de chaves.
5. Criar um script simples de validação executável localmente e pelo CI.
6. Testar o guard com arquivos permitidos e proibidos.

Critérios de aceite:

- [x] `git add -f data/sessions/exemplo/user-profile.md` é detectado pelo guard
  usado no CI.
- [x] README, exemplos Markdown e `.env.example` sanitizados continuam permitidos.
- [x] Chave, token, private key ou credencial inserida em arquivo rastreado faz
  o guard falhar.
- [x] O erro informa o arquivo responsável e a linha quando aplicável.
- [x] O mesmo script executa localmente e no workflow.

Validação:

- `python -m unittest discover -s scripts/tests -p "test_*.py" -v`: 8 testes
  passando;
- `python scripts/validate_data_guard.py`: 153 arquivos rastreados/staged
  verificados, sem violações;
- 14 arquivos novos/modificados da rodada verificados separadamente pelo mesmo
  scanner, sem violações;
- artefatos locais existentes em `data/` permaneceram ignorados e não foram
  lidos, alterados ou removidos.

#### M0-03 — Validar o protocolo de entrada do WebSocket

Prioridade: P0

Estado: concluída em 2026-07-04.

Arquivos principais:

- `backend/routers/chat.py`
- `backend/config.py`
- `backend/tests/test_chat_websocket_failures.py`
- `frontend/src/hooks/useWebSocket.ts`
- `frontend/src/types.ts`

Execução:

1. Definir schema para mensagens recebidas.
2. Exigir objeto JSON com `type="message"` e `content` string.
3. Definir tamanho máximo configurável para mensagem.
4. Restringir `date_filter` aos valores suportados.
5. Responder erro controlado sem encerrar a conexão para payload recuperável.
6. Encerrar com código apropriado quando o limite de protocolo for violado.
7. Garantir que payloads inválidos não alterem nem persistam estado.

Critérios de aceite:

- [x] Lista, número, `null`, objeto sem `content` e `content` não textual são
  rejeitados.
- [x] Mensagem excessiva não chega ao Maestro ou aos provedores.
- [x] Estado anterior permanece intacto após erro.
- [x] Testes cobrem conexão viva e encerramento controlado.

Validação:

- WebSocket backend: 20 testes focalizados passando.
- Suíte backend: 264 testes passando.
- Frontend: 58 testes, lint e build passando.

#### M0-04 — Incluir os testes frontend no CI

Prioridade: P1, antecipada por baixo custo e efeito de proteção.

Estado: concluída em 2026-07-04.

Arquivos principais:

- `.github/workflows/ci.yml`
- `frontend/package.json`
- `frontend/package-lock.json`

Execução:

1. Substituir `npm install` por `npm ci`.
2. Executar `npm run test -- --run` antes de lint e build.
3. Padronizar branches monitoradas pelos workflows.
4. Habilitar cache usando o lockfile.
5. Garantir cancelamento de execução antiga quando houver novo push na mesma
   branch.

Critérios de aceite:

- [x] Um teste frontend quebrado bloqueia o pull request.
- [x] O CI instala exatamente o conteúdo do lockfile.
- [x] Testes, lint e build são jobs obrigatórios ou etapas bloqueantes.

Validação:

- Frontend: `npm ci`, 58 testes, lint e build passando.
- Backend: 264 testes passando.
- Data Guard: 8 testes e 159 arquivos verificados.
- Workflows padronizados para `main`, com cache npm e `concurrency`.

#### Gate da Fase 0

- [x] M0-01 concluída.
- [x] M0-02 concluída.
- [x] M0-03 concluída.
- [x] M0-04 concluída.
- [x] Suítes backend e frontend aprovadas.
- [x] Nenhuma alteração de contrato sem teste.

### Fase 1 — Integridade e linhagem dos artefatos

Objetivo: garantir que nenhum resultado derivado seja exibido após suas entradas
mudarem.

Dependências: Fase 0 concluída.

#### M1-01 — Formalizar o grafo de dependências

Prioridade: P0

Status: concluída em 2026-07-04.

Entregáveis:

- [x] ADR em `docs/adr/`;
- [x] mapa de dependências versionado no backend;
- [x] casos de teste para cada transição.

Grafo inicial:

1. Perfil altera:
   - resultados de vagas;
   - recomendações de cursos;
   - match;
   - reconciliação;
   - tailoring;
   - PDI;
   - entrevista.
2. Currículo altera:
   - match;
   - reconciliação;
   - tailoring;
   - PDI;
   - entrevista.
3. Vaga altera:
   - match;
   - reconciliação;
   - tailoring;
   - PDI;
   - entrevista.
4. Match ou foco altera:
   - reconciliação;
   - tailoring;
   - PDI;
   - entrevista.
5. Tailoring altera:
   - PDI.

Critérios de aceite:

- [x] Cada artefato do grafo inicial possui dependentes definidos.
- [x] O contrato do grafo possui uma única definição central.
- [x] A política diferencia invalidar, recalcular e preservar.

Entregas subsequentes:

1. [x] M1-02 criou o registro central e o estado de atualidade sem apagar os
   artefatos Markdown existentes.
2. [x] M1-03A migrou currículo e análise de vaga para o serviço central, com
   testes por rota.

#### M1-02 — Criar um registro central de artefatos

Prioridade: P0

Status: concluída em 2026-07-04.

Implementação recomendada:

- [x] criar `backend/artifacts.py`;
- [x] manter um `artifact-manifest.json` em cada diretório de sessão;
- [x] preservar os arquivos Markdown atuais como conteúdo legível.

Metadados mínimos por artefato:

1. nome e versão do schema;
2. data de geração em UTC;
3. hash do conteúdo;
4. hashes dos artefatos de entrada;
5. versão do gerador;
6. estado: atual, obsoleto ou corrompido.

Execução:

1. [x] Implementar cálculo de hash determinístico.
2. [x] Implementar escrita atômica do manifesto.
3. [x] Implementar leitura com verificação de conteúdo e entradas.
4. [x] Implementar invalidação central por grafo.
5. [x] Tratar sessões antigas sem manifest como legado não verificado.
6. [x] Não apagar artefato corrompido antes de preservar evidência.

Critérios de aceite:

- [x] Alterar uma entrada permite marcar seus derivados como obsoletos.
- [x] Um arquivo modificado fora da aplicação é detectado pelo hash.
- [x] Falha na escrita do manifesto preserva a versão anterior sem arquivo parcial.
- [x] Sessão antiga recebe tratamento explícito e seguro.

Pendências para M1-03:

1. Replicar escrita, registro e invalidação sob o mesmo lock nos demais produtores.
2. Migrar match, foco, reconciliação, tailoring, PDI, Scout, Curator e Coach.
3. Validar atualidade antes do consumo nos routers e agentes.

#### M1-03 — Migrar produtores e consumidores

Prioridade: P0

Status: M1-03A e M1-03B concluídas em 2026-07-04; M1-03C pendente.

M1-03A:

- [x] registrar currículo como `current`;
- [x] registrar análise de vaga REST e Maestro como `current`;
- [x] marcar dependentes registrados como `stale` pelo grafo central;
- [x] preservar arquivos derivados e sessões legadas/parciais;
- [x] remover listas locais de invalidação dos produtores migrados;
- [x] adicionar 8 testes de integração e falha.

M1-03B:

- [x] registrar match no REST e no Maestro e invalidar seus dependentes;
- [x] registrar foco e invalidar reconciliação, tailoring, PDI e entrevista;
- [x] registrar reconciliação, tailoring e PDI após geração bem-sucedida;
- [x] bloquear match `stale` ou `corrupted` em reconciliação e tailoring;
- [x] bloquear match ou tailoring inválido antes de gerar PDI;
- [x] bloquear match inválido no Coach, preservando sessões `legacy`;
- [x] adicionar 12 testes de registro, invalidação, compatibilidade e erro;
- [x] validar o backend completo com 303 testes.

Ordem:

1. análise de currículo;
2. análise de vaga;
3. match;
4. reconciliação/foco;
5. tailoring;
6. PDI;
7. Scout/Curator;
8. Coach;
9. perfil.

Execução:

1. Substituir listas locais de `unlink` pelo serviço central.
2. Registrar metadados ao gerar cada artefato.
3. Validar atualidade antes de consumir.
4. Retornar erro de domínio específico para artefato obsoleto.
5. Manter mensagens acionáveis indicando qual etapa deve ser refeita.

Critérios de aceite:

- [ ] Nenhum router mantém sua própria lista de invalidação.
- [x] Match antigo não alimenta tailoring ou PDI.
- [ ] Reconciliação antiga não permanece concluída após mudar vaga/currículo.
- [ ] Entrevista não reutiliza contexto obsoleto silenciosamente.

Pendências para M1-03C:

1. Registrar a entrevista e validar suas demais entradas além do match.
2. Migrar perfil, Scout e Curator sem ampliar listas locais.
3. Proteger endpoints `latest` e expor estado para o frontend.
4. Cobrir falha entre a escrita do conteúdo e a atualização do manifesto.

#### M1-04 — Refletir atualidade no frontend

Prioridade: P0

Arquivos principais:

- `frontend/src/components/ApplicationPipeline.tsx`
- componentes de relatórios
- `frontend/src/types.ts`
- cliente de API

Execução:

1. Parar de inferir conclusão apenas pela existência do arquivo.
2. Consumir estado de atualidade retornado pelo backend.
3. Diferenciar etapa ausente, atual, obsoleta e corrompida.
4. Oferecer ação para recalcular a etapa correta.
5. Atualizar a pipeline imediatamente após invalidação.

Critérios de aceite:

- [ ] Artefato obsoleto nunca aparece como etapa concluída.
- [ ] A interface informa a entrada que mudou.
- [ ] A ação recomendada leva à etapa correta.
- [ ] Testes de componente cobrem todas as transições do grafo.

#### Gate da Fase 1

- [ ] Nenhum relatório derivado é consumido sem verificação de atualidade.
- [ ] Testes provam invalidação backend e atualização frontend.
- [ ] ADR e schemas estão documentados.

### Fase 2 — Identidade, autorização e privacidade

Objetivo: impedir acesso cruzado e tornar explícito o ciclo de vida dos dados
pessoais.

Dependências: registro central de artefatos concluído.

#### M2-01 — Definir modos de execução e modelo de identidade

Prioridade: P0

Decisão recomendada:

1. `APP_MODE=local`
   - acesso anônimo permitido;
   - sessão default permitida apenas em loopback;
   - aviso explícito de que não é modo público.
2. `APP_MODE=public`
   - autenticação obrigatória;
   - sessão default proibida;
   - identidade derivada de credencial validada no servidor.

Antes da implementação:

1. escolher provedor de identidade;
2. decidir cookie seguro de sessão ou ticket curto para WebSocket;
3. definir logout, revogação e expiração;
4. registrar a decisão em ADR.

Critérios de aceite:

- [ ] Inicialização em modo público falha se autenticação estiver incompleta.
- [ ] O cliente não escolhe o identificador de propriedade dos dados.
- [ ] Nenhum token duradouro é enviado na query do WebSocket.

#### M2-02 — Criar contexto de usuário autorizado

Prioridade: P0

Arquivos previstos:

- novo módulo de segurança no backend;
- `backend/main.py`;
- `backend/session.py`;
- todos os routers;
- `backend/routers/chat.py`.

Execução:

1. Criar dependência `UserContext`.
2. Validar credencial antes de resolver caminhos.
3. Derivar diretório interno de identificador opaco e não reversível.
4. Remover confiança em `X-Session-Id` no modo público.
5. Aplicar a mesma identidade no REST e WebSocket.
6. Validar `Origin` do WebSocket.
7. Registrar auditoria sem currículo, prompt ou segredo nos logs.

Critérios de aceite:

- [ ] Usuário A recebe 401/403 ao tentar acessar dados de B.
- [ ] Alterar headers ou query string não troca a identidade efetiva.
- [ ] REST e WebSocket resolvem o mesmo proprietário.
- [ ] Logs permitem rastrear operação sem registrar conteúdo pessoal.

#### M2-03 — Implementar direitos sobre os dados

Prioridade: P0

Execução:

1. Definir prazo de retenção por ambiente.
2. Criar endpoint e interface para exportar os dados da pessoa.
3. Criar exclusão completa com confirmação forte.
4. Remover artefatos, candidaturas, estado de chat, manifestos e backups.
5. Registrar apenas evidência mínima da exclusão.
6. Implementar coleta automática de sessões expiradas.

Critérios de aceite:

- [ ] Exportação contém todos os artefatos pertencentes à identidade.
- [ ] Exclusão remove também temporários e backups.
- [ ] A identidade excluída não recupera dados em novo login.
- [ ] Testes usam duas identidades e verificam ausência de efeito cruzado.

#### Gate da Fase 2

- [ ] Autenticação e autorização aplicadas a todas as superfícies.
- [ ] Modo local e modo público separados.
- [ ] Exportação, exclusão e retenção testadas.

### Fase 3 — Limites, disponibilidade e operação

Objetivo: controlar custo, disco, memória e concorrência.

Dependências: identidade disponível para atribuição de quota.

#### M3-01 — Aplicar limites de entrada

Prioridade: P0

Execução:

1. Inventariar todos os modelos Pydantic e mensagens WebSocket.
2. Definir tamanho máximo por campo e por lista.
3. Limitar quantidade de candidaturas por identidade.
4. Limitar tamanho total de artefatos por sessão.
5. Proteger extração de PDF/DOCX contra consumo excessivo de CPU/memória.
6. Padronizar respostas 413 e 422.

Critérios de aceite:

- [ ] Todos os inputs externos possuem limite explícito.
- [ ] Rejeição ocorre antes de chamar LLM ou Firecrawl.
- [ ] Limites são configuráveis e documentados.

#### M3-02 — Adicionar rate limiting e quotas

Prioridade: P0

Escopos separados:

1. leitura REST;
2. mutação REST;
3. upload;
4. conexão e mensagem WebSocket;
5. chamada LLM;
6. chamada Firecrawl.

Critérios de aceite:

- [ ] Limite excedido retorna resposta previsível com orientação de retry.
- [ ] Uma identidade não consome quota de outra.
- [ ] Scout e Curator não repetem chamadas externas durante retry do cliente.
- [ ] Métricas registram bloqueios sem expor conteúdo.

#### M3-03 — Controlar sessões, locks e armazenamento

Prioridade: P0

Execução:

1. Remover locks inativos de `_session_locks`.
2. Criar rotina de limpeza de diretórios expirados.
3. Definir quota de disco por identidade.
4. Rotacionar backups de corrupção.
5. Alertar antes de atingir limite global de armazenamento.
6. Testar interrupção durante limpeza e escrita.

Critérios de aceite:

- [ ] Criar IDs repetidamente não causa crescimento permanente de memória.
- [ ] Limpeza não remove sessão ativa.
- [ ] Falha de disco cheio retorna erro controlado e preserva o arquivo anterior.

#### M3-04 — Definir concorrência suportada

Prioridade: P1

Execução:

1. Manter um único worker como contrato inicial, ou adotar lock/persistência
   multiprocesso.
2. Tornar a escolha explícita no Docker e na documentação.
3. Se houver múltiplas réplicas, remover dependência de estado somente em
   memória.
4. Testar read-modify-write entre processos.

Critérios de aceite:

- [ ] Configuração de produção não permite topologia não suportada.
- [ ] Concorrência documentada corresponde ao comportamento testado.

#### M3-05 — Melhorar health checks e observabilidade

Prioridade: P2

Execução:

1. Manter `/health` como liveness.
2. Criar readiness para diretório gravável e dependências essenciais.
3. Não considerar provedor opcional indisponível como falha total.
4. Adicionar métricas de latência, erro, fallback, quota e armazenamento.
5. Configurar headers de segurança, hosts confiáveis e CORS por ambiente.
6. Documentar TLS no proxy de produção.

#### Gate da Fase 3

- [ ] Entradas, custos e armazenamento possuem limites.
- [ ] Topologia de concorrência está declarada e testada.
- [ ] Readiness diferencia falha total de modo degradado.

### Fase 4 — Qualidade de contratos e testes

Objetivo: transformar os controles anteriores em gates automáticos de release.

Dependências: Fases 1 a 3 estáveis.

#### M4-01 — Versionar schemas de artefatos

Prioridade: P1

Execução:

1. Definir schema e versão para cada Markdown/JSON.
2. Centralizar leitura, validação e conversão.
3. Diferenciar:
   - ausente;
   - vazio;
   - obsoleto;
   - versão incompatível;
   - corrompido;
   - erro de I/O.
4. Padronizar status HTTP e mensagens.
5. Definir migração ou descarte seguro de versões antigas.

Critérios de aceite:

- [ ] `profile`, `data_files`, vaga, currículo, match, reconciliação, tailoring e
  PDI usam o mesmo contrato.
- [ ] Artefato inválido não retorna 404 como se estivesse ausente.
- [ ] Matriz de testes cobre todos os estados.

#### M4-02 — Ampliar testes frontend

Prioridade: P1

Ordem:

1. `apiRequest`;
2. `useWebSocket`;
3. `ApplicationTracker`;
4. pré-preenchimento do quiz;
5. `ApplicationPipeline`;
6. auto-scroll;
7. estados loading, vazio, erro e sucesso.

Critérios de aceite:

- [ ] Falhas 400, 409, 413, 422, 500, timeout e rede estão cobertas.
- [ ] Replay/reconexão não duplicam mensagens.
- [ ] Invalidação repinta a pipeline corretamente.

#### M4-03 — Criar E2E do caminho crítico

Prioridade: P0

Infraestrutura recomendada:

- Playwright;
- backend e frontend reais iniciados pelo runner;
- `DATA_DIR` temporário por execução;
- provedores externos substituídos por fakes determinísticos;
- contextos de navegador separados para teste de isolamento.

Cenários obrigatórios:

1. currículo → confirmação de perfil;
2. vaga → match → foco → tailoring → PDI;
3. entrevista completa;
4. salvar e acompanhar candidatura;
5. reload durante quiz e entrevista;
6. queda do backend durante streaming e reconexão;
7. alteração de entrada invalidando derivados;
8. duas identidades sem vazamento;
9. exclusão completa dos dados.

Critérios de aceite:

- [ ] E2E executa no CI sem depender de API externa.
- [ ] Falha do E2E bloqueia publicação.
- [ ] Evidências de erro são anexadas pelo runner.

#### M4-04 — Medir cobertura sem mascarar risco

Prioridade: P1

Execução:

1. Garantir instalação reproduzível de `requirements-dev.txt`.
2. Habilitar cobertura backend e frontend.
3. Registrar baseline real.
4. Definir limiar inicial sem reduzir a cobertura atual.
5. Elevar o limiar por módulo crítico, não apenas pela média global.

Módulos críticos:

- sessão e autorização;
- artefatos;
- WebSocket;
- upload;
- candidaturas;
- integrações externas.

#### Gate da Fase 4

- [ ] Contratos versionados.
- [ ] E2E bloqueante.
- [ ] Cobertura mensurada e protegida no CI.

### Fase 5 — Fechamento funcional

Objetivo: concluir lacunas de produto após os gates de segurança e integridade.

Dependências: Fases 0 a 4.

#### M5-01 — Salvar candidatura a partir do Scout

Prioridade: P1

Execução:

1. Exibir ação apenas para vaga `source="real"`.
2. Persistir pelo `POST /api/applications/`.
3. Definir chave de deduplicação por URL normalizada e identidade.
4. Mostrar estados salvando, salva, duplicada e erro.
5. Atualizar o tracker sem reload.

Critérios de aceite:

- [ ] Vaga real pode ser salva em um clique.
- [ ] Vaga LLM/simulada não vira candidatura real.
- [ ] Duplicidade é tratada sem criar registros repetidos.

#### M5-02 — Melhorar conflito e precedência

Prioridade: P1

Execução:

1. Explicar as fontes perfil, currículo e vaga.
2. Mostrar por que uma fonte prevalece.
3. Mostrar quais relatórios serão invalidados.
4. Exigir confirmação para trocar foco.
5. Rejeitar foco inválido em todas as rotas.

Critérios de aceite:

- [ ] A escolha de foco não ocorre silenciosamente.
- [ ] O usuário entende o impacto antes de confirmar.
- [ ] Derivados são invalidados/recalculados após a alteração.

#### M5-03 — Refinar cursos e PDI

Prioridade: P1

Execução:

1. Priorizar recursos gratuitos adequados.
2. Incluir pago somente com justificativa objetiva.
3. Exibir preço, plataforma e origem.
4. Manter alternativa gratuita.
5. Não apresentar recomendação interna como busca real.

Critérios de aceite:

- [ ] Toda opção paga tem justificativa e alternativa gratuita.
- [ ] Origem do recurso permanece inequívoca.
- [ ] Testes cobrem ordenação e fallback.

#### Gate da Fase 5

- [ ] Jornada funcional completa pela interface.
- [ ] Nenhuma funcionalidade contorna os gates das fases anteriores.

### Fase 6 — Desempenho, manutenção e documentação

Objetivo: reduzir custo de evolução e alinhar documentação ao sistema real.

Dependências: funcionalidades e contratos estabilizados.

#### M6-01 — Reduzir bundle e custo do frontend

Prioridade: P2

Execução:

1. Registrar orçamento inicial:
   - bundle principal: 379,68 kB;
   - chunk do chat: 174,47 kB.
2. Concluir lazy loading dos painéis.
3. Revisar imports e tree-shaking.
4. Criar gate de tamanho no CI.
5. Remover dependências e pacotes extraneous após instalação limpa.

#### M6-02 — Reduzir dívida técnica do backend

Prioridade: P2

Execução:

1. Mover I/O síncrono remanescente para helpers apropriados.
2. Remover tratamentos de mojibake após garantir UTF-8 na borda.
3. Acompanhar a migração de `python_multipart`.
4. Revisar responsabilidades de routers e agentes.
5. Validar respostas externas antes de convertê-las em artefato.

#### M6-03 — Sincronizar documentação

Prioridade: P3

Arquivos:

- `plano.md`
- `README.md`
- `docs/project-update-report.md`
- `docs/avaliacao-20-06.md`
- `data/README.md`
- novos ADRs e schemas

Execução:

1. Reescrever `plano.md` com a arquitetura atual.
2. Atualizar contagens de testes.
3. Documentar rotas REST e protocolo WebSocket.
4. Marcar relatórios antigos como snapshots históricos.
5. Documentar schemas e grafo de artefatos.
6. Criar diagrama frontend → API → agentes → persistência.
7. Documentar operação local e pública separadamente.

#### Gate da Fase 6

- [ ] README e plano refletem o código.
- [ ] ADRs explicam decisões de segurança, sessão e artefatos.
- [ ] Não há contagens ou estados contraditórios entre documentos.

## 6. Ordem sugerida de pull requests

Para manter revisões pequenas e reversíveis:

1. PR-01: validação de link/status de candidaturas.
2. PR-02: allowlist de dados e teste do guard.
3. PR-03: schema e limites do WebSocket.
4. PR-04: frontend CI com testes e `npm ci`.
5. PR-05: ADR e grafo de artefatos.
6. PR-06: registro central e manifesto de artefatos.
7. PR-07: migração de produtores/consumidores.
8. PR-08: estado de atualidade na pipeline frontend.
9. PR-09: ADR de identidade e modos local/público.
10. PR-10: autenticação/autorização REST.
11. PR-11: autenticação/autorização WebSocket.
12. PR-12: exportação, exclusão e retenção.
13. PR-13: rate limiting, quotas e limpeza de sessão.
14. PR-14: schemas versionados e erros consistentes.
15. PR-15: testes frontend críticos.
16. PR-16: infraestrutura E2E.
17. PR-17: E2E da jornada completa.
18. PR-18: salvar candidatura pelo Scout.
19. PR-19: conflitos, foco, cursos e PDI.
20. PR-20: desempenho e documentação final.

PRs podem ser agrupados apenas quando não aumentarem o raio de risco ou
dificultarem rollback.

## 7. Dependências críticas

1. Autenticação depende de uma decisão explícita sobre provedor e sessão.
2. Quotas por usuário dependem da identidade estar disponível.
3. E2E de isolamento público depende da autorização concluída.
4. Pipeline confiável depende do registro de atualidade dos artefatos.
5. Salvar candidatura depende da validação de URL/status.
6. Firecrawl real depende de chave válida, créditos e ambiente controlado.
7. Escala com múltiplos workers depende de persistência/locks multiprocesso.

## 8. Riscos de execução

### Risco 1 — Autenticação ampliar excessivamente o escopo

Mitigação:

1. separar modo local e público;
2. usar provedor gerenciado em vez de implementar credenciais próprias;
3. entregar autorização REST e WebSocket em etapas independentes.

### Risco 2 — Manifesto divergir dos arquivos

Mitigação:

1. escrita sob o mesmo lock;
2. operação atômica;
3. hash verificado na leitura;
4. teste de falha entre escrita do conteúdo e do manifesto.

### Risco 3 — Invalidação agressiva apagar trabalho útil

Mitigação:

1. marcar como obsoleto antes de apagar;
2. preservar conteúdo para auditoria local;
3. oferecer recálculo;
4. apagar somente conforme política de retenção.

### Risco 4 — E2E ficar instável

Mitigação:

1. usar provedores fake determinísticos;
2. esperar por estado observável, não por tempo fixo;
3. isolar diretório e portas por execução;
4. manter teste real do Firecrawl fora do E2E bloqueante comum.

### Risco 5 — Compatibilidade com sessões antigas

Mitigação:

1. detectar versão ausente;
2. não assumir que legado é atual;
3. fornecer migração ou regeneração orientada;
4. preservar backup antes de converter.

## 9. Critérios de release

### Release local controlado

- [x] Testes backend e frontend aprovados na entrega M0-01.
- [x] Links/status de candidaturas validados.
- [x] Protocolo WebSocket limitado.
- [x] Dados de runtime permanecem fora do Git e das imagens, protegidos por
  ignore e Data Guard.
- [ ] Interface identifica fallback e dados simulados.

### Release público piloto

- [ ] Fases 0 a 4 concluídas.
- [ ] Autenticação e autorização validadas por testes negativos.
- [ ] Artefatos obsoletos não são exibidos como atuais.
- [ ] Quotas, retenção, exportação e exclusão operacionais.
- [ ] E2E crítico bloqueante.
- [ ] TLS e configurações de produção documentados.
- [ ] Firecrawl real validado com evidências.

### Release público estável

- [ ] Fase 5 concluída.
- [ ] Métricas e alertas operacionais.
- [ ] Backup e restauração testados.
- [ ] Topologia de concorrência suportada e documentada.
- [ ] Documentação da Fase 6 sincronizada.
- [ ] Revisão final de privacidade e tratamento de dados pessoais.

## 10. Acompanhamento

Ao iniciar uma tarefa:

1. marcar o item correspondente como em andamento no checklist;
2. registrar o PR associado;
3. manter um único responsável técnico pela decisão;
4. registrar bloqueios externos de forma explícita.

Ao concluir:

1. anexar comandos e resultados de validação;
2. atualizar critérios de aceite;
3. atualizar contagens de testes;
4. revisar se a tarefa criou nova dependência;
5. mover o próximo item desbloqueado para execução.

Próxima ação recomendada: confirmar os workflows no GitHub após o próximo push
ou pull request.
