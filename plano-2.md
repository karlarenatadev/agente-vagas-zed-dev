# Scout — Agente de Busca de Vagas

## Visão Geral

Sistema multi-agente que auxilia usuários em sua jornada de desenvolvimento de carreira, combinando busca de empregos, identificação de lacunas de habilidades, recomendações de cursos e simulação de entrevistas.

**Objetivo**: Opção A do menu funciona. Agente busca vagas via Firecrawl, mostra resultados com correspondência de habilidades.

## Pré-requisitos

- Firecrawl instalado e configurado (`FIRECRAWL_API_KEY` definida)

## Diretrizes para Modelos MoE

Todas as personas e skills são projetadas para modelos Mixture of Experts (MoE). Siga estas regras:

- Sem instruções ambíguas. Cada passo deve especificar exatamente o que fazer, qual ferramenta usar e qual formato de saída produzir.
- Sem tabelas markdown em nenhuma saída. Use listas numeradas com pares chave-valor para dados estruturados.
- Todos os caminhos de arquivo devem ser relativos à raiz do projeto com prefixo explícito `data/`. A raiz do projeto é o diretório `recoloca-ia/`.
- Se uma ferramenta falhar, o agente deve relatar a falha no campo `erros` e não continuar silenciosamente.
- Nunca invente dados. Se um `firecrawl search` ou `firecrawl scrape` falhar, reporte o erro exato e pare. **Exceção**: Em `skills/course-analysis.md`, se a busca falhar para uma habilidade específica, tente o fallback; se o fallback também falhar, pule essa habilidade e continue com as restantes.
- O agente NÃO deve escrever scripts Python, scripts de shell ou qualquer código para implementar personas. O agente personifica cada papel diretamente através do seu comportamento e respostas conversacionais. Personas são instruções comportamentais, não código a ser gerado.

## Arquitetura

```mermaid
graph TD
    A[Usuário] --> B(Maestro - Orquestrador);
    B --> C{Agentes Especializados};
    C -->|Scout (Busca de Vagas)| D(Scout Agent);
    C -->|Curator (Busca de Cursos)| E(Agent Curator);
    C -->|Coach (Simulação de Entrevistas)| F(Agent Coach);
    B -- Interage com --> A;
    B -- Delega Tarefas --> C;
    C -- Retorna Resultados --> B;
```

**Escopo**: Implementar o bloco Scout e conectá-lo ao Maestro.

## Estrutura de Diretórios

```
recoloca-ia/
├── AGENTS.md                   # (existente)
├── personas/
│   ├── maestro.md          # (existente)
│   └── scout.md            # NOVO: Agente de busca de vagas
├── skills/
│   ├── firecrawl.md        # (existente)
│   ├── dispatch.md         # (existente)
│   └── job-search.md       # NOVO: Capacidades de busca de vagas
└── data/
    ├── personality-quiz.md       # (existente)
    ├── user-profile.md           # (existente)
    └── job-search-results.md     # NOVO: Últimos resultados do Scout
```

## Scout - Agente de Busca de Vagas

**Responsabilidade**: Buscar vagas de emprego via Firecrawl, que agrega resultados do Indeed, Catho, LinkedIn, Glassdoor, Infojobs e outras fontes.

**Skills**:
- `skills/job-search.md` — Fluxo completo: comandos firecrawl, leitura de perfil, extração de dados, correspondência de habilidades, filtragem por nível, formato de resposta e tratamento de erros. **OBRIGATÓRIO CARREGAR.**
- `skills/firecrawl.md` — Comandos e regras do CLI Firecrawl.

**Ferramentas do Zed**:
- `terminal` — executar comandos `firecrawl search` e `firecrawl scrape`

**Ferramentas de acesso web**:
- Sempre use `firecrawl search` via `terminal` como seu método primário de acesso à web
- Se o firecrawl falhar consistentemente, você PODE usar `curl` ou `wget` como fallback — note as limitações (sem renderização JS, possíveis bloqueios anti-bot, HTML bruto em vez de markdown limpo)
- Evite `Fetch`, `webfetch` ou outras ferramentas HTTP — prefira firecrawl primeiro, depois curl/wget apenas como recuperação

**Fontes de Dados**:
- Busca Firecrawl (agrega Indeed, Catho, LinkedIn, Glassdoor, Infojobs)

**Entradas**:
- Área de interesse, Localização, Nível de experiência, Habilidades atuais (de `data/user-profile.md`)

**Saídas**:
- Retornar resultados ao Maestro via Response Envelope (Maestro salva em `data/job-search-results.md`)
- Exibir lista de até 5 vagas com título, empresa, localização, link, habilidades correspondentes/em falta e contagem de correspondência

## Skills

### job-search.md

- **Ferramenta Zed**: `terminal` — executar comandos CLI do `firecrawl`
  - **Descoberta de vagas**: `firecrawl search "vagas [area_de_interesse] [localizacao]" --json`
    - Retorna JSON com: url, titulo, descricao, cargo para cada resultado
  - **Detalhes completos da vaga**: `firecrawl scrape <url> --format markdown`
    - Usar em URLs individuais de vagas dos resultados da busca para obter descrição e requisitos completos
    - Se a extração falhar ou expirar, usar o título e descrição do resultado da busca
- Se a busca não retornar resultados, reportar ao usuário e sugerir ampliar os termos de busca
- Para cada vaga encontrada, extrair: título, empresa (da URL ou título), localização, link, habilidades requeridas
- Comparar habilidades requeridas com as habilidades atuais do usuário usando correspondência de strings sem distinção de maiúsculas/minúsculas
- Se a vaga menciona um nível de experiência, preferir vagas que correspondam ao nível do usuário (Júnior, Pleno, Sênior). Se não houver vagas do nível correspondente nos primeiros resultados, expandir a busca e incluir vagas de nível adjacente anotando a discrepância.
- Contar correspondências e listar habilidades em falta
- Retornar até 5 vagas

## Protocolo de Handoff do Scout

**Contexto passado:** área de interesse e localização do usuário do user-profile.md

**Envelope de Despacho** (construído pelo Maestro):

```
## DESPACHO: SCOUT
### referencia_persona
[Conteúdo completo de personas/scout.md]

### tarefa
Buscar vagas de emprego para [area] em [localizacao]

### perfil_usuario
[Conteúdo de data/user-profile.md]

### contexto
Area: [area_de_interesse]
Localizacao: [localizacao]
Nivel: [nivel_de_experiencia]
Habilidades: [lista_de_habilidades]

### saida_esperada
Envelope de resposta com estado, resumo, dados (lista de vagas) e erros se houver
```

**Formato de dados da resposta:**
```
1. titulo: [título da vaga]
   empresa: [nome da empresa]
   localizacao: [cidade ou Remoto]
   link: [URL]
   habilidades_correspondentes: [habilidade1, habilidade2]
   habilidades_faltantes: [habilidade3, habilidade4]
   contagem_correspondencia: [X de Y habilidades correspondem]

2. [próxima vaga no mesmo formato]
```

## Esquemas dos Arquivos de Dados

### data/job-search-results.md

Armazena os resultados mais recentes do Scout para uso pelo Curator e Coach:

```
Data da Busca: [AAAA-MM-DD HH:MM]
Parâmetros de Busca:
  Área: [valor]
  Localização: [valor]

Resultados:
1. titulo: [título da vaga]
   empresa: [nome da empresa]
   localizacao: [cidade ou Remoto]
   link: [URL]
   habilidades_correspondentes: [habilidade1, habilidade2]
   habilidades_faltantes: [habilidade3, habilidade4]
   contagem_correspondencia: [X de Y habilidades correspondem]

2. titulo: [próximo título de vaga]
   ...
```

## Tasks

### 1. Escrever `skills/job-search.md`

Contendo:
- Comandos firecrawl para busca de vagas
- Como analisar resultados JSON
- Como corresponder habilidades do usuário com requisitos da vaga
- Regras de filtragem por nível de experiência
- Formato de resposta esperado
- Tratamento de erros

### 2. Escrever `personas/scout.md`

Contendo:
- Papel e responsabilidade do Scout
- Ferramentas disponíveis (terminal com firecrawl)
- Referência obrigatória à skill `skills/job-search.md`
- Referência à skill `skills/firecrawl.md` (existente)
- Formato do Response Envelope
- Regras de tratamento de erros

### 3. Conectar `spawn_agent` no Maestro para despachar o Scout

- Quando o usuário digitar "A", o Maestro deve construir o envelope de despacho
- Chamar `spawn_agent` com o prompt de despacho
- Analisar a resposta do Scout
- Salvar resultados em `data/job-search-results.md`
- Exibir vagas ao usuário
- Retornar ao menu

### 4. Testar: busca de vagas funcional

- Usuário seleciona A
- Scout busca via Firecrawl
- Resultados exibidos com habilidades correspondentes/em falta

### 5. Testar: tratamento de erro

- Se a busca falhar, o erro é reportado ao usuário
- Agente retorna ao menu

## Fluxo

```mermaid
graph TD
    A[Usuário seleciona A no menu] --> B(Maestro constrói envelope de despacho para Scout);
    B --> C(spawn_agent dispara Scout com persona + contexto);
    C --> D(Scout executa firecrawl search → firecrawl scrape nas URLs);
    D --> E(Scout corresponde habilidades com user-profile.md);
    E --> F(Scout retorna envelope de resposta com até 5 vagas);
    F --> G(Maestro salva em data/job-search-results.md → exibe ao usuário → retorna ao menu);
```

## Regras de Erro

- Se `firecrawl search` falhar, reportar o erro ao usuário e retornar ao menu.
- Se `firecrawl scrape` falhar em uma URL específica, usar o título/descrição do resultado da busca e anotar que a extração falhou.
- Se `spawn_agent` falhar, dizer ao usuário o que deu errado e retornar ao menu.
- Se a busca retornar resultados mas algumas extrações falharem, mostrar resultados parciais com detalhes completos onde disponíveis.

## Entregável

Scout totalmente funcional, busca de vagas end-to-end a partir do menu.
