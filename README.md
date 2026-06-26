<div align="center">

# import vagas

**Plataforma de desenvolvimento de carreira com IA multi-agente**

Encontre vagas alinhadas ao seu perfil, descubra o que aprender e pratique entrevistas — tudo em uma conversa.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/Licença-MIT-8B5CF6?style=flat-square)](LICENSE)

</div>

---

## O que é

**import vagas** é um sistema multi-agente de desenvolvimento de carreira que combina busca inteligente de empregos, recomendação de cursos e simulação de entrevistas em uma interface conversacional.

O sistema é orquestrado pelo **Maestro**, que coordena três agentes especializados:

| Agente | Papel | Como funciona |
|--------|-------|---------------|
| **Scout** | Busca de vagas | Pesquisa vagas via Firecrawl SDK oficial, extrai requisitos e calcula o match com suas habilidades. Quando o Firecrawl não retorna nada ou está sem créditos, sugere vagas com o LLM disponível (marcadas como "Sugerida por IA", não verificadas); a simulação determinística fica como último recurso |
| **Curator** | Trilha de aprendizado | Para cada habilidade que falta, prioriza materiais gratuitos, videos, documentacao oficial e cursos pagos acessiveis; premium entra apenas quando for relevante |
| **Coach** | Entrevista simulada | Conduz 5 perguntas técnicas e comportamentais com feedback em tempo real e pontuação final; quando há vaga analisada e relatório de aderência, calibra as perguntas pela vaga e pelas lacunas do match |

---

## Funcionalidades

Além da busca de vagas, cursos e entrevista, a plataforma cobre o ciclo completo de candidatura:

- **Diagnóstico de perfil** — quiz de 7 perguntas (área, nível, localização, preferências, soft skills, objetivo, habilidades).
- **Currículo → quiz automático** — envie um currículo em **PDF, DOCX ou TXT** e o sistema extrai área, nível, habilidades e soft skills, **pré-preenchendo o quiz** e perguntando só o que falta.
- **Filtro de recência das vagas** — escolha **24h, 7 dias, 1 mês ou todas**; o Scout aplica o parametro `tbs` do Firecrawl na busca.
- **Análise de descrição de vaga** — cole o anúncio e receba requisitos, hard/soft skills, ferramentas e alertas estruturados.
- **Match currículo × vaga** — relatório de aderência com score, evidências fortes/parciais e lacunas.
- **Sugestões de currículo** — ajustes seguros (sem inventar experiência) para a vaga analisada.
- **PDI** — plano de desenvolvimento individual de 7, 30 e 60 dias a partir das lacunas.
- **Candidaturas** — tracker para salvar vagas e acompanhar o status (salva, aplicada, entrevista, oferta…).
- **Career Arcade Pipeline** — rota visual de 6 fases (Currículo · Vaga · Match · Sugestões · PDI · Entrevista) que ilumina o próximo passo; recolhível, virando uma barra de progresso futurista.

---

## Demonstração rápida

```
> A

⚔ Scout — Iniciando varredura de vagas...

1. titulo: Cientista de Dados Júnior
   empresa: Nubank
   localizacao: Remoto
   salario: R$ 4.000 - R$ 6.000
   habilidades_correspondentes: Python, SQL, Git
   habilidades_faltantes: Spark, Airflow, dbt
   contagem_correspondencia: 3 de 6 habilidades correspondem
   dica_curriculo: Destaque projetos com Python e SQL — são os requisitos principais

> B

📚 Curator — Buscando trilha de aprendizado...

Habilidade Faltante: Spark
  Gratuito: Apache Spark Tutorial — YouTube (3h)
  Acessivel: Apache Spark com PySpark — Udemy/Alura, quando fizer sentido
```

---

## Arquitetura

```
┌──────────────────────────────────────────────────────────┐
│                   Frontend  (React + TS)                  │
│                                                           │
│   StatusBar · ProfilePanel · ChatTerminal · ChatInput    │
└─────────────────────────┬────────────────────────────────┘
                          │  WebSocket (streaming)
┌─────────────────────────▼────────────────────────────────┐
│                   Backend  (FastAPI)                      │
│                                                           │
│              ┌─────────────────────┐                     │
│              │  Maestro            │                     │
│              │  Orquestrador       │                     │
│              │  · Quiz de perfil   │                     │
│              │  · Menu de opções   │                     │
│              │  · Despacho         │                     │
│              └──────┬──────┬───────┘                     │
│                     │      │      │                      │
│              ┌──────▼─┐ ┌──▼────┐ ┌▼──────┐             │
│              │ Scout  │ │Curator│ │ Coach │             │
│              └──────┬─┘ └──┬────┘ └───────┘             │
│                     └──────┘                             │
│                        │  Firecrawl SDK                  │
└────────────────────────┼─────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │    data/  (estado)  │
              │  personality-quiz   │
              │  user-profile       │
              │  job-search-results │
              │  course-recs        │
              │  interview-session  │
              └─────────────────────┘
```

O estado da sessão é persistido em arquivos Markdown dentro de `data/`. Sem banco de dados, sem sessões complexas — cada arquivo é legível e editável diretamente.

---

## Estrutura do projeto

```
import-vagas/
│
├── backend/
│   ├── agents/
│   │   ├── base.py        # Classe base com streaming LLM
│   │   ├── maestro.py     # Orquestrador principal
│   │   ├── scout.py       # Busca de vagas
│   │   ├── curator.py     # Recomendação de cursos
│   │   └── coach.py       # Entrevista simulada
│   ├── routers/
│   │   ├── chat.py             # WebSocket com protocolo de estado (+ date_filter)
│   │   ├── profile.py          # REST: perfil do usuário
│   │   ├── resume.py           # REST: upload e análise de currículo (PDF/DOCX/TXT)
│   │   ├── job_description.py  # REST: análise de descrição de vaga
│   │   ├── resume_match.py     # REST: match currículo × vaga
│   │   ├── resume_tailoring.py # REST: sugestões seguras de currículo
│   │   ├── pdi.py              # REST: plano de desenvolvimento individual
│   │   ├── applications.py     # REST: tracker de candidaturas
│   │   └── data_files.py       # REST: vagas, cursos, entrevista, análises
│   ├── main.py            # FastAPI app
│   ├── config.py          # Configurações e paths (.env por caminho absoluto)
│   ├── logging_config.py  # Logging estruturado em JSON
│   ├── session.py         # Paths por sessão, locks e escrita atômica
│   ├── firecrawl_client.py # Cliente seguro do Firecrawl SDK
│   ├── mock_server.py     # Servidor mock para testes sem API key
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── StatusBar.tsx                  # Topbar com status de conexão
│       │   ├── ProfilePanel.tsx               # Sidebar: perfil, nav e filtro de data
│       │   ├── ApplicationPipeline.tsx        # Career Arcade Pipeline (recolhível)
│       │   ├── ChatTerminal.tsx               # Lista de mensagens
│       │   ├── ChatMessage.tsx                # Mensagem individual com markdown
│       │   ├── ChatInput.tsx                  # Input com atalhos de menu
│       │   ├── ScoutReport.tsx                # Cartões de vagas do Scout
│       │   ├── CuratorReport.tsx              # Trilha de aprendizado
│       │   ├── QuizPanel.tsx                  # Quiz de perfil
│       │   ├── ResumeUpload.tsx               # Upload e análise de currículo
│       │   ├── JobDescriptionAnalyzer.tsx     # Análise de descrição de vaga
│       │   ├── ResumeMatchReport.tsx          # Match currículo × vaga
│       │   ├── ResumeTailoringSuggestions.tsx # Sugestões de currículo
│       │   ├── PdiPlan.tsx                     # Plano de desenvolvimento (PDI)
│       │   ├── ApplicationTracker.tsx         # Tracker de candidaturas
│       │   └── AgentBadge.tsx                  # Indicador de agente ativo
│       ├── hooks/
│       │   ├── useWebSocket.ts    # Conexão WebSocket com streaming
│       │   └── useScrollToResult.ts # Scroll automático para resultados gerados
│       ├── types.ts
│       └── App.tsx
│
├── personas/
│   ├── maestro.md   # Comportamento e fluxo do Maestro
│   ├── scout.md     # Comportamento do Scout
│   └── curator.md   # Comportamento do Curator
│
├── skills/
│   ├── dispatch.md        # Protocolo de despacho entre agentes
│   ├── job-search.md      # Fluxo de busca de vagas
│   ├── course-analysis.md # Fluxo de busca de cursos
│   └── firecrawl.md       # Regras de uso do Firecrawl
│
└── data/                  # Estado local (gerado em runtime, *.md ignorado pelo Git)
    ├── README.md           # Único arquivo versionado da pasta
    ├── personality-quiz.md
    ├── user-profile.md
    ├── resume-analysis.md
    ├── job-search-results.md
    ├── job-description-analysis.md
    ├── resume-match-report.md
    ├── resume-tailoring-suggestions.md
    ├── pdi-plan.md
    ├── course-recommendations.md
    └── interview-session.md
```

> **Privacidade:** os arquivos `data/*.md`, `data/applications.json` e `data/sessions/` são estado local por pessoa/sessão e
> podem conter dados sensíveis (currículo, perfil). Eles são ignorados pelo Git —
> apenas `data/README.md` é versionado.
> A pasta `data/` armazena artefatos locais gerados pela aplicação, incluindo currículo,
> vaga, match, sugestões e PDI. Não versione esses arquivos. Variáveis reais devem ficar
> somente em `.env` local ou GitHub Secrets. Este projeto ainda não deve ser usado com
> dados reais sensíveis em produção sem proteção adicional.

---

## Pré-requisitos

- **Python** 3.11+
- **Node.js** 18+
- **OpenAI API Key** — [platform.openai.com](https://platform.openai.com)
- **Firecrawl API Key** — [firecrawl.dev](https://firecrawl.dev)

---

## Instalação e execução

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/import-vagas.git
cd import-vagas
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Edite `.env` com suas chaves:

```env
OPENAI_API_KEY=sk-...
FIRECRAWL_API_KEY=fc-...
```

Inicie o servidor:

```bash
python run.py
# Rodando em http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Rodando em http://localhost:5173
```

---

## Testando sem API keys

Para explorar a interface sem configurar chaves de API, use o servidor mock:

```bash
cd backend
python mock_server.py
# Mock rodando em http://localhost:8000
```

O mock simula todas as respostas dos agentes com dados realistas e streaming token a token, idêntico ao comportamento real.

---

## Rodar com Docker

Para subir tudo com um comando, sem instalar Python ou Node — basta o [Docker](https://docs.docker.com/get-docker/):

```bash
# (opcional) configure as chaves reais
cp backend/.env.example backend/.env   # edite OPENAI_API_KEY e FIRECRAWL_API_KEY

docker compose up --build
```

- **Site (frontend):** <http://localhost:8080>
- **API + docs (backend):** <http://localhost:8000/docs>

O frontend é servido por Nginx, que faz proxy reverso de `/api` e `/ws` para o
backend. Por isso, quem só **acessa** o site precisa apenas do navegador; o
Docker é necessário apenas em quem **roda/hospeda** os containers.

O estado local (perfil, currículo, match, PDI, sessões) é persistido no volume
`backend-data`, sobrevivendo a reinícios. Sem `backend/.env`, o backend sobe em
modo degradado: sem Firecrawl e sem LLM, o Scout cai direto em vagas simuladas;
com uma chave de LLM válida, ele tenta sugerir vagas via IA antes de recorrer à
simulação.

Para explorar sem chaves de API, suba também o mock server e aponte o proxy do
frontend para ele — defina `BACKEND_UPSTREAM=mock:8000` (em um `.env` na raiz do
projeto ou como variável de ambiente) e rode:

```bash
docker compose --profile mock up --build
```

> Requer Docker Compose v2.24+ (sintaxe `env_file.required`).

---

## Fluxo de uso

```
1. Perfil
   ├── Envie um currículo (PDF/DOCX/TXT) — opcional
   │   e o sistema pré-preenche o quiz com o que extrair
   └── Responda só o que faltar das 7 perguntas
       (área, nível, localização, preferências, soft skills, objetivo, habilidades)

2. Menu principal (duas seções, letras A–I)
   ╭─ Esteira de Carreira ────────────────────────────╮
   ├── [A] Buscar Vagas
   │       Scout pesquisa vagas compatíveis com seu perfil e calcula o
   │       match de habilidades. Filtro de recência: 24h · 7 dias · 1 mês · todas
   │
   ├── [B] Encontrar Cursos
   │       Curator analisa as habilidades faltantes das vagas
   │       e monta uma trilha acessivel (gratuito, videos, docs e cursos pagos quando fizer sentido)
   │
   ├── [C] Entrevista Simulada
   │       Coach conduz 5 perguntas com feedback em tempo real
   │       e entrega pontuação final com áreas de melhoria.
   │       Quando há vaga analisada + relatório de aderência, as perguntas
   │       técnicas e de cenário são calibradas pela vaga e pelas lacunas do match
   │
   └── [D] Refazer Quiz
           Reseta o perfil e reinicia do zero
   ╰──────────────────────────────────────────────────╯
   ╭─ Esteira de Candidatura ─────────────────────────╮
   ├── [E] Analisar Vaga
   │       Cole a descrição da vaga e o Maestro extrai cargo, empresa,
   │       senioridade, hard/soft skills, ferramentas, requisitos e alertas.
   │       Reanalisar apaga o match/tailoring/PDI anteriores.
   │
   ├── [F] Comparar Vaga × Currículo
   │       ResumeMatcher calcula o score de aderência (0–100) e separa
   │       evidências fortes, parciais e lacunas críticas.
   │
   ├── [G] Sugestões de Currículo
   │       ResumeTailor gera orientações seguras por seção (resumo,
   │       habilidades, projetos, experiências) e palavras-chave.
   │
   ├── [H] Gerar PDI
   │       PdiGenerator transforma as lacunas em plano de 7/30/60 dias,
   │       com projetos práticos, estudos e preparação para entrevista.
   │
   └── [I] Reconciliar
           Reconciler detecta conflitos entre perfil, currículo e vaga,
           com score de consistência e recomendações pelo foco da candidatura.
   ╰──────────────────────────────────────────────────╯
   As etapas E–I também rodam pela Career Arcade Pipeline (botões/REST);
   o chat é a via conversacional para acioná-las sem sair do terminal.
```

---

## Interface

A interface foi projetada com estética **dark tech** — escura, densa e funcional, com toques de cor para hierarquia visual.

- **Tipografia**: Space Grotesk (corpo) · Syne (títulos) · JetBrains Mono (código e dados)
- **Paleta**: fundo `#050508` · ciano `#22d3ee` · rosa `#f472b6` · emerald `#34d399`
- **Efeitos**: dot grid, scanline sutil, noise texture, glow nos elementos ativos
- **Animações**: Framer Motion — streaming token a token, fade-in nas mensagens, pulse no agente ativo, expansão suave da pipeline
- **Career Arcade Pipeline**: rota de 6 fases que recolhe numa barra de progresso futurista (nós neon ciano, conectores ciano→rosa, etapa atual pulsante)
- **Barra de escrita flutuante**: input translúcido com blur e glow; nos momentos de escolha (menu) ela vira cards de opção animados, voltando ao texto livre depois
- **Sidebar**: perfil do usuário com barra de progresso, funções alvo, skills em tags e filtro de recência das vagas; recolhe para modo compacto (ícones)

---

## Robustez operacional

O backend passou por uma etapa de hardening para operar como API de producao:

- **Logging estruturado** em JSON via `logging_config.py`, com `session_id` em eventos de WebSocket, agentes e chamadas externas.
- **Contratos de erro seguros** no FastAPI para validacao 422 e falhas internas 500, sem expor stack trace ao frontend.
- **Persistencia atomica** com locks por sessao e `write_text_atomic_async`, evitando corrupcao em escritas concorrentes.
- **Estado do WebSocket recuperavel** em `data/sessions/{session_id}/chat_state.json`.
- **Firecrawl SDK oficial** (`firecrawl-py`) no lugar de CLI/subprocess, executado fora do Event Loop com `asyncio.to_thread`.
- **Upload de curriculos endurecido** com limite de tamanho, validacao de `Content-Type` e Magic Numbers para PDF/DOCX.
- **Suite automatizada** com 150 testes passando, incluindo stress test de 50 escritas simultaneas.

---

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | Chave da API OpenAI | — |
| `FIRECRAWL_API_KEY` | Chave da API Firecrawl | — |
| `LLM_MODEL` | Modelo LLM a usar | `gpt-4o-mini` |
| `LLM_BASE_URL` | URL base de um provedor compatível com a API OpenAI (ex.: OpenRouter). Vazio usa o endpoint padrão da OpenAI | — |
| `DATA_DIR` | Diretório dos arquivos de estado | `../data` |
| `PERSONAS_DIR` | Diretório das personas | `../personas` |
| `SKILLS_DIR` | Diretório das skills | `../skills` |
| `LOG_LEVEL` | Nível de logging do backend | `INFO` |
| `LOG_TO_FILE` | Habilita escrita de logs em arquivo | `false` |
| `LOG_DIR` | Diretório de logs quando `LOG_TO_FILE=true` | `../logs` |
| `LOG_FILE` | Arquivo de log do backend | `../logs/backend.log` |
| `LOG_MAX_BYTES` | Tamanho máximo do arquivo de log rotativo | `5242880` |
| `LOG_BACKUP_COUNT` | Quantidade de backups de log rotativo | `3` |

---

## Tecnologias

**Backend**:

- [FastAPI](https://fastapi.tiangolo.com) — framework web assíncrono
- [WebSockets](https://websockets.readthedocs.io) — streaming em tempo real
- [OpenAI Python SDK](https://github.com/openai/openai-python) — integração com LLMs
- [Firecrawl SDK](https://firecrawl.dev) (`firecrawl-py`) — scraping e busca web

**Frontend**:

- [React 19](https://react.dev) + [TypeScript](https://typescriptlang.org)
- [Vite](https://vitejs.dev) — build tool
- [Tailwind CSS](https://tailwindcss.com) — utilitários de estilo
- [Framer Motion](https://www.framer.com/motion) — animações
- [React Markdown](https://github.com/remarkjs/react-markdown) — renderização de markdown
- [Lucide React](https://lucide.dev) — ícones

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.
