# Relatório de andamento do projeto

Data do levantamento: 2026-06-27

## Rodadas P0 locais de estabilização (sobre `d14e2d1`, ainda não commitadas)

Sequência de micro-rodadas focadas em robustez/segurança, sem depender de
ambiente externo (sem Firecrawl real, sem E2E):

1. Validação de artefatos Markdown no consumo: ausente/vazio → HTTP 400;
   corrompido/binário/não-UTF-8 → HTTP 409 controlado (`read_required` /
   `read_optional_text`). Cobertura em `test_artifact_corruption.py`.
2. Confirmação antes de atualizar o perfil: o upload de currículo não grava mais
   o perfil silenciosamente; preview + `POST /api/resume/apply-profile`
   (`confirm: true`). Cobertura em `test_resume_profile_confirmation.py`.
3. Isolamento da sessão default em `data/sessions/_default/`; `data/*.md` soltos
   na raiz viram legado e não são consumidos (sem apagar nada). Cobertura em
   `test_session.py` e `test_session_default_isolation.py`.
4. Matriz de falhas REST + WebSocket (reconexão sem duplicar, replay sem avançar
   estado, estado corrompido → fallback, JSON inválido → erro controlado).
   Cobertura em `test_chat_websocket_failures.py`.
5. Hardening da escrita atômica (retry + backoff exponencial) para o
   `PermissionError` transitório do Windows no `os.replace`.

Validação: backend **221 testes passando** (`pytest -q`, 0 falhas; 1
`PendingDeprecationWarning` pré-existente do Starlette). A suíte frontend não foi
reexecutada nesta rodada — mantém a contagem anterior (26). Mudanças locais,
ainda não commitadas. As pendências P0 que dependem de ambiente externo
(Firecrawl real com chave/créditos e E2E completo) seguem em aberto.

---

Data do levantamento: 2026-06-26

## Estado atual (fallback inteligente e recuperação visual de sessão)

Desde o levantamento de 2026-06-20, o projeto fechou o loop conversacional da
esteira de candidatura, ganhou containerização, passou a honrar o foco da
candidatura ponta a ponta e endureceu os fluxos dependentes de LLM, Firecrawl e
WebSocket. A referência atual é o commit `d14e2d1`, *"feat: recupera o estado
visual da sessao no primeiro load do WebSocket"*, de 2026-06-26.

Antes desta atualização documental, o repositório estava na branch `main`,
sincronizado com `origin/main` (0 à frente, 0 atrás) e com a árvore de trabalho
limpa.

### Principais entregas do período (2026-06-23 a 2026-06-26)

1. Coach conectado à vaga analisada (`7ec128b`):
   - O Coach lê `job-description-analysis.md` e `resume-match-report.md` além de
     Scout/Curator.
   - O `interview_context` prioriza a vaga analisada (título + empresa); as
     perguntas técnicas e de cenário são calibradas pelos requisitos da vaga e
     pelas lacunas do match.
   - O gate de início foi relaxado: a entrevista começa com Scout **ou** vaga
     analisada. Cobertura em `test_coach.py`.

2. Roteamento conversacional do Maestro (`21fda2b`):
   - O menu passou a ter duas esteiras — Carreira (A–D) e Candidatura (E–I).
   - As opções E–I (analisar vaga, comparar, sugestões, PDI e reconciliação),
     antes só acessíveis por botão/REST, agora rodam pelo chat.
   - Cobertura em `test_maestro_routing.py`.

3. Menu em fluxo master/detail no rodapé do chat (`ccc1035`, `68308cf`):
   - `ChatInput` substituiu o accordion por dois pills de esteira; ao escolher,
     só as opções daquela esteira aparecem, com botão para voltar.

4. Dockerização (`a18e469`):
   - `backend/Dockerfile` (`python:3.12-slim`, usuário sem privilégios,
     `HEALTHCHECK` em `/health`), `frontend/Dockerfile` (build Vite servido por
     Nginx com proxy reverso de `/api` e `/ws`) e `docker-compose.yml` com os
     três serviços e volume `backend-data`, além do profile `mock`.
   - `docker compose up --build` sobe o site em http://localhost:8080.

5. Falha degradada do Firecrawl exposta (`520a931`):
   - O Scout sinaliza `status_busca: real_degraded` com `busca_degradada` e
     `aviso_degradacao` quando a query específica falha e só a ampla recupera.
   - O `ScoutReport` mostra um banner de degradação distinto do banner de
     simulação total.

6. Foco da candidatura (`520a931`):
   - `PUT /api/reconciliation/focus` persiste o foco (perfil/currículo/vaga) na
     linha "Foco da candidatura:" do perfil.
   - Match, Tailor e PDI leem o foco via `resolve_focus` (precedência: corpo da
     requisição > perfil > "vaga") e calibram o `next_steps`.
   - O seletor de foco no `ResumeMatchReport` persiste a escolha ao clicar,
     fechando o loop no frontend.

7. Cliente LLM configurável e erros controlados (`b5fc5b5`):
   - `LLM_BASE_URL` permite usar OpenAI, OpenRouter, MiMo e outros provedores
     compatíveis com a API OpenAI sem trocar o SDK.
   - `call_llm` e `stream_llm` tratam a classe-base `openai.APIError`, convertendo
     falhas de upstream em `LLMProviderError` sem expor traceback ao usuário.
   - O caminho real foi validado com chamadas a provedores compatíveis; essa
     validação não foi repetida neste levantamento local.

8. Fallback do Scout via LLM (`1bf5e6c`):
   - A cadeia agora é Firecrawl → LLM disponível → simulação determinística.
   - Falta de créditos do Firecrawl é distinguida de rate limit por
     `FirecrawlCreditError`, com `status_busca: no_credits`.
   - O LLM produz até três sugestões coerentes com o perfil. Elas usam
     `source="llm"`, não possuem link clicável e aparecem no frontend com badge
     "Sugerida por IA" e aviso de que não são vagas verificadas.

9. Recuperação visual da sessão no WebSocket (`d14e2d1`):
   - No primeiro load da aba, `useWebSocket` envia `replay=1`; o Maestro repinta
     a pergunta atual do quiz, menu, Coach ou prompt de descrição de vaga.
   - O replay não grava arquivos, não avança etapas e não emite `__STATE__`.
   - Reconexões transitórias omitem o flag, evitando expor a reconexão ou
     duplicar o prompt.

10. Docker validado ponta a ponta:
    - Além dos Dockerfiles e do Compose já entregues, foram verificados build das
      imagens, healthcheck do backend, SPA no Nginx, proxy `/api` e upgrade do
      WebSocket.

### Validações executadas no período

* Backend: `backend/.venv/Scripts/python.exe -m pytest -q` em **177 testes
  passando**, incluindo concorrência, fallback do Scout e replay de sessão.
  Há 1 `PendingDeprecationWarning` do Starlette relacionado a `import multipart`.
* Frontend: `npm run test` em **26 testes passando**, `npm run lint` e
  `npm run build` sem erros.
* Build atual: 2.415 módulos transformados; bundle principal de 376,81 kB e
  chunk do chat de 174,29 kB. O Vite apenas reportou observação de timing do
  plugin `rolldown:vite-resolve`.
* Nota de execução: a primeira tentativa do backend com o Python global falhou
  por ausência de `pytest`; a suíte foi então executada com sucesso pelo ambiente
  virtual local em `backend/.venv`.

### Estado da entrevista (Coach)

A entrevista deixou de ser puramente genérica. Quando há vaga analisada e
relatório de aderência, o Coach calibra as perguntas pela vaga e pelas lacunas
do match. O fluxo de cinco perguntas e o fallback local seguem funcionando
quando os artefatos estão ausentes. Pendência conhecida: o feedback ainda não é
calibrado pelo nível de aderência (texto genérico).

### Pendências priorizadas após este levantamento

1. Validar a busca real do Firecrawl com chave e créditos: salários, requisitos
   extraídos, origem dos dados e abertura dos links.
2. Criar testes E2E do fluxo completo de candidatura e validação dos schemas
   Markdown.
3. Ampliar os testes de estabilidade para reconexão real do WebSocket durante
   streaming longo.
4. Calibrar o feedback do Coach pelo nível de aderência e pelas lacunas do
   currículo, não apenas as perguntas.
5. Sugerir cursos pagos no PDI quando fizer sentido, normalizar links no
   `CuratorReport` e migrar dados legados de `data/*.md` para sessões.
6. Sincronizar `plano.md`, que ainda apresenta a recuperação visual do primeiro
   load do WebSocket como pendente.
7. Acompanhar a depreciação de `multipart` sinalizada pelo Starlette na suíte do
   backend.

---

Data do levantamento: 2026-06-20

## Melhorias realizadas após a avaliação técnica

Após a avaliação inicial do projeto **Agente Import Vagas**, foram realizadas micro-rodadas de estabilização com foco em segurança básica, robustez do frontend, tratamento de erros, WebSocket e documentação de acompanhamento.

### 1. Higiene de repositório e privacidade básica

Foi reforçada a proteção de arquivos locais e sensíveis no repositório.

Melhorias realizadas:

* `.gitignore` atualizado para proteger arquivos `.env`, `.env.*`, logs, caches e diretórios de dados locais.
* `data/` e `backend/data/` passaram a ser tratados explicitamente como diretórios locais que não devem ser versionados.
* `backend/.env.example` foi sanitizado com placeholders seguros.
* Variáveis de logging foram adicionadas ao `backend/.env.example`.
* README recebeu nota de privacidade explicando que `data/` pode conter currículo, vaga, match, sugestões e PDI.
* Ficou documentado que dados reais sensíveis não devem ser usados em produção sem proteção adicional.

### 2. Criação do helper centralizado de API no frontend

Foi criado o helper `apiRequest` para centralizar e normalizar chamadas REST no frontend.

Melhorias realizadas:

* Leitura da resposta como texto antes de tentar converter para JSON.
* Tratamento seguro para corpo vazio.
* Tratamento de respostas HTML ou texto inesperado.
* Normalização de erros `400`, `413`, `422`, `500`, erro de rede e timeout.
* Extração mais segura de mensagens vindas de `detail`, `message` ou `error`.
* Suporte a `detail` em lista, como nos erros padrão do FastAPI.
* Timeout com `AbortController`, evitando loading infinito em requisições penduradas.

### 3. Migração dos fluxos principais para `apiRequest`

Os principais fluxos REST do frontend foram migrados para o helper centralizado.

Componentes migrados:

* `ResumeUpload.tsx`
* `JobDescriptionAnalyzer.tsx`
* `ResumeMatchReport.tsx`
* `ResumeTailoringSuggestions.tsx`
* `PdiPlan.tsx`
* `ApplicationPipeline.tsx`
* `ProfilePanel.tsx`
* `ApplicationTracker.tsx`

Com isso, os fluxos abaixo passaram a lidar melhor com falhas:

* upload de currículo;
* análise de vaga;
* geração e leitura de match;
* reconciliação do relatório de match;
* geração de sugestões seguras;
* leitura e geração de PDI;
* leitura da pipeline;
* leitura do perfil;
* leitura, edição e exclusão de candidaturas.

### 4. Melhoria no tratamento de erros do frontend

O frontend passou a apresentar comportamento mais previsível em cenários de falha.

Melhorias realizadas:

* Erros `422` do FastAPI agora viram mensagens amigáveis.
* Erros `500` com HTML ou texto técnico não vazam mais para a interface.
* Respostas vazias não quebram mais os componentes.
* Payload inesperado é tratado como erro amigável.
* Timeout não deixa loading preso indefinidamente.
* Estados anteriores são preservados quando esse já era o comportamento esperado.
* Estados de loading, erro, vazio e sucesso foram mantidos sem redesenhar a interface.

### 5. ApplicationPipeline mais resiliente

O `ApplicationPipeline` foi ajustado para usar `apiRequest` na leitura de dados.

Melhorias realizadas:

* `readDataFile` deixou de depender de `fetch + response.ok + response.json()`.
* Erros de leitura agora são normalizados pelo helper.
* Em caso de falha, a pipeline preserva o snapshot anterior.
* A nota de sincronização existente foi mantida.
* O empty state continuou funcionando.

### 6. ProfilePanel e ApplicationTracker mais robustos

Os painéis de perfil e acompanhamento de candidaturas também foram migrados para `apiRequest`.

Melhorias realizadas:

* `ProfilePanel` passou a tratar melhor falhas no `GET /api/profile/`.
* `ApplicationTracker` passou a tratar melhor `GET`, `PATCH` e `DELETE`.
* Erros `422`, `500`, corpo vazio, texto inesperado e timeout passaram a ser normalizados.
* O perfil carregado anteriormente continua preservado em caso de falha.
* A lista de candidaturas não é apagada quando ocorre erro em uma mutação.

### 7. WebSocket com feedback em falha de envio

O envio de mensagens via WebSocket foi ajustado para não falhar silenciosamente.

Melhorias realizadas:

* `sendMessage` agora retorna `true` quando a mensagem é enviada.
* `sendMessage` retorna `false` quando o socket não está aberto.
* Quando a conexão está fechada, o usuário recebe mensagem amigável.
* Se a conexão cair entre o clique e o envio, o hook detecta o problema.
* Estados de loading e streaming são liberados corretamente.
* O fluxo normal de chat continua funcionando quando a conexão está aberta.

### 8. Aumento da cobertura de testes no frontend

Os testes do frontend foram ampliados durante as rodadas de estabilização.

Melhorias realizadas:

* Cobertura adicionada para erro `422` com `detail` em lista.
* Cobertura adicionada para erro `500` com corpo não JSON.
* Cobertura adicionada para resposta vazia.
* Cobertura adicionada para HTML/texto inesperado.
* Cobertura adicionada para falha de envio com WebSocket fechado.
* Testes passaram de forma progressiva até chegar a 25 testes passando.

Validações executadas:

* `npm run test` passou.
* `npm run lint` passou.
* `npm run build` passou.
* `git diff --check` passou sem erro crítico.

### 9. Checklist de acompanhamento atualizado

O checklist do projeto passou a acompanhar as micro-rodadas de estabilização.

Melhorias realizadas:

* Registro da criação e aplicação do `apiRequest`.
* Registro da migração de componentes para tratamento de erro normalizado.
* Registro da correção do envio silencioso no WebSocket.
* Registro das validações executadas.
* Registro das pendências restantes, como testes E2E, validação backend e reconexão WebSocket mais realista.

### 10. Resultado geral das melhorias

Após as estruturações realizadas, o projeto ficou mais estável no frontend e mais seguro para versionamento local.

Principais ganhos:

* O frontend ficou mais resiliente a falhas de API.
* O usuário recebe feedback melhor em erros REST e WebSocket.
* O risco de loading infinito foi reduzido.
* O risco de quebra por resposta vazia ou não JSON foi reduzido.
* O repositório ficou mais protegido contra versionamento acidental de dados sensíveis.
* A documentação começou a acompanhar melhor a evolução do projeto.
* A base ficou mais preparada para as próximas etapas: validação backend, E2E e CI/CD.

---

Data do levantamento: 2026-06-13

## Resumo executivo

O projeto evoluiu de uma interface conversacional básica para uma plataforma de carreira com frontend React, backend FastAPI, estado persistido em Markdown e quatro papéis de agente: Maestro, Scout, Curator e Coach.

Os últimos updates relevantes foram concluídos em 2026-06-07. O repositório está na branch `main`, sincronizado com `origin/main`, sem alterações locais pendentes. O último commit é `132b5f6`, de 2026-06-07 20:15:33 -03:00.

O fluxo funcional mais recente avançou por:

1. Diagnóstico profissional concluído.
2. Perfil consolidado.
3. Busca de oportunidades executada com fallback simulado.
4. Trilha de aprendizado gerada com base interna.
5. Entrevista simulada iniciada.
6. Parada atual na Pergunta 1, aguardando resposta do usuário.

## O que temos hoje

1. Frontend:
   - Aplicação React com TypeScript e Vite.
   - Layout de copiloto de carreira com painel lateral de perfil.
   - Área de ações para oportunidades, lacunas, entrevista e novo diagnóstico.
   - Chat com streaming por WebSocket.
   - Quiz de perfil com retomada de sessão.
   - Upload e análise de currículo em PDF, DOCX ou TXT.
   - Painel de acompanhamento de candidaturas.
   - Interface responsiva e componentes carregados sob demanda.

2. Backend:
   - API FastAPI com endpoint de saúde.
   - WebSocket para conversa e streaming dos agentes.
   - Rotas REST para perfil, arquivos de dados, candidaturas e currículo.
   - Persistência local em arquivos Markdown.
   - Análise heurística de currículo e sugestão de atualização do perfil.
   - Fallbacks locais para manter os fluxos funcionando quando LLM ou Firecrawl não estão disponíveis.

3. Maestro:
   - Inicialização e leitura do estado salvo.
   - Quiz de sete perguntas.
   - Retomada de quiz incompleto.
   - Consolidação do perfil e funções alvo.
   - Roteamento para Scout, Curator e Coach.
   - Controle da sequência da entrevista.
   - Tratamento de erros e manutenção do estado da sessão.

4. Scout:
   - Busca e análise de oportunidades.
   - Cálculo de aderência.
   - Comparação de habilidades técnicas e soft skills.
   - Identificação de requisitos recorrentes.
   - Priorização de candidatura e dicas para currículo.
   - Fallback com oportunidades simuladas quando a busca real não retorna resultados.

5. Curator:
   - Normalização e priorização das lacunas detectadas pelo Scout.
   - Recomendações gratuitas, referências oficiais, opções pagas e projetos práticos.
   - Organização em "estudar agora" e "estudar depois".
   - Base interna de recomendações quando o Firecrawl não está disponível.

6. Coach:
   - Entrevista estruturada em cinco perguntas.
   - Alternância entre perguntas comportamentais e técnicas.
   - Feedback por resposta.
   - Avaliação final e áreas de melhoria.
   - Fallback local quando o LLM não responde.

## Linha do tempo dos updates

1. 2026-06-05:
   - Implementado upload e análise de currículo.
   - Adicionada extração de habilidades técnicas e soft skills.
   - Criada integração da análise com o perfil.
   - Ajustadas rotas, configuração e inicialização local.
   - Evoluído o gerenciamento visual do perfil.

2. 2026-06-07, início:
   - Implementada retomada do quiz e melhoria do estado da sessão.
   - Reorganizado o pós-diagnóstico como uma esteira de carreira.

3. 2026-06-07, meio:
   - Scout evoluído para inteligência de oportunidades, scores e lacunas.
   - Curator evoluído para trilhas de aprendizado priorizadas.
   - Adicionada base interna de cursos e normalização de habilidades.

4. 2026-06-07, fim:
   - Coach e Maestro reforçados com tratamento de erros e continuidade da entrevista.
   - Interface amplamente reorganizada.
   - Painel de perfil e estilos refinados no último commit.

Desde o update de perfil de 2026-06-05 até o estado atual, foram alterados 21 arquivos, com 3.585 linhas adicionadas e 593 removidas.

## Estado atual dos dados

1. Perfil salvo em `data/user-profile.md`:
   - Área: Frontend.
   - Nível: Sênior.
   - Preferência: Presencial.
   - Localização: Salvador, Bahia.
   - Objetivo: Trilha de liderança.
   - Habilidade atual informada: js.
   - Funções alvo: Engenheiro Frontend Sênior, Líder de Desenvolvimento UI e Arquiteto Frontend.

2. Análise de currículo em `data/resume-analysis.md`:
   - Detectou perfil de Ciência de Dados Júnior.
   - Detectou Python, SQL, Power BI e Git.
   - Esse resultado diverge do perfil atual de Frontend Sênior e precisa ser confirmado ou reconciliado pelo usuário.

3. Busca em `data/job-search-results.md`:
   - Três oportunidades simuladas.
   - Scores entre 23/100 e 30/100.
   - Principais lacunas: JavaScript, React, TypeScript, CSS, Git, HTML e consumo de APIs.
   - Nenhuma vaga real foi retornada pelo Firecrawl nessa execução.

4. Trilha em `data/course-recommendations.md`:
   - Sete habilidades priorizadas.
   - JavaScript, React, TypeScript, CSS, Git e HTML marcadas para estudo imediato.
   - Consumo de APIs marcado para estudo posterior.
   - Recomendações geradas por base interna porque o Firecrawl CLI não foi encontrado.

5. Entrevista em `data/interview-session.md`:
   - Contexto: posição baseada no perfil.
   - Pergunta atual: 1 de 5.
   - A Pergunta 1 foi salva.
   - Ainda não existe resposta R1.

## Onde paramos

O ponto funcional exato é a entrevista simulada, Pergunta 1. O próximo passo do fluxo do usuário é responder à pergunta registrada em `data/interview-session.md`. Depois disso, o Maestro deve avaliar R1, salvar a resposta e gerar a Pergunta 2.

O ponto técnico exato é o refinamento recente do painel de perfil e do CSS. O build de produção está funcionando, mas o lint ainda possui uma falha no componente ProfilePanel: a carga inicial chama uma função que atualiza estado sincronamente dentro de um `useEffect`.

## Validação executada em 2026-06-13

1. Git:
   - Branch `main`.
   - Sincronizada com `origin/main`.
   - Zero commits à frente ou atrás.
   - Árvore de trabalho limpa.

2. Frontend:
   - `npm run build`: sucesso.
   - 2.398 módulos transformados.
   - Bundle JavaScript principal com 512,23 kB.
   - Alerta de chunk acima de 500 kB.
   - `npm run lint`: falha com um erro em ProfilePanel.tsx, linha 300.

3. Backend:
   - Compilação dos módulos Python: sucesso.
   - Importação da aplicação FastAPI: sucesso.
   - Aplicação identificada como Recoloca IA, versão 1.0.0.

4. Testes:
   - Não foi encontrada suíte automatizada de testes para frontend ou backend.

## Pendências prioritárias

1. Corrigir o erro de lint no carregamento do ProfilePanel.
2. Instalar e configurar o Firecrawl CLI para validar vagas e cursos reais.
3. Reconciliar a divergência entre o currículo de Ciência de Dados Júnior e o quiz de Frontend Sênior.
4. Retomar e concluir a entrevista simulada iniciada.
5. Criar testes para quiz, persistência de sessão, Scout, Curator, Coach, upload de currículo e WebSocket.
6. Reduzir ou dividir o bundle principal, atualmente acima do limite recomendado de 500 kB.
7. Atualizar a documentação, que ainda apresenta versões e estrutura parcialmente anteriores ao código atual.

## Próxima sequência recomendada

1. Estabilização:
   - Corrigir lint.
   - Adicionar testes mínimos dos fluxos críticos.
   - Confirmar build e execução integrada.

2. Dados reais:
   - Configurar Firecrawl.
   - Executar uma busca real.
   - Validar extração, links, salários, requisitos e tratamento de resultados parciais.

3. Consistência do perfil:
   - Criar uma etapa explícita para o usuário escolher entre dados do currículo e respostas do quiz quando houver conflito.
   - Normalizar aliases como `js` para `JavaScript` antes do cálculo de aderência.

4. Experiência completa:
   - Concluir a entrevista atual.
   - Validar a esteira inteira: currículo ou quiz, Scout, Curator, Coach e candidaturas.

## Erros e limitações observados

1. Firecrawl CLI não encontrado na última execução do Curator.
2. Busca real do Scout sem resultados; oportunidades simuladas foram usadas.
3. Lint do frontend com um erro.
4. Bundle principal acima de 500 kB.
5. Ausência de testes automatizados.
6. Divergência entre análise de currículo e perfil salvo.
