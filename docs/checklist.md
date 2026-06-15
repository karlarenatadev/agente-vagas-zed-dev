# Roadmap — Evolução do Import Vagas

## Auditoria atual

Última revisão: 2026-06-15.

Validação executada nesta revisão:

* [x] `npm run lint` concluído sem erros.
* [x] `npm run build` concluído sem erros.
  Os bloqueios de props em `App.tsx`/`StatusBar` e tipagem de `Skill` em `ChatMessage.tsx` foram corrigidos.
* [x] Backend compilado e aplicação FastAPI importada com sucesso.
* [x] Rotas REST e WebSocket registradas na aplicação.
* [x] Firecrawl CLI instalado no ambiente.
* [x] `FIRECRAWL_API_KEY` configurada em `backend/.env` e carregada por caminho absoluto.
* [ ] Suíte automatizada de testes disponível.
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

* [ ] Isolamento multiusuário: agentes leem/escrevem `data/*.md` globais sem
  `session_id`; usuários simultâneos sobrescrevem dados uns dos outros
  (refactor arquitetural, fora do escopo desta sessão).
* [ ] `applications.json`: read-modify-write sem lock (possível corrida).
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
* [ ] Conectar o Coach à descrição da vaga e ao relatório de aderência.
* [ ] Criar testes automatizados mínimos para backend e frontend.
* [x] Executar e registrar `docs/frontend-qa-checklist.md`.

## Barra de progresso recolhida + correção de ordem do chat

Sessão executada em 2026-06-15.

Rota de candidatura recolhida vira barra de progresso:

* [x] `ApplicationPipeline`: quando recolhida, renderiza `.pipeline-minibar`
  com 6 nós ligados por conectores, no estilo do mock de baixa fidelidade.
* [x] Cores seguem a paleta de status (concluído=verde, disponível=amarelo,
  bloqueado=cinza); nó atual com leve glow/escala; conector concluído em verde.

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
* [ ] Tratamento de erros completo.
  Situação atual: Coach e novas rotas têm tratamento explícito; falhas de Firecrawl no Scout podem ser ocultadas pelo fallback.
* [x] Manutenção do estado da sessão.

### O que iremos acrescentar

* [ ] Roteamento para análise de descrição de vaga.
* [ ] Roteamento para comparação vaga x currículo.
* [ ] Roteamento para sugestões seguras de currículo.
* [ ] Roteamento para geração de PDI por vaga.
* [ ] Roteamento para entrevista baseada em uma vaga específica.
* [ ] Etapa de reconciliação entre perfil, currículo e vaga.
* [ ] Mensagens mais claras quando houver conflito entre dados do usuário.
* [ ] Limpar também currículo, vaga analisada, match, tailoring e PDI ao refazer o diagnóstico.

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

* [ ] Gerar entrevista a partir da descrição da vaga analisada.
* [ ] Usar o relatório de aderência como contexto.
* [ ] Criar perguntas técnicas com base nas lacunas.
* [ ] Criar perguntas comportamentais com base nas responsabilidades da vaga.
* [ ] Adaptar feedback ao nível de aderência do usuário.
* [ ] Sugerir respostas mais estratégicas com base no currículo.
* [ ] Preparar roteiro de entrevista para vaga específica.

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

* [ ] Usar a descrição da vaga como contexto.
* [ ] Usar o relatório de aderência como contexto.
* [ ] Criar perguntas técnicas baseadas nos requisitos.
* [ ] Criar perguntas comportamentais baseadas nas responsabilidades.
* [ ] Criar perguntas sobre lacunas críticas.
* [ ] Gerar feedback direcionado.
* [ ] Criar plano de melhoria após a entrevista.

---

# 5. Consistência entre perfil, currículo e vaga

## O que temos

* [x] Perfil salvo em `data/user-profile.md`.
* [x] Análise de currículo salva em `data/resume-analysis.md`.
* [x] Análise de vaga salva em `data/job-description-analysis.md`.
* [x] Possibilidade de divergência entre perfil declarado e currículo analisado.

## O que iremos acrescentar

* [ ] Detectar conflito entre perfil e currículo.
* [x] Detectar conflito entre currículo e vaga.
* [ ] Detectar conflito entre perfil e vaga.
* [ ] Permitir escolher foco da candidatura.
* [ ] Permitir usar dados do currículo como base.
* [ ] Permitir usar dados do perfil como base.
* [ ] Permitir usar a vaga como foco principal.
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
* [ ] Ignorar também `data/applications.json` e futuros formatos de runtime não Markdown.

---

# 7. Dados reais com Firecrawl

## O que temos

* [x] Estrutura prevista para uso do Firecrawl.
* [x] Fallback local quando Firecrawl não retorna resultados.
* [x] Busca simulada funcionando.
* [x] Recomendações internas funcionando.

## O que iremos acrescentar

* [x] Instalar Firecrawl CLI.
* [x] Configurar `FIRECRAWL_API_KEY`.
* [x] Testar busca real de vagas diretamente pelo Firecrawl CLI.
* [ ] Testar busca real de cursos.
* [x] Validar que a busca real retorna URLs de vagas no CLI.
* [ ] Revalidar a busca completa pelo Scout com backend reiniciado e abertura do
  link de vaga no navegador.
* [ ] Validar salários.
* [ ] Validar requisitos extraídos.
* [ ] Registrar origem dos dados.
* [ ] Tratar resultados parciais.
* [x] Tratar ausência de resultados reais sem quebrar o fluxo por meio de fallback local.
* [ ] Expor ao usuário as falhas parciais do Firecrawl em vez de descartá-las silenciosamente.

---

# 8. Testes e validação

## O que temos

* [x] Validação atual de build.
* [x] Validação manual de lint.
* [x] Validação manual do backend.
* [x] Reexecutar teste integrado da análise de descrição de vaga.
* [x] Tratamento de entrada inválida na análise de vaga.

## O que iremos acrescentar

### Backend

* [ ] Testar análise de descrição de vaga de forma reproduzível.
* [ ] Testar comparação vaga x currículo de forma reproduzível.
* [ ] Testar ausência de currículo.
* [ ] Testar ausência de vaga.
* [ ] Testar geração de Markdown.
* [ ] Testar normalização de aliases.
* [ ] Testar cálculo de score.
* [ ] Testar geração do PDI personalizado.
* [ ] Testar ausência de currículo, vaga, relatório de aderência e sugestões de currículo no PDI.
* [ ] Testar leitura de `data/pdi-plan.md` pela API.

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
* [ ] Iniciar entrevista baseada na vaga.

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

# 10. Documentação

## O que temos

* [x] README inicial do projeto.
* [x] Explicação da arquitetura multiagente.
* [x] Explicação de instalação e execução.
* [x] Explicação do fluxo atual de uso.

## O que iremos acrescentar

* [ ] Atualizar a proposta do produto.
* [ ] Documentar a esteira de candidatura.
* [ ] Documentar análise de descrição de vaga.
* [ ] Documentar comparação vaga x currículo.
* [ ] Documentar sugestões seguras de currículo.
* [ ] Documentar PDI personalizado.
* [ ] Documentar arquivos gerados em `data/`.
* [ ] Documentar novas rotas REST.
* [ ] Criar seção de roadmap.
* [ ] Criar seção de decisões de arquitetura.
* [ ] Adicionar prints futuramente.
* [ ] Atualizar `README.md` para React 19, TypeScript 6, novas rotas e novos artefatos.
* [ ] Atualizar `plano.md`, que ainda descreve escopo e quantidade de perguntas antigos.
* [ ] Atualizar `docs/project-update-report.md` com os commits, validações e estado da entrevista atuais.

---

# 11. Ordem prática de evolução

## Etapa atual

* [x] **Garantir geração de `resume-analysis.md` durante upload/análise de currículo.**
  Validado com upload TXT real em 2026-06-14.
* [x] Integrar o componente `PdiPlan` ao frontend visível e à pipeline.
* [x] Adicionar rota de leitura para `resume-analysis` em `data_files.py`.
* [ ] Conectar a entrevista à vaga analisada e ao match.
* [ ] Criar testes mínimos dos fluxos críticos.

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
* [ ] Conectar Coach à vaga analisada e ao relatório de aderência.
* [ ] Resolver divergência entre perfil, currículo e vaga.
* [x] Configurar dados reais com Firecrawl (`FIRECRAWL_API_KEY`).
* [x] Separar arquivos locais de `data/` do que deve ser versionado (privacidade).
* [ ] Criar testes mínimos automatizados.
* [ ] Atualizar documentação (README, plano.md, project-update-report.md).

---

# 12. Definição de pronto

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

# 13. Career Arcade Pipeline

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

# Status de Implementação Detalhado

## Arquitetura completa validada

### Backend (FastAPI + Python)
* [x] 22 endpoints HTTP, 1 WebSocket e 4 rotas automáticas de documentação registrados
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
- ✅ Adicionado endpoint `GET /api/data/resume-analysis` em `data_files.py`
- ✅ Pipeline atualizada para ler o arquivo via API
- ✅ API passou a ser a fonte principal; `localStorage` obsoleto é removido quando o artefato não existe
- ✅ Validado: lint e build passando sem erros

### 2. ~~Firecrawl estava quebrando~~ ✅ RESOLVIDO
**Status:** RESOLVIDO em 2026-06-14

**Descoberta:**
- Firecrawl CLI está instalado e funcionando perfeitamente (versão 1.18.1)
- API Key configurada corretamente no `.env`
- O problema era o **formato de resposta** que mudou na versão atual

**Formato antigo esperado:**
```json
{"data": [...]}
```

**Formato atual retornado (v1.18.1):**
```json
{
  "success": true,
  "data": {"web": [...]},
  "id": "...",
  "creditsUsed": 2
}
```

**Correções aplicadas:**
- ✅ Atualizado `Scout._run_firecrawl_search()` para processar `data.web`
- ✅ Atualizado `Curator._normalize_search_payload()` para processar `data.web`
- ✅ Mantida retrocompatibilidade com formatos alternativos
- ✅ Fallbacks locais continuam funcionando
- ✅ Validado: `firecrawl search "test" --json` retorna 10 resultados reais

### 3. ~~Componente PDI não está integrado à interface~~ ✅ RESOLVIDO
**Status:** RESOLVIDO em 2026-06-14

**Correções aplicadas:**
- `PdiPlan.tsx` é carregado sob demanda em um modal acessível.
- Pipeline libera a ação do PDI após a conclusão das sugestões seguras.
- Plano salvo é recuperado por `GET /api/pdi/latest`.
- Geração bem-sucedida atualiza imediatamente o estado da pipeline.

**Validações executadas:**
- [x] `npm run lint`
- [x] `npm run build`
- [x] `py_compile` e importação do FastAPI com 27 rotas.
- [x] Round-trip automatizado entre dados estruturados e `pdi-plan.md`.
- [x] Validar o modal e a geração completa no Chrome em `1366x768` e `390x844`.
- [x] Validar estado vazio, erro de geração, persistência e ausência de overflow horizontal.

### 4. ~~Rota de leitura para resume-analysis ausente~~ ✅ RESOLVIDO
**Status:** RESOLVIDO em 2026-06-14 (mesmo commit do item 1)

## Melhorias recomendadas (não bloqueantes)

### Privacidade e dados locais
* [x] Adicionar `data/*.md` ao `.gitignore` (evitar commit de dados pessoais)
* [x] Remover arquivos de runtime do rastreamento do Git
* [x] Manter `data/README.md` e permitir exemplos sanitizados `*.example.md`
* [x] Documentar em `data/README.md` que `data/` contém estado local potencialmente sensível

### Testes automatizados
* [ ] Criar testes unitários para agentes principais
* [ ] Criar testes de integração para rotas críticas
* [ ] Criar testes E2E para fluxo completo de candidatura
* [ ] Adicionar validação de schemas dos arquivos Markdown

### Documentação
* [ ] Atualizar `README.md` com rotas e artefatos atuais
* [ ] Atualizar `plano.md` com escopo e perguntas corretos
* [ ] Atualizar `docs/project-update-report.md` com commits recentes
* [ ] Criar diagramas de fluxo de dados
* [ ] Documentar estrutura dos arquivos Markdown em `data/`

### Performance
* [ ] Aplicar lazy loading em todos os módulos principais
* [ ] Revisar tamanho do bundle (atual: 357,78 kB principal + 171,20 kB chat)
* [ ] Evitar duplicação de tipos TypeScript
* [ ] Otimizar imports e tree-shaking

### Configuração externa
* [x] Configurar `FIRECRAWL_API_KEY` no ambiente
* [x] Testar busca real de vagas diretamente pelo Firecrawl CLI
* [ ] Testar busca real de cursos com Firecrawl
* [ ] Revalidar o fluxo Scout/backend e a abertura da vaga no navegador
* [ ] Expor falhas parciais do Firecrawl ao usuário (atualmente silenciosas)

## Próximas features planejadas

### Coach conectado à vaga
* [ ] Usar descrição da vaga como contexto
* [ ] Usar relatório de aderência como contexto
* [ ] Criar perguntas técnicas baseadas nos requisitos
* [ ] Criar perguntas comportamentais baseadas nas responsabilidades
* [ ] Gerar feedback direcionado às lacunas identificadas

### Reconciliação de dados
* [ ] Detectar conflito entre perfil declarado e currículo analisado
* [ ] Detectar conflito entre currículo e vaga
* [ ] Permitir escolher foco da candidatura (perfil vs currículo vs vaga)
* [ ] Atualizar perfil somente com confirmação do usuário

### Isolamento multiusuário
* [ ] Implementar sessions ou user IDs
* [ ] Separar dados por usuário em `data/{user_id}/`
* [ ] Evitar sobrescrita de dados entre usuários simultâneos
* [ ] Adicionar lock em operações read-modify-write (ex: applications.json)
