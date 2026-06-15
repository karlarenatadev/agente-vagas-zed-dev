<div align="center">

# import vagas

**Plataforma de desenvolvimento de carreira com IA multi-agente**

Encontre vagas alinhadas ao seu perfil, descubra o que aprender e pratique entrevistas — tudo em uma conversa.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/Licença-MIT-8B5CF6?style=flat-square)](LICENSE)

</div>

---

## O que é

**import vagas** é um sistema multi-agente de desenvolvimento de carreira que combina busca inteligente de empregos, recomendação de cursos e simulação de entrevistas em uma interface conversacional.

O sistema é orquestrado pelo **Maestro**, que coordena três agentes especializados:

| Agente | Papel | Como funciona |
|--------|-------|---------------|
| **Scout** | Busca de vagas | Pesquisa no Indeed, LinkedIn, Catho e Glassdoor via Firecrawl, extrai requisitos e calcula o match com suas habilidades |
| **Curator** | Trilha de aprendizado | Para cada habilidade que falta, prioriza materiais gratuitos, videos, documentacao oficial e cursos pagos acessiveis; premium entra apenas quando for relevante |
| **Coach** | Entrevista simulada | Conduz 5 perguntas técnicas e comportamentais com feedback em tempo real e pontuação final |

---

## Funcionalidades

Além da busca de vagas, cursos e entrevista, a plataforma cobre o ciclo completo de candidatura:

- **Diagnóstico de perfil** — quiz de 7 perguntas (área, nível, localização, preferências, soft skills, objetivo, habilidades).
- **Currículo → quiz automático** — envie um currículo em **PDF, DOCX ou TXT** e o sistema extrai área, nível, habilidades e soft skills, **pré-preenchendo o quiz** e perguntando só o que falta.
- **Filtro de recência das vagas** — escolha **24h, 7 dias, 1 mês ou todas**; o Scout aplica o filtro `--tbs` do Firecrawl na busca.
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
│                        │  Firecrawl CLI                  │
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
│   └── firecrawl.md       # Comandos e regras do Firecrawl
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

> **Privacidade:** os arquivos `data/*.md` são estado local por pessoa/sessão e
> podem conter dados sensíveis (currículo, perfil). Eles são ignorados pelo Git —
> apenas `data/README.md` é versionado.

---

## Pré-requisitos

- **Python** 3.11+
- **Node.js** 18+
- **Firecrawl CLI** — `npm install -g firecrawl`
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

## Fluxo de uso

```
1. Perfil
   ├── Envie um currículo (PDF/DOCX/TXT) — opcional
   │   e o sistema pré-preenche o quiz com o que extrair
   └── Responda só o que faltar das 7 perguntas
       (área, nível, localização, preferências, soft skills, objetivo, habilidades)

2. Menu principal
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
   │       e entrega pontuação final com áreas de melhoria
   │
   └── [D] Refazer Quiz
           Reseta o perfil e reinicia do zero

3. Esteira de candidatura (Career Arcade Pipeline)
   Currículo → Vaga → Match → Sugestões → PDI → Entrevista
   Analise uma vaga, veja o match, gere sugestões seguras de currículo,
   monte um PDI de 7/30/60 dias e salve candidaturas no tracker.
```

---

## Interface

A interface foi projetada com estética **dark tech** — escura, densa e funcional, com toques de cor para hierarquia visual.

- **Tipografia**: Space Grotesk (corpo) · Syne (títulos) · JetBrains Mono (código e dados)
- **Paleta**: fundo `#050508` · ciano `#22d3ee` · rosa `#f472b6` · emerald `#34d399`
- **Efeitos**: dot grid, scanline sutil, noise texture, glow nos elementos ativos
- **Animações**: Framer Motion — streaming token a token, fade-in nas mensagens, pulse no agente ativo, expansão suave da pipeline
- **Career Arcade Pipeline**: rota de 6 fases que recolhe numa barra de progresso futurista (nós neon ciano, conectores ciano→rosa, etapa atual pulsante)
- **Sidebar**: perfil do usuário com barra de progresso, funções alvo, skills em tags e filtro de recência das vagas; recolhe para modo compacto (ícones)

---

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | Chave da API OpenAI | — |
| `FIRECRAWL_API_KEY` | Chave da API Firecrawl | — |
| `LLM_MODEL` | Modelo OpenAI a usar | `gpt-4o-mini` |
| `DATA_DIR` | Diretório dos arquivos de estado | `../data` |
| `PERSONAS_DIR` | Diretório das personas | `../personas` |
| `SKILLS_DIR` | Diretório das skills | `../skills` |

---

## Tecnologias

**Backend**
- [FastAPI](https://fastapi.tiangolo.com) — framework web assíncrono
- [WebSockets](https://websockets.readthedocs.io) — streaming em tempo real
- [OpenAI Python SDK](https://github.com/openai/openai-python) — integração com LLMs
- [Firecrawl](https://firecrawl.dev) — scraping e busca web

**Frontend**
- [React 18](https://react.dev) + [TypeScript](https://typescriptlang.org)
- [Vite](https://vitejs.dev) — build tool
- [Tailwind CSS](https://tailwindcss.com) — utilitários de estilo
- [Framer Motion](https://www.framer.com/motion) — animações
- [React Markdown](https://github.com/remarkjs/react-markdown) — renderização de markdown
- [Lucide React](https://lucide.dev) — ícones

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.
