# Checklist de QA do frontend

Este roteiro cobre a identidade Career Arcade Pipeline e a regressão dos fluxos já existentes.

## Fluxo feliz

* [x] Abrir a aplicação e confirmar que a pipeline mostra Currículo, Vaga, Match, Sugestões, PDI e Entrevista.
* [x] Enviar um currículo PDF, DOCX ou TXT válido.
* [ ] Confirmar o estado de sucesso do currículo e a atualização do perfil.
* [x] Colar uma descrição completa de vaga.
* [x] Confirmar cards de resumo, palavras-chave, requisitos e alertas.
* [x] Comparar a vaga com o currículo.
* [x] Confirmar score, evidências fortes, parciais e ausentes.
* [x] Gerar sugestões seguras de currículo.
* [x] Copiar uma seção e confirmar a troca temporária do texto para “Copiado”.
* [x] Confirmar que PDI aparece apenas como fase futura, sem ação ativa.

## Fluxos de erro

* [ ] Tentar analisar uma vaga com menos de 40 caracteres.
* [ ] Tentar comparar sem currículo analisado.
* [ ] Tentar comparar sem vaga válida.
* [ ] Tentar gerar sugestões sem relatório de match.
* [ ] Parar o backend e confirmar uma mensagem amigável no frontend.
* [ ] Simular arquivo ausente ou inválido e confirmar que a aplicação não quebra.
* [ ] Reconectar o backend e confirmar que o chat recupera o estado de conexão.

## Regressão

* [x] O chat continua enviando e recebendo mensagens por WebSocket.
* [ ] O ProfilePanel continua carregando o perfil.
* [ ] O quiz continua abrindo e recebendo respostas.
* [x] O upload de currículo continua funcionando.
* [x] A análise de vaga continua salvando o resultado.
* [x] O match continua funcionando.
* [x] As sugestões seguras continuam funcionando.
* [ ] O painel de candidaturas continua abrindo.
* [ ] As rotas de leitura continuam funcionando.

## Visual

* [x] Desktop grande: pipeline em seis colunas, sem sobreposição.
* [ ] Notebook: pipeline em duas linhas de três etapas.
* [ ] Tablet: pipeline em duas colunas.
* [x] Mobile: pipeline vertical com rolagem interna.
* [x] Sidebar não cobre o conteúdo principal.
* [x] Modal de vaga cabe na altura disponível.
* [x] Textarea ocupa largura confortável.
* [x] Cards com textos longos não estouram.
* [x] Tags quebram linha sem cortar conteúdo.
* [x] Botões mantêm área de toque confortável.
* [ ] Loading, erro, vazio e sucesso são visualmente distintos.
* [x] Fundo de labirinto e pellets não prejudica a leitura.

## Acessibilidade

* [x] Navegar por botões, campos e modais usando apenas teclado.
* [x] Confirmar foco visível em todos os elementos interativos.
* [x] Confirmar que os status possuem texto e não dependem apenas de cor.
* [x] Confirmar labels e `aria-label` nos botões de copiar e fechar.
* [x] Confirmar leitura confortável dos textos principais.
* [x] Confirmar contraste de texto normal de pelo menos 4.5:1.
* [x] Confirmar contraste de bordas e elementos importantes de pelo menos 3:1.
* [x] Ativar redução de movimento no sistema e confirmar ausência de animações excessivas.

## Performance

* [x] Confirmar que ChatTerminal é carregado sob demanda.
* [x] Registrar o tamanho do bundle principal após o build.
* [x] Confirmar que nenhuma dependência pesada foi adicionada.

Bundle principal registrado em 2026-06-14: `359,10 kB` (`114,27 kB` gzip).

## Polimento final de responsividade

* [x] Não existe scroll horizontal em `390x844`.
* [x] Não existe scroll horizontal em `360x800`.
* [x] Sidebar vira layout compacto em mobile.
* [x] Header não sobrepõe botões em mobile.
* [x] Pipeline vira lista vertical em mobile.
* [x] Cards da pipeline não cortam texto.
* [x] Tags longas quebram linha.
* [x] Modal de vaga cabe na tela.
* [x] Chat/input não cobre conteúdo.
* [x] Botões principais têm área de toque confortável.
* [x] Fundo arcade não prejudica leitura no mobile.
* [x] Foco por teclado continua visível.

## Estabilização responsiva do frontend

Validação executada em Chrome em 2026-06-14, com sidebar aberta e fechada quando aplicável.

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

Resoluções validadas:

* [x] `1440x900`
* [x] `1366x768`
* [x] `1280x720`
* [x] `1024x768`
* [x] `900x720`
* [x] `768x1024`
* [x] `390x844`
* [x] `360x800`

## Rodada final de QA visual e acessibilidade

Validação executada em 2026-06-14 sem alterações de backend, agentes ou PDI.

Navegadores e viewports desta rodada:

* [x] Google Chrome `149.0.7827.114` em `1366x768` e `390x844`.
* [x] Microsoft Edge `149.0.4022.69` em `1366x768` e `390x844`.

Evidências validadas:

* [x] Sem overflow horizontal nos dois navegadores e nos dois viewports.
* [x] `skill-tag`, `profile-tag` e `status-badge` contêm texto extremo sem espaços.
* [x] Controles touch visíveis possuem área mínima de `44x44` CSS px.
* [x] Botões principais desktop possuem altura mínima de `40` CSS px.
* [x] Foco por teclado usa contorno sólido e halo visível.
* [x] Modal de vaga mantém o foco interno, fecha com `Escape` e devolve o foco ao gatilho.
* [x] Status da pipeline combinam ícone e texto, sem depender apenas de cor.
* [x] Tokens de texto principal, secundário, muted e ghost atingem pelo menos `4.5:1` nos fundos usados.
* [x] Foco ciano e elementos importantes atingem pelo menos `3:1`.
* [x] `prefers-reduced-motion: reduce` reduz animações e transições CSS a uma única iteração mínima.
* [x] Framer Motion respeita a preferência do usuário por meio de `MotionConfig`.
* [x] `npm run lint` passa.
* [x] `npm run build` passa.

## Rodada final de QA funcional

Validação executada em 2026-06-14 com o backend real disponível em `http://127.0.0.1:8000`.

Navegadores desta rodada:

* [x] Google Chrome `149.0.7827.114` em `1366x768`.
* [x] Microsoft Edge `149.0.4022.69` em `1366x768`.

Fluxos e evidências validados nos dois navegadores:

* [x] Sidebar, logo clicável, navegação lateral e pipeline continuam funcionando.
* [x] Upload e análise de currículo TXT concluídos com estado de sucesso.
* [x] Análise de vaga real concluída com cards, tags, requisitos e alertas.
* [x] Match concluído com score, evidências e lacunas.
* [x] Sugestões seguras geradas e seção copiada com confirmação “Copiado”.
* [x] Chat envia a mensagem, recebe resposta do Maestro e mantém o input utilizável.
* [x] Modal de vaga abre, rola internamente e mantém os botões acessíveis.
* [x] Relatórios reais renderizam 37 cards visíveis e 97 tags no pico do fluxo.
* [x] Parágrafos, listas Markdown extensas e token extremo sem espaços não causam overflow.
* [x] Nenhuma etapa auditada gerou overflow horizontal no documento, modal ou cards.
* [x] Backend permaneceu saudável e não houve erro HTTP nem exceção de navegador.
* [x] Chrome e Edge concluíram o fluxo principal completo.

Problema corrigido:

* [x] Botão de copiar usa fallback quando a Clipboard API está exposta, mas rejeita a escrita.

Pendências não validadas nesta rodada:

* [ ] Executar todos os fluxos de erro com backend disponível e indisponível.
* [ ] Confirmar separadamente a atualização do perfil após o upload do currículo.
* [ ] Revalidar quiz e painel de candidaturas em uma rodada dedicada.
