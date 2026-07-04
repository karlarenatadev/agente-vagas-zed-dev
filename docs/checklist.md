# Checklist de Escalabilidade — import-vagas

## Objetivo

Preparar o `import-vagas` para escalar sem trocar Python, evoluindo a arquitetura atual com FastAPI, React, persistência estruturada, filas, limites, autenticação, observabilidade e testes de produção.

A decisão inicial é manter Python/FastAPI no backend. O foco não é trocar linguagem, e sim corrigir os pontos arquiteturais que impedem escala: estado local, ausência de identidade, ausência de limites, processamento síncrono pesado, falta de filas, pouca observabilidade produtiva e ausência de estratégia clara para múltiplas instâncias.

---

# 0. Fundação de qualidade

## Status atual

* [X] README atualizado com comandos de validação local.
* [X] Checklist/template de PR criado.
* [X] Backend CI alinhado com `pytest -v`.
* [X] Frontend CI usando `npm ci`.
* [X] Frontend CI executando Vitest.
* [X] Data Guard preservado.
* [X] Docs Check preservado.
* [X] Backend validado com 303 testes passando.
* [X] Frontend validado com 58 testes passando.
* [X] Lint e build frontend aprovados.
* [X] Data Guard aprovado com 8 testes.
* [X] M0-03 validada com 20 testes WebSocket focalizados.
* [X] M0-04 concluída com cache npm, branches e `concurrency` padronizados.
* [X] M1-01 concluída com ADR, grafo central e testes unitários de linhagem.
* [X] M1-02 concluída com manifesto, hashes e estados de atualidade.
* [X] M1-03A concluída para currículo e análise de vaga.
* [X] M1-03B concluída para match, foco, reconciliação, tailoring, PDI e Coach.
* [X] Confirmar execução real dos workflows após push/PR.

## Próxima ação imediata

* [X] Abrir PR da branch de qualidade.
* [X] Confirmar que todos os workflows passam no GitHub Actions.
* [X] Atualizar `docs/checklist.md` com os novos números:

  * backend: 303 testes;
  * frontend: 58 testes;
  * Data Guard: 8 testes;
  * build/lint: aprovados.

---

# 1. Escala de identidade e acesso

## Problema

O projeto não deve escalar com sessão baseada apenas em header ou query string. Para ambiente público, cada dado precisa estar vinculado a uma identidade real e autorizada.

## Checklist

* [ ] Definir modos de execução:

  * [ ] `APP_MODE=local`;
  * [ ] `APP_MODE=public`.
* [ ] Em modo local, permitir sessão anônima apenas explicitamente.
* [ ] Em modo público, bloquear uso sem autenticação.
* [ ] Escolher provedor de identidade:

  * [ ] Auth gerenciado;
  * [ ] JWT próprio;
  * [ ] OAuth;
  * [ ] outro.
* [ ] Criar `UserContext` no backend.
* [ ] Aplicar autorização em todas as rotas REST.
* [ ] Aplicar autorização no WebSocket.
* [ ] Remover confiança em `X-Session-Id` como identidade pública.
* [ ] Impedir que o frontend escolha diretamente o dono dos dados.
* [ ] Validar `Origin` no WebSocket.
* [ ] Criar testes negativos:

  * [ ] usuário A não acessa dados de B;
  * [ ] usuário A não altera dados de B;
  * [ ] troca manual de header/query não troca identidade efetiva;
  * [ ] sessão default é proibida em modo público.

## Critério de pronto

* [ ] Nenhum dado pessoal fica acessível sem identidade validada.
* [ ] REST e WebSocket usam a mesma identidade.
* [ ] Modo local e modo público estão claramente separados.
* [ ] Testes de autorização passam no CI.

---

# 2. Escala de persistência

## Problema

Persistência em Markdown local é boa para MVP, demo e portfólio, mas não escala bem para múltiplas instâncias. Cada container teria seus próprios arquivos.

## Caminho recomendado

Não migrar tudo de uma vez.

Evoluir em etapas:

1. manter Markdown local para ambiente local;
2. criar camada abstrata de armazenamento;
3. adicionar PostgreSQL para dados estruturados;
4. usar storage externo para arquivos grandes, se necessário;
5. manter Markdown como exportação/artefato legível, não como fonte principal de verdade em produção.

## Checklist

### 2.1 Camada de armazenamento

* [ ] Criar interface de persistência.
* [ ] Separar regra de negócio de leitura/escrita em arquivo.
* [ ] Centralizar acesso a sessões, artefatos e candidaturas.
* [ ] Evitar `open`, `unlink`, `read_text` e `write_text` espalhados em routers.
* [ ] Criar testes da camada de storage.

### 2.2 PostgreSQL

* [ ] Definir tabelas iniciais:

  * [ ] users;
  * [ ] sessions;
  * [ ] resumes;
  * [ ] job_descriptions;
  * [ ] matches;
  * [ ] application_focus;
  * [ ] applications;
  * [ ] artifacts;
  * [ ] audit_events.
* [ ] Definir migrations.
* [ ] Criar conexão com pooling.
* [ ] Criar configuração por ambiente.
* [ ] Criar testes com banco temporário.
* [ ] Definir backup e restore.

### 2.3 Artefatos Markdown

* [ ] Decidir quais artefatos continuam como Markdown.
* [ ] Salvar metadados dos artefatos no banco.
* [ ] Salvar conteúdo grande em storage adequado, se necessário.
* [ ] Manter exportação em Markdown para leitura humana.
* [ ] Não depender apenas da existência do arquivo para considerar etapa concluída.

## Critério de pronto

* [ ] O backend não depende de disco local para dados críticos em modo público.
* [ ] Múltiplas instâncias conseguem acessar o mesmo estado.
* [ ] Dados estruturados têm schema claro.
* [ ] Markdown vira artefato/exportação, não fonte única de verdade produtiva.

---

# 3. Escala de artefatos e invalidação

## Problema

Se currículo, vaga, perfil ou match mudam, relatórios derivados podem ficar obsoletos. Em escala, isso vira risco de exibir recomendação antiga como se fosse atual.

## Checklist

* [X] Criar grafo central de dependências.
* [X] Definir dependências:

  * [X] perfil altera vagas, cursos, match, reconciliação, tailoring, PDI e entrevista;
  * [X] currículo altera match, reconciliação, tailoring, PDI e entrevista;
  * [X] vaga altera match, reconciliação, tailoring, PDI e entrevista;
  * [X] match/foco altera reconciliação, tailoring, PDI e entrevista;
  * [X] tailoring altera PDI.
* [X] Criar testes unitários do contrato do grafo.
* [X] Criar manifesto de artefatos.
* [X] Registrar:

  * [X] versão do schema;
  * [X] data de geração;
  * [X] hash do conteúdo;
  * [X] hash das entradas;
  * [X] versão do gerador;
  * [X] status: atual, obsoleto, corrompido ou legado.
* [X] Detectar divergência de conteúdo e entradas sem apagar artefatos.
* [X] Criar testes unitários do registro e do manifesto.
* [X] Migrar currículo e análise de vaga para registro e invalidação central.
* [X] Registrar match, foco, reconciliação, tailoring e PDI no manifesto.
* [X] Preservar arquivos derivados ao marcá-los como obsoletos.
* [X] Criar testes de invalidação para as rotas migradas.
* [X] Impedir consumo crítico de artefato obsoleto em reconciliação, tailoring, PDI e Coach.
* [ ] Impedir que endpoints de leitura exibam artefato obsoleto como atual.
* [ ] Atualizar frontend para mostrar:

  * [ ] etapa ausente;
  * [ ] etapa atual;
  * [ ] etapa obsoleta;
  * [ ] etapa corrompida.
* [ ] Criar testes de invalidação para as rotas restantes.
* [ ] Criar testes de pipeline frontend.

## Critério de pronto

* [ ] Nenhum relatório derivado é exibido como atual sem validar suas entradas.
* [ ] A interface informa qual entrada mudou.
* [ ] O usuário sabe qual etapa precisa recalcular.
* [ ] Invalidação é centralizada, não espalhada em routers.

---

# 4. Escala de processamento assíncrono

## Problema

Análise de currículo, busca de vagas, Firecrawl, LLM, PDI e entrevista podem demorar. Não devem depender apenas de request síncrona.

## Arquitetura alvo

```text
Frontend
   ↓
FastAPI
   ↓
Fila de jobs
   ↓
Worker Python
   ↓
PostgreSQL / Redis / Storage
   ↓
Frontend acompanha status
```

## Checklist

* [ ] Identificar tarefas demoradas:

  * [ ] análise de currículo;
  * [ ] análise de vaga;
  * [ ] match;
  * [ ] Scout;
  * [ ] Curator;
  * [ ] Coach;
  * [ ] PDI;
  * [ ] tailoring.
* [ ] Escolher fila:

  * [ ] Celery;
  * [ ] RQ;
  * [ ] Arq;
  * [ ] Dramatiq.
* [ ] Escolher broker:

  * [ ] Redis;
  * [ ] RabbitMQ.
* [ ] Criar modelo de job:

  * [ ] id;
  * [ ] tipo;
  * [ ] status;
  * [ ] usuário;
  * [ ] sessão;
  * [ ] payload;
  * [ ] erro;
  * [ ] criado em;
  * [ ] atualizado em.
* [ ] Criar endpoint para iniciar job.
* [ ] Criar endpoint para consultar status.
* [ ] Criar atualização em tempo real via WebSocket/SSE.
* [ ] Criar retry com limite.
* [ ] Criar timeout por tarefa.
* [ ] Evitar reprocessamento duplicado.
* [ ] Criar idempotência para tarefas críticas.
* [ ] Criar testes de job:

  * [ ] sucesso;
  * [ ] erro;
  * [ ] retry;
  * [ ] timeout;
  * [ ] cancelamento;
  * [ ] duplicidade.

## Critério de pronto

* [ ] Tarefa longa não trava request principal.
* [ ] Usuário acompanha progresso.
* [ ] Worker pode ser escalado separado da API.
* [ ] Falha de provedor externo não derruba a API inteira.
* [ ] Jobs possuem rastreabilidade.

---

# 5. Escala de WebSocket

## Problema

WebSocket precisa de protocolo claro, limite de mensagem, autenticação, reconexão e controle de estado.

## Checklist

* [ ] Validar schema de entrada.
* [ ] Aceitar apenas payload JSON esperado.
* [ ] Exigir `type="message"`.
* [ ] Exigir `content` string.
* [ ] Definir tamanho máximo de mensagem.
* [ ] Restringir filtros e parâmetros aceitos.
* [ ] Responder erro controlado sem derrubar conexão quando possível.
* [ ] Encerrar conexão com código adequado em violação grave.
* [ ] Garantir que payload inválido não persiste estado.
* [ ] Implementar autenticação no handshake.
* [ ] Validar `Origin`.
* [ ] Criar heartbeat/ping.
* [ ] Criar reconexão no frontend com backoff.
* [ ] Evitar duplicação de mensagem após reconexão.
* [ ] Criar testes:

  * [ ] payload lista;
  * [ ] payload número;
  * [ ] payload `null`;
  * [ ] objeto sem `content`;
  * [ ] `content` não textual;
  * [ ] mensagem excessiva;
  * [ ] conexão viva após erro recuperável;
  * [ ] encerramento controlado;
  * [ ] reconexão frontend.

## Critério de pronto

* [ ] WebSocket não aceita payload livre.
* [ ] Mensagem inválida não chega ao Maestro.
* [ ] WebSocket funciona com múltiplas instâncias ou tem limitação documentada.
* [ ] Reconexão não duplica ações.

---

# 6. Escala de limites, quotas e custo

## Problema

LLM, Firecrawl, upload, WebSocket e armazenamento têm custo. Sem limite, um usuário ou script pode consumir recursos demais.

## Checklist

### 6.1 Limites de entrada

* [ ] Definir limite global de payload REST.
* [ ] Definir limite de upload.
* [ ] Definir limite de mensagem WebSocket.
* [ ] Definir limite de campos textuais.
* [ ] Definir limite de listas.
* [ ] Definir limite de candidaturas por usuário.
* [ ] Definir limite de sessões por usuário.
* [ ] Definir limite de artefatos por sessão.

### 6.2 Rate limiting

* [ ] Rate limit para leitura REST.
* [ ] Rate limit para mutação REST.
* [ ] Rate limit para upload.
* [ ] Rate limit para WebSocket.
* [ ] Rate limit para LLM.
* [ ] Rate limit para Firecrawl.
* [ ] Resposta padronizada para limite excedido.
* [ ] Header ou mensagem com orientação de retry.

### 6.3 Quotas

* [ ] Quota diária por usuário.
* [ ] Quota mensal por usuário.
* [ ] Quota por tipo de operação.
* [ ] Quota para chamadas externas.
* [ ] Quota de armazenamento.
* [ ] Bloqueio de abuso sem afetar outros usuários.

## Critério de pronto

* [ ] Input excessivo é rejeitado antes de chamar LLM ou Firecrawl.
* [ ] Uma identidade não consome quota de outra.
* [ ] Custo externo fica controlado.
* [ ] Bloqueios são rastreáveis nos logs/métricas.

---

# 7. Escala de observabilidade

## Problema

Em produção, não basta ter log local dentro do container. É preciso enxergar erro, latência, custo, fallback, volume, uso e falhas externas.

## Checklist

### 7.1 Logs

* [ ] Garantir logs em stdout/stderr para ambiente container.
* [ ] Manter logs estruturados em JSON.
* [ ] Adicionar correlation id/request id.
* [ ] Não logar currículo, prompt completo, token ou dado sensível.
* [ ] Registrar eventos importantes:

  * [ ] início/fim de job;
  * [ ] erro externo;
  * [ ] fallback;
  * [ ] rate limit;
  * [ ] quota excedida;
  * [ ] invalidação de artefato;
  * [ ] exclusão de dados.

### 7.2 Métricas

* [ ] Latência por endpoint.
* [ ] Taxa de erro por endpoint.
* [ ] Quantidade de conexões WebSocket.
* [ ] Tempo médio de job.
* [ ] Uso de Firecrawl.
* [ ] Uso de LLM.
* [ ] Fallbacks acionados.
* [ ] Jobs em fila.
* [ ] Jobs com erro.
* [ ] Armazenamento por usuário/sessão.

### 7.3 Healthcheck

* [ ] Manter `/health` como liveness.
* [ ] Criar `/ready` como readiness.
* [ ] Verificar banco.
* [ ] Verificar Redis/broker.
* [ ] Verificar diretório/storage gravável.
* [ ] Verificar configuração obrigatória.
* [ ] Não derrubar app inteiro por provedor opcional indisponível.
* [ ] Sinalizar modo degradado.

## Critério de pronto

* [ ] É possível investigar erro sem acessar container manualmente.
* [ ] É possível saber se o sistema está saudável.
* [ ] É possível medir custo e gargalo.
* [ ] Logs não expõem dados pessoais.

---

# 8. Escala de segurança e privacidade

## Problema

O projeto lida com currículo, vaga, perfil e dados de candidatura. Isso exige cuidado com privacidade antes de ambiente público.

## Checklist

* [ ] Documentar dados coletados.
* [ ] Documentar finalidade de uso.
* [ ] Documentar tempo de retenção.
* [ ] Criar exportação dos dados do usuário.
* [ ] Criar exclusão completa dos dados.
* [ ] Apagar artefatos derivados na exclusão.
* [ ] Apagar backups relacionados.
* [ ] Apagar temporários.
* [ ] Criar auditoria mínima sem conteúdo sensível.
* [ ] Definir política de retenção.
* [ ] Criar limpeza automática de sessões antigas.
* [ ] Configurar CORS por ambiente.
* [ ] Configurar trusted hosts.
* [ ] Configurar headers de segurança.
* [ ] Forçar HTTPS em produção.
* [ ] Usar secrets manager ou variáveis seguras.
* [ ] Não versionar `.env`.
* [ ] Não enviar token duradouro em query string.
* [ ] Revisar riscos de prompt injection em conteúdos de currículo/vagas.

## Critério de pronto

* [ ] Usuário consegue exportar e apagar seus dados.
* [ ] Dados sensíveis não aparecem em logs.
* [ ] Ambiente público não sobe sem configuração segura.
* [ ] Secrets não ficam no Git nem na imagem Docker.

---

# 9. Escala de deploy

## Problema

Antes de escalar horizontalmente, é preciso declarar qual topologia é suportada. Múltiplas instâncias com estado em memória ou disco local podem quebrar sessão, locks e WebSocket.

## Checklist

### 9.1 Deploy inicial seguro

* [ ] Definir ambiente alvo:

  * [ ] Render;
  * [ ] Railway;
  * [ ] AWS ECS;
  * [ ] AWS EC2;
  * [ ] Kubernetes;
  * [ ] outro.
* [ ] Criar `.env.example` completo.
* [ ] Criar Dockerfile de produção.
* [ ] Criar compose de produção, se fizer sentido.
* [ ] Separar configuração local e pública.
* [ ] Documentar comandos de deploy.
* [ ] Documentar rollback.

### 9.2 Concorrência

* [ ] Declarar se o backend suporta um ou múltiplos workers.
* [ ] Se for um worker:

  * [ ] documentar limitação;
  * [ ] impedir configuração insegura.
* [ ] Se forem múltiplos workers:

  * [ ] remover estado crítico da memória;
  * [ ] usar PostgreSQL/Redis;
  * [ ] coordenar locks fora do processo;
  * [ ] testar concorrência multiprocesso.
* [ ] Definir estratégia de WebSocket com load balancer.
* [ ] Definir sticky session ou estado externo.

### 9.3 Escala horizontal

* [ ] API escalável separada dos workers.
* [ ] Workers escaláveis por fila.
* [ ] Banco com pool configurado.
* [ ] Redis/broker monitorado.
* [ ] Storage externo para arquivos.
* [ ] Health/readiness usados pelo orquestrador.

## Critério de pronto

* [ ] A topologia documentada corresponde ao que foi testado.
* [ ] O deploy não depende de disco local para estado crítico.
* [ ] Múltiplas instâncias não corrompem dados.
* [ ] Rollback está documentado.

---

# 10. Escala de testes

## Problema

Para escalar com segurança, os testes precisam validar jornada real, autorização, dados, falhas externas e recuperação.

## Checklist

### 10.1 Backend

* [ ] Testar autorização por usuário.
* [ ] Testar invalidação de artefatos.
* [ ] Testar rate limit.
* [ ] Testar quotas.
* [ ] Testar jobs assíncronos.
* [ ] Testar banco/storage.
* [ ] Testar WebSocket.
* [ ] Testar erros externos.
* [ ] Medir cobertura com `pytest-cov`.

### 10.2 Frontend

* [ ] Testar `useWebSocket`.
* [ ] Testar `apiRequest`.
* [ ] Testar pipeline de etapas.
* [ ] Testar tracker de candidaturas.
* [ ] Testar estados loading/vazio/erro/sucesso.
* [ ] Testar reconexão.
* [ ] Testar artefato obsoleto na UI.

### 10.3 E2E

* [ ] Configurar Playwright.
* [ ] Subir backend e frontend reais no runner.
* [ ] Usar diretório/banco temporário.
* [ ] Usar provedores externos fake no E2E comum.
* [ ] Testar jornada:

  * [ ] currículo;
  * [ ] perfil;
  * [ ] vaga;
  * [ ] match;
  * [ ] foco;
  * [ ] tailoring;
  * [ ] PDI;
  * [ ] entrevista;
  * [ ] candidatura.
* [ ] Testar isolamento entre dois usuários.
* [ ] Testar alteração de entrada invalidando derivados.
* [ ] Testar reload no meio da jornada.
* [ ] Testar queda do backend durante streaming.
* [ ] Rodar E2E no CI.

## Critério de pronto

* [ ] Falha crítica bloqueia PR.
* [ ] CI roda backend, frontend, Data Guard, build e E2E.
* [ ] Cobertura é medida.
* [ ] Testes não dependem de chave real para passar.

---

# 11. Escala de integrações externas

## Problema

LLM e Firecrawl são gargalos de custo, latência e instabilidade.

## Checklist

* [ ] Criar camada única para provedores externos.
* [ ] Padronizar timeout.
* [ ] Padronizar retry com backoff.
* [ ] Padronizar fallback.
* [ ] Padronizar erro de domínio.
* [ ] Criar cache de respostas quando seguro.
* [ ] Identificar origem da resposta:

  * [ ] real;
  * [ ] llm;
  * [ ] simulated;
  * [ ] interna.
* [ ] Separar teste determinístico de teste real.
* [ ] Criar validação manual controlada do Firecrawl.
* [ ] Criar limite de custo por usuário.
* [ ] Criar métrica de chamadas externas.

## Critério de pronto

* [ ] Falha externa não derruba jornada inteira.
* [ ] Usuário sabe quando resultado é real, simulado ou interno.
* [ ] Custo externo é rastreável.
* [ ] Teste de CI não depende de crédito externo.

---

# 12. Ordem recomendada de implementação

## Sprint 1 — Fechar base atual

* [X] README de validação local.
* [X] PR template.
* [X] CI frontend com Vitest.
* [X] CI backend com pytest.
* [X] Cache npm baseado em `frontend/package-lock.json`.
* [X] Cancelamento de execuções antigas por workflow e ref.
* [ ] Confirmar workflows no GitHub após push/PR.
* [X] Atualizar `docs/checklist.md` com os resultados novos.

## Sprint 2 — WebSocket seguro

* [X] Schema de mensagem.
* [X] Limite de tamanho.
* [X] Erro controlado.
* [X] Testes backend.
* [ ] Testes frontend de reconexão.

## Sprint 3 — Identidade e modo público/local

* [ ] ADR de autenticação.
* [ ] `APP_MODE`.
* [ ] `UserContext`.
* [ ] Autorização REST.
* [ ] Autorização WebSocket.
* [ ] Testes negativos de acesso cruzado.

## Sprint 4 — Artefatos e invalidação

* [X] Grafo de dependências.
* [X] Manifesto.
* [X] Hash de entradas.
* [X] Estado atual/obsoleto/corrompido.
* [ ] Pipeline frontend refletindo atualidade.

## Sprint 5 — Persistência produtiva

* [ ] Interface de storage.
* [ ] PostgreSQL.
* [ ] Migrations.
* [ ] Pool de conexão.
* [ ] Testes de integração.
* [ ] Estratégia para Markdown como exportação.

## Sprint 6 — Jobs e filas

* [ ] Redis/broker.
* [ ] Worker.
* [ ] Modelo de job.
* [ ] Status de job.
* [ ] Retry/timeout.
* [ ] Frontend acompanhando progresso.

## Sprint 7 — Limites e quotas

* [ ] Rate limiting.
* [ ] Quotas.
* [ ] Limite de storage.
* [ ] Limpeza de sessão.
* [ ] Exportação/exclusão de dados.

## Sprint 8 — E2E e release público piloto

* [ ] Playwright.
* [ ] Jornada crítica.
* [ ] Dois usuários isolados.
* [ ] Falha/reconexão.
* [ ] Firecrawl real validado separadamente.
* [ ] Documentação de deploy.

---

# Definição de pronto para escala inicial

O projeto estará pronto para uma escala inicial controlada quando:

* [ ] CI completo passar em todo PR.
* [ ] E2E crítico estiver bloqueando merge.
* [ ] Usuários tiverem identidade e autorização.
* [ ] Dados críticos não dependerem de disco local.
* [ ] Tarefas longas rodarem em workers.
* [ ] WebSocket tiver autenticação, schema e reconexão.
* [ ] Rate limit e quotas estiverem ativos.
* [ ] Artefatos obsoletos não forem exibidos como atuais.
* [ ] Logs e métricas permitirem diagnóstico.
* [ ] Exportação e exclusão de dados estiverem funcionando.
* [ ] Topologia de produção estiver documentada e testada.

---

# Decisão técnica

Não trocar Python neste momento.

Manter:

* FastAPI para API;
* Python para workers;
* React para frontend;
* PostgreSQL para dados estruturados;
* Redis para cache, sessão curta, rate limit e fila;
* storage externo para arquivos/artefatos grandes, se necessário.

Trocar linguagem só deve ser considerado se houver evidência real de gargalo após medir:

* latência;
* CPU;
* memória;
* concorrência;
* custo;
* throughput;
* tempo de job.
