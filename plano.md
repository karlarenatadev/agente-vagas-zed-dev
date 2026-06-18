# Plano: Orquestrador Multi-Agente (MoE) - Maestro 

## Atualizacao de Roadmap Tecnico (2026-06-17)

O backend passou por uma etapa de hardening e agora opera com contratos mais proximos de producao:

* [x] Logging estruturado centralizado em `backend/logging_config.py`.
* [x] Tratamento global de excecoes no FastAPI para respostas JSON seguras.
* [x] Falhas de LLM e provedores externos encapsuladas em erros de dominio controlados.
* [x] Persistencia local protegida por locks, escrita atomica e I/O delegado para thread quando necessario.
* [x] Sessoes isoladas por `session_id`, com estado do WebSocket salvo em `data/sessions/{id}/chat_state.json`.
* [x] Firecrawl migrado de CLI/subprocess para SDK oficial `firecrawl-py`.
* [x] Upload de curriculos endurecido com limite de tamanho e Magic Numbers.
* [x] Suite atual: 73 testes passando, incluindo stress test de 50 escritas concorrentes.

Proximos marcos arquiteturais:

* [ ] Frontend consumir os contratos padronizados de erro 422/500 com toasts ou banners amigaveis.
* [ ] Frontend refletir visualmente a recuperacao de estado do WebSocket apos reconexao.
* [ ] Dockerizar backend e frontend.
* [ ] Criar GitHub Actions com pipeline bloqueante para testes de contrato e concorrencia.
## Visão Geral 

Este plano detalha a implementação do Maestro, o orquestrador central de um Sistema Multi-Agente baseado em Mixture of Experts (MoE), projetado para auxiliar usuários em sua jornada de desenvolvimento de carreira. O sistema combina busca de empregos, identificação de lacunas de habilidades, recomendações de cursos e simulação de entrevistas. O Maestro é responsável por saudar o usuário, conduzir o quiz de perfil, gerenciar o estado do usuário e apresentar o menu de opções, delegando tarefas a agentes especializados. 

## Arquitetura MoE 

O sistema adota uma arquitetura Mixture of Experts (MoE), onde cada agente (ou "expert") é especializado em uma tarefa específica. O Maestro atua como o orquestrador principal, coordenando a interação entre os agentes e o usuário. 

```mermaid graph 
TD A[Usuário] --> B(Maestro - Orquestrador); B --> C{Agentes Especializados}; C -->|Scout (Busca de Vagas)| D(import_vagas); C -->|Curator (Busca de Cursos)| E(Agent Curator); C -->|Coach (Simulação de Entrevistas)| F(Agent Coach); B -- Interage com --> A; B -- Delega Tarefas --> C; C -- Retorna Resultados --> B; 

``` 

### Agentes Especializados (Visão Geral) 
* **Maestro**: Orquestrador principal. Interface com o usuário, gerencia o quiz e o perfil, apresenta o menu e despacha tarefas. 
* **Scout (`import_vagas`)**: Focado exclusivamente em minerar vagas de tecnologia para os níveis de senioridade Estágio e Júnior. 
* **Curator**: Especializado em identificar e recomendar cursos para preencher lacunas de habilidades. 
* **Coach**: Focado em simulações de entrevistas. 

## Estrutura de Diretórios A arquitetura MoE segue uma estrutura de diretórios organizada: 

``` 

import-vagas/ ├── AGENTS.md

 # Instruções de inicialização para o agente Maestro
 ├── personas/ │ └── maestro.md 
 
 # Persona detalhada do Maestro ├── skills/ │ └── dispatch.md 
 
 # Protocolo de despacho e handoff de agentes 
 └── data/ 
    ├── personality-quiz.md 
 
 # Template para respostas do quiz do usuário └── user-profile.md
 
 # Template para o perfil consolidado do usuário 
 ```
 
## Persona do Maestro
O Maestro adota uma estética "digital soft dark" de terminal de dados. Suas respostas são limpas, organizadas e silenciosas. Apesar de objetivo, utiliza os princípios da Comunicação Não-Violenta (CNV) para ser acolhedor, evitando gerar atrito ou ansiedade no usuário. 
 
 ## Protocolo de Despacho (`skills/dispatch.md`)
 
O Maestro utiliza o protocolo definido em `skills/dispatch.md` para interagir com outros agentes. Este protocolo inclui: 

 * **Tabela de Roteamento**: Mapeia intenções do usuário para agentes específicos (ex: A -> `import_vagas`, B -> Curator, C -> Coach, D -> Maestro (quiz)). 
 * **Formato de Envelope de Despacho**: Estrutura de prompt para `spawn_agent`, contendo persona, tarefa, perfil do usuário, contexto e formato de saída esperado. 
 * **Formato de Envelope de Resposta**: Estrutura esperada para a resposta de um agente despachado (estado, resumo, dados, erros). 
 * **Especificações de Handoff**: Detalhes sobre como passar informações entre agentes. 
 * **Regras de Tratamento de Erros**: Procedimentos a serem seguidos caso uma ferramenta ou agente falhe. 
 
 ## Fluxo de Interação do Maestro 
 
 1. **Inicialização**: 

 * O Maestro saúda o usuário com um tom acolhedor e objetivo, seguindo os princípios da CNV e a estética "digital soft dark". 
 * Verifica a existência e o status de conclusão do arquivo `data/personality-quiz.md` usando `find_path`. 
 * **Se o quiz estiver incompleto**: Pergunta ao usuário se deseja continuar de onde parou (se houver dados parciais) ou recomeçar. Guia o usuário pelas 5 perguntas do quiz, uma por vez, e salva as respostas em `data/personality-quiz.md`. 
 * **Se o quiz estiver completo**: Carrega o perfil existente de `data/user-profile.md`. 
 * Gera ou atualiza `data/user-profile.md` com base nas respostas do quiz. 
 
 2. **Apresentação do Menu**: * Exibe o menu de opções ao usuário: 

 * A — Executar `import_vagas` (Indeed, Catho, LinkedIn, Glassdoor, Infojobs) - *Funcionalidade em construção*. 
 * B — Encontrar cursos e materiais (Premium e Gratuitos) para preencher lacunas de habilidades (Curator). 
 * C — Praticar com uma entrevista simulada. 
 * D — Refazer o quiz (para atualizar seu perfil). 
 
 3. **Processamento da Seleção do Usuário**: 
 
 * Recebe a seleção do usuário (A, B, C, D). 
 * **Se a entrada for válida**: Delega a tarefa ao agente apropriado usando `spawn_agent` com o prompt estruturado de `skills/dispatch.md`. 
 * **Se a entrada for inválida (Regra de Fallback)**: Redireciona educadamente o usuário de volta ao menu principal. 
 * Exemplo: "Desculpe, não entendi sua solicitação. Por favor, escolha uma das opções do menu: A, B, C ou D." 
 
 4. **Exibição de Resultados**: * Apresenta a resposta do agente despachado ao usuário de forma limpa e organizada.
 
 5. **Loop**: Exibe o menu novamente para o usuário. 
 
 ## Perguntas do Quiz (Perfil de Busca)
 
 As seguintes perguntas são feitas sequencialmente para montar o Perfil de Busca do usuário: 
 
 1. "Qual área de interesse principal em tecnologia? Opções: Frontend, Backend, Ciência de Dados, Mobile, DevOps, Full Stack, Governança de Dados, Design UX, Design UI, Liderança, RH, Marketing de Mídias Sociais, Growth Marketing, Gestão de Produtos ou Cibersegurança." 
 2. "Como você descreveria seu nível de experiência atual? Opções: Júnior, Pleno ou Sênior." 
 3. "Como você prefere trabalhar? Opções: Remoto, Híbrido ou Presencial." 
 4. "Onde você está localizado? Me diga sua cidade e estado, ou apenas diga \'Remoto\'." 
 5. "Quais são suas soft skills mais fortes? Pense em coisas como comunicação, trabalho em equipe, liderança, resolução de problemas — o que vier naturalmente para você." 
 6. "Onde você se vê em sua carreira? Opções: Crescimento técnico, Transição de carreira, Primeiro emprego ou Trilha de liderança." 
 7. "Quais habilidades técnicas você já tem? Apenas liste separadas por vírgulas — por exemplo: Python, SQL, Excel, Figma, Git." 
 
 ## Esquemas dos Arquivos de Dados 
 
 ### `data/personality-quiz.md` 
 
 ```markdown
  Área de interesse: [valor] Nível de experiência: [valor] Preferências de trabalho: [valor] Localização: [valor] Soft skills: [valor] Objetivo de carreira: [valor] Habilidades atuais: [valor] Concluído: [true | false] 
 ``` 
 ### `data/user-profile.md` 
 
 ```markdown 
 Área de interesse: [valor] Nível de experiência: [valor] Preferências de trabalho: [valor] Localização: [valor] Soft skills: [valor] Objetivo de carreira: [valor] Habilidades atuais: [valor] Funções alvo: [lista separada por vírgulas] Concluído: [true | false] 
 ``` 
 
 *Nota: O mapeamento de "Funções alvo" será gerado pelo Maestro com base nas respostas do quiz, seguindo um conjunto predefinido de 45 combinações.* 
 
 ## Notas Técnicas 
 
 * **Orquestração**: Executada dentro do editor Zed usando `spawn_agent` para despacho de sub-agentes. 
 
 * **Armazenamento de Estado**: Todos os dados são mantidos em arquivos Markdown sob o diretório `data/`.
 
 * **Simplicidade**: Sem cache, sem IDs de sessão complexos. Cada agente realiza uma tarefa específica e retorna seus resultados diretamente.
 
 * **Sem Geração de Código**: Agentes personificam seus papéis através de comportamento conversacional e uso de ferramentas, não gerando scripts ou código executável.