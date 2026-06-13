# Checklist de QA do frontend

Este roteiro cobre a identidade Career Arcade Pipeline e a regressão dos fluxos já existentes.

## Fluxo feliz

* [ ] Abrir a aplicação e confirmar que a pipeline mostra Currículo, Vaga, Match, Sugestões, PDI e Entrevista.
* [ ] Enviar um currículo PDF, DOCX ou TXT válido.
* [ ] Confirmar o estado de sucesso do currículo e a atualização do perfil.
* [ ] Colar uma descrição completa de vaga.
* [ ] Confirmar cards de resumo, palavras-chave, requisitos e alertas.
* [ ] Comparar a vaga com o currículo.
* [ ] Confirmar score, evidências fortes, parciais e ausentes.
* [ ] Gerar sugestões seguras de currículo.
* [ ] Copiar uma seção e confirmar a troca temporária do texto para “Copiado”.
* [ ] Confirmar que PDI aparece apenas como fase futura, sem ação ativa.

## Fluxos de erro

* [ ] Tentar analisar uma vaga com menos de 40 caracteres.
* [ ] Tentar comparar sem currículo analisado.
* [ ] Tentar comparar sem vaga válida.
* [ ] Tentar gerar sugestões sem relatório de match.
* [ ] Parar o backend e confirmar uma mensagem amigável no frontend.
* [ ] Simular arquivo ausente ou inválido e confirmar que a aplicação não quebra.
* [ ] Reconectar o backend e confirmar que o chat recupera o estado de conexão.

## Regressão

* [ ] O chat continua enviando e recebendo mensagens por WebSocket.
* [ ] O ProfilePanel continua carregando o perfil.
* [ ] O quiz continua abrindo e recebendo respostas.
* [ ] O upload de currículo continua funcionando.
* [ ] A análise de vaga continua salvando o resultado.
* [ ] O match continua funcionando.
* [ ] As sugestões seguras continuam funcionando.
* [ ] O painel de candidaturas continua abrindo.
* [ ] As rotas de leitura continuam funcionando.

## Visual

* [ ] Desktop grande: pipeline em seis colunas, sem sobreposição.
* [ ] Notebook: pipeline em duas linhas de três etapas.
* [ ] Tablet: pipeline em duas colunas.
* [ ] Mobile: pipeline vertical com rolagem interna.
* [ ] Sidebar não cobre o conteúdo principal.
* [ ] Modal de vaga cabe na altura disponível.
* [ ] Textarea ocupa largura confortável.
* [ ] Cards com textos longos não estouram.
* [ ] Tags quebram linha sem cortar conteúdo.
* [ ] Botões mantêm área de toque confortável.
* [ ] Loading, erro, vazio e sucesso são visualmente distintos.
* [ ] Fundo de labirinto e pellets não prejudica a leitura.

## Acessibilidade

* [ ] Navegar por botões, campos e modais usando apenas teclado.
* [ ] Confirmar foco visível em todos os elementos interativos.
* [ ] Confirmar que os status possuem texto e não dependem apenas de cor.
* [ ] Confirmar labels e `aria-label` nos botões de copiar e fechar.
* [ ] Confirmar leitura confortável dos textos principais.
* [ ] Confirmar contraste de texto normal de pelo menos 4.5:1.
* [ ] Confirmar contraste de bordas e elementos importantes de pelo menos 3:1.
* [ ] Ativar redução de movimento no sistema e confirmar ausência de animações excessivas.

## Performance

* [ ] Confirmar que ChatTerminal é carregado sob demanda.
* [ ] Registrar o tamanho do bundle principal após o build.
* [ ] Confirmar que nenhuma dependência pesada foi adicionada.
