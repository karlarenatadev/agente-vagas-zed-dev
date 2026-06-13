# Relatório de andamento do projeto

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
