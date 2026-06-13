# Roadmap — Evolução do Import Vagas

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
* [x] Tratamento de erros.
* [x] Manutenção do estado da sessão.

### O que iremos acrescentar

* [ ] Roteamento para análise de descrição de vaga.
* [ ] Roteamento para comparação vaga x currículo.
* [ ] Roteamento para sugestões seguras de currículo.
* [ ] Roteamento para geração de PDI por vaga.
* [ ] Roteamento para entrevista baseada em uma vaga específica.
* [ ] Etapa de reconciliação entre perfil, currículo e vaga.
* [ ] Mensagens mais claras quando houver conflito entre dados do usuário.

---

## 1.3 Scout

O Scout é o agente responsável por oportunidades e análise de vagas.

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

### O que iremos acrescentar

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
* [ ] Comparar a descrição da vaga com o currículo analisado.
* [ ] Separar evidências fortes, evidências parciais e requisitos ausentes.
* [ ] Gerar score de aderência entre vaga e currículo.
* [ ] Gerar relatório em `data/resume-match-report.md`.

---

## 1.4 Curator

O Curator é o agente responsável por trilhas de aprendizado.

### O que temos

* [x] Normalização de lacunas detectadas pelo Scout.
* [x] Priorização de habilidades faltantes.
* [x] Recomendações gratuitas.
* [x] Recomendações com referências oficiais.
* [x] Sugestão de cursos pagos quando fizer sentido.
* [x] Sugestão de projetos práticos.
* [x] Organização entre “estudar agora” e “estudar depois”.
* [x] Base interna de recomendações quando o Firecrawl não está disponível.

### O que iremos acrescentar

* [ ] Gerar PDI personalizado a partir do relatório vaga x currículo.
* [ ] Separar plano por prazo:

  * [ ] 7 dias;
  * [ ] 30 dias;
  * [ ] 60 dias.
* [ ] Classificar lacunas por impacto na candidatura.
* [ ] Indicar quais lacunas impedem candidatura imediata.
* [ ] Indicar quais lacunas podem ser estudadas depois.
* [ ] Sugerir projetos práticos para gerar evidências reais.
* [ ] Sugerir entregáveis para GitHub, LinkedIn e currículo.
* [ ] Salvar o PDI em `data/pdi-plan.md`.

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

* [ ] Comparar currículo com descrição de vaga específica.
* [ ] Identificar palavras-chave da vaga que já aparecem no currículo.
* [ ] Identificar palavras-chave ausentes.
* [ ] Identificar experiências que podem ser melhor destacadas.
* [ ] Identificar informações fracas ou pouco claras.
* [ ] Criar sugestões seguras de melhoria.
* [ ] Criar seção “Não afirmar ainda”.
* [ ] Gerar `data/resume-tailoring-suggestions.md`.

---

## 2.2 Sugestões seguras de currículo

### O que temos

* [x] Base inicial para análise de currículo.
* [x] Dados suficientes para cruzar currículo com vaga futuramente.

### O que iremos acrescentar

* [ ] Sugestão de novo resumo profissional.
* [ ] Sugestão de reorganização da seção de habilidades.
* [ ] Sugestão de projetos a destacar.
* [ ] Sugestão de experiências a reposicionar.
* [ ] Sugestão de palavras-chave para inserir.
* [ ] Separação entre:

  * [ ] pode destacar melhor;
  * [ ] pode reposicionar;
  * [ ] precisa estudar primeiro;
  * [ ] não afirmar ainda.
* [ ] Botão para copiar sugestões.
* [ ] Avisos para evitar exageros ou informações falsas.

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

* [ ] Botão “Comparar com meu currículo”.
* [ ] Integração com `data/resume-analysis.md`.
* [ ] Geração do relatório de aderência.
* [ ] Exibição de score geral.
* [ ] Exibição de palavras-chave encontradas.
* [ ] Exibição de palavras-chave ausentes.
* [ ] Exibição de lacunas críticas.
* [ ] Exibição de sugestões seguras.
* [ ] Exibição da seção “Não afirmar ainda”.

---

# 4. O que iremos acrescentar na esteira de candidatura

## 4.1 Comparação vaga x currículo

### Objetivo

Criar uma etapa que mostre o quanto o currículo do usuário está aderente à vaga analisada.

### O que será acrescentado

* [ ] Criar módulo de comparação entre vaga e currículo.
* [ ] Ler `data/job-description-analysis.md`.
* [ ] Ler `data/resume-analysis.md`.
* [ ] Normalizar aliases de habilidades.
* [ ] Comparar hard skills.
* [ ] Comparar soft skills.
* [ ] Comparar ferramentas.
* [ ] Comparar palavras-chave.
* [ ] Comparar senioridade e área.
* [ ] Separar evidências em:

  * [ ] evidência forte;
  * [ ] evidência parcial;
  * [ ] ausente.
* [ ] Calcular score geral.
* [ ] Gerar nível de prontidão.
* [ ] Gerar recomendações seguras.
* [ ] Gerar alertas.
* [ ] Salvar resultado em `data/resume-match-report.md`.
* [ ] Criar rota `POST /api/resume-match/analyze`.
* [ ] Criar rota `GET /api/data/resume-match`.
* [ ] Criar interface para visualizar o relatório.

---

## 4.2 Relatório de aderência

### Objetivo

Criar um documento simples e claro que explique o quanto o currículo conversa com a vaga.

### O que será acrescentado

* [ ] Score geral de aderência.
* [ ] Nível de prontidão.
* [ ] Evidências fortes.
* [ ] Evidências parciais.
* [ ] Requisitos ausentes.
* [ ] Palavras-chave encontradas.
* [ ] Palavras-chave ausentes.
* [ ] Pontos fortes para a vaga.
* [ ] Lacunas críticas.
* [ ] Sugestões seguras para melhorar o currículo.
* [ ] Seção “Não afirmar ainda”.
* [ ] Próximos passos recomendados.

---

## 4.3 Sugestões de currículo adaptado

### Objetivo

Ajudar o usuário a melhorar o currículo para uma vaga específica sem inventar experiência.

### O que será acrescentado

* [ ] Gerar sugestões para resumo profissional.
* [ ] Gerar sugestões para habilidades.
* [ ] Gerar sugestões para projetos.
* [ ] Gerar sugestões para experiências.
* [ ] Mostrar palavras-chave que podem ser adicionadas com segurança.
* [ ] Mostrar termos que precisam de evidência antes de entrar no currículo.
* [ ] Permitir copiar sugestões.
* [ ] Salvar em `data/resume-tailoring-suggestions.md`.

---

## 4.4 PDI personalizado por vaga

### Objetivo

Transformar as lacunas entre vaga e currículo em plano de desenvolvimento individual.

### O que será acrescentado

* [ ] Gerar PDI com base no `resume-match-report.md`.
* [ ] Separar lacunas por prioridade.
* [ ] Criar plano de 7 dias.
* [ ] Criar plano de 30 dias.
* [ ] Criar plano de 60 dias.
* [ ] Sugerir estudos gratuitos.
* [ ] Sugerir documentação oficial.
* [ ] Sugerir cursos pagos apenas quando fizer sentido.
* [ ] Sugerir projetos práticos.
* [ ] Sugerir entregáveis para portfólio.
* [ ] Sugerir ajustes futuros no currículo.
* [ ] Salvar em `data/pdi-plan.md`.

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
* [ ] Detectar conflito entre currículo e vaga.
* [ ] Detectar conflito entre perfil e vaga.
* [ ] Permitir escolher foco da candidatura.
* [ ] Permitir usar dados do currículo como base.
* [ ] Permitir usar dados do perfil como base.
* [ ] Permitir usar a vaga como foco principal.
* [ ] Atualizar perfil somente com confirmação do usuário.
* [ ] Normalizar habilidades antes de qualquer cálculo de aderência.

---

# 6. Dados reais com Firecrawl

## O que temos

* [x] Estrutura prevista para uso do Firecrawl.
* [x] Fallback local quando Firecrawl não retorna resultados.
* [x] Busca simulada funcionando.
* [x] Recomendações internas funcionando.

## O que iremos acrescentar

* [ ] Instalar Firecrawl CLI.
* [ ] Configurar `FIRECRAWL_API_KEY`.
* [ ] Testar busca real de vagas.
* [ ] Testar busca real de cursos.
* [ ] Validar links retornados.
* [ ] Validar salários.
* [ ] Validar requisitos extraídos.
* [ ] Registrar origem dos dados.
* [ ] Tratar resultados parciais.
* [ ] Tratar ausência de resultados reais sem quebrar o fluxo.

---

# 7. Testes e validação

## O que temos

* [x] Validação manual de build.
* [x] Validação manual de lint.
* [x] Validação manual do backend.
* [x] Teste integrado da análise de descrição de vaga.
* [x] Tratamento de entrada inválida na análise de vaga.

## O que iremos acrescentar

### Backend

* [ ] Testar análise de descrição de vaga.
* [ ] Testar comparação vaga x currículo.
* [ ] Testar ausência de currículo.
* [ ] Testar ausência de vaga.
* [ ] Testar geração de Markdown.
* [ ] Testar normalização de aliases.
* [ ] Testar cálculo de score.

### Frontend

* [ ] Testar renderização do analisador de vaga.
* [ ] Testar botão de comparação com currículo.
* [ ] Testar loading.
* [ ] Testar mensagens de erro.
* [ ] Testar renderização de tags.
* [ ] Testar responsividade básica.

### Fluxo completo

* [ ] Enviar currículo.
* [ ] Analisar currículo.
* [ ] Colar descrição da vaga.
* [ ] Analisar vaga.
* [ ] Comparar vaga com currículo.
* [ ] Gerar relatório de aderência.
* [ ] Gerar sugestões seguras.
* [ ] Gerar PDI.
* [ ] Iniciar entrevista baseada na vaga.

---

# 8. Performance e organização

## O que temos

* [x] Build funcionando.
* [x] Interface responsiva.
* [x] Componentes carregados sob demanda.
* [x] Aviso de bundle principal acima de 500 kB.

## O que iremos acrescentar

* [ ] Investigar bundle principal.
* [ ] Aplicar lazy loading em componentes grandes.
* [ ] Separar melhor os componentes da esteira de candidatura.
* [ ] Evitar duplicação de tipos TypeScript.
* [ ] Revisar CSS adicionado.
* [ ] Garantir consistência visual entre módulos.
* [ ] Revisar nomes de arquivos e responsabilidades.

---

# 9. Documentação

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

---

# 10. Ordem prática de evolução

## Etapa atual

* [x] Corrigir lint do ProfilePanel.
* [x] Criar análise de descrição de vaga.
* [x] Criar rota de análise de vaga.
* [x] Criar interface para colar descrição.
* [x] Salvar análise em Markdown.

## Próxima etapa

* [ ] Criar comparação vaga x currículo.
* [ ] Gerar `resume-match-report.md`.
* [ ] Exibir relatório no frontend.
* [ ] Tratar ausência de currículo ou vaga.
* [ ] Validar lint, build e backend.

## Etapas seguintes

* [ ] Gerar sugestões seguras de currículo.
* [ ] Gerar PDI personalizado por vaga.
* [ ] Conectar Coach à vaga analisada.
* [ ] Resolver divergência entre perfil, currículo e vaga.
* [ ] Configurar dados reais com Firecrawl.
* [ ] Criar testes mínimos.
* [ ] Atualizar documentação.

---

# 11. Definição de pronto

Uma etapa só deve ser considerada pronta quando:

* [ ] A funcionalidade aparece no frontend.
* [ ] A rota backend responde corretamente.
* [ ] O arquivo Markdown correspondente é gerado.
* [ ] Os erros comuns são tratados.
* [ ] O lint passa.
* [ ] O build passa.
* [ ] O backend importa ou compila corretamente.
* [ ] Existe uma forma clara de testar manualmente.
* [ ] Nenhum fluxo anterior foi quebrado.
* [ ] A documentação foi atualizada quando necessário.
