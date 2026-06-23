# Plano de implementação — Coach conectado à vaga analisada

> **Item 1 da auditoria de backend (2026-06-23).** Conectar o Coach à
> descrição da vaga (`job-description-analysis.md`) e ao relatório de aderência
> (`resume-match-report.md`), fechando a proposta de "entrevista baseada na
> vaga". Hoje o Coach só consome o Scout (`job-search-results.md`) e o Curator
> (`course-recommendations.md`).

Este documento é a especificação para quem for escrever o código. Tudo está em
`backend/`. **Não** há mudança de frontend, `config.py` ou `session.py`.

---

## 1. Objetivo e critério de sucesso

A entrevista simulada deve usar, quando disponíveis:

* a **descrição da vaga analisada** (título, empresa, senioridade,
  responsabilidades, requisitos obrigatórios, hard skills, ferramentas) como
  contexto principal da entrevista;
* o **relatório de aderência** (score, nível de prontidão, lacunas críticas,
  evidências fortes, requisitos ausentes) para calibrar perguntas técnicas,
  perguntas sobre lacunas e o feedback final.

Quando esses artefatos **não existem**, o comportamento atual (Scout + perfil)
deve continuar funcionando sem regressão.

---

## 2. Estado atual (o que mudar e onde)

### `backend/agents/coach.py`

* `run()` (linha ~372) recebe um `context` com `profile`, `job_results`,
  `course_recommendations`, `interview_context`, `history`, `step`.
* Monta o `interview_brief` via `_build_interview_brief(...)` (linha ~121), que
  hoje só conhece perfil + Scout + Curator.
* `_question_for_step(...)` (linha ~192) gera as perguntas de fallback lendo o
  brief. Os passos 2 e 4 referenciam "requisitos recorrentes" e "vagas do
  Scout" — devem passar a referenciar a **vaga analisada** e as **lacunas do
  match**.
* `QUESTION_PLAN` (linha ~34): os focos dos passos 2 e 4 citam o Scout; ajustar
  o texto para refletir vaga/match (não muda a estrutura, só a descrição).
* **Gate** em `run()` (linha ~386): hoje retorna erro se `job_results` não tem
  `"habilidades_faltantes"`. Precisa aceitar também o caminho "vaga analisada".

### `backend/agents/maestro.py`

* `_dispatch_coach_start()` (linha ~691): lê profile/job_results/course_recs e
  chama `coach.run({...})`. **Não lê** os dois artefatos novos nem os repassa.
  O `interview_context` é resolvido pelo primeiro título do Scout.
* `_handle_coach()` (linha ~775): idem — duas chamadas a `coach.run({...})`
  (passos 2-5 e passo 6) sem os artefatos novos.
* **Gate** em `_dispatch_coach_start` (linha ~702): bloqueia sem Scout.

---

## 3. Decisões de design (seguir estas)

1. **Reusar os parsers canônicos, não escrever regex novo.**
   * `from agents.job_description_analyzer import analysis_from_markdown`
   * `from agents.resume_matcher import match_report_from_markdown`
   Ambos recebem o conteúdo do `.md` e devolvem um `dict` (ou `None` se o
   arquivo for inválido/ausente). Isso evita aliasing frágil e segue o padrão
   do `reconciliation.py`, que já reusa helpers do matcher.

2. **Os artefatos são enriquecimento opcional, não obrigatório.**
   Se `job-description-analysis.md` existir → usar como contexto primário.
   Se faltar → cair no fluxo Scout/perfil de hoje. O match é sempre opcional
   (calibra, mas não bloqueia).

3. **Prioridade do `interview_context`** (rótulo da entrevista):
   1. Título + empresa da **vaga analisada** (`analysis['title']` /
      `analysis['company']`), se houver análise;
   2. senão, primeira vaga do Scout (comportamento atual);
   3. senão, "Funções alvo" do perfil;
   4. senão, "Posição baseada no seu perfil".

4. **Relaxar o gate** para permitir iniciar a entrevista quando existir **OU**
   resultado do Scout **OU** vaga analisada. Só bloquear quando faltarem os
   dois (além do perfil, que continua obrigatório).

5. **Compatibilidade:** assinatura de `coach.run(context)` continua aceitando
   um `dict`; as chaves novas são opcionais. Nenhum teste existente deve
   quebrar.

---

## 4. Mudanças por arquivo

### 4.1 `backend/agents/coach.py`

**a) Novas chaves de contexto em `run()`** — ler dois artefatos novos, com o
mesmo padrão de fallback do código atual (`context.get(...) or self._read_context_file(...)`):

```python
job_analysis = context.get("job_analysis", "") or self._read_context_file(self.paths.JOB_DESCRIPTION_ANALYSIS_FILE)
match_report = context.get("match_report", "") or self._read_context_file(self.paths.RESUME_MATCH_REPORT_FILE)
```

**b) Helpers novos de extração** (privados), usando os parsers canônicos:

* `_parse_job_analysis(text) -> dict` → `analysis_from_markdown(text) or {}`.
* `_parse_match_report(text) -> dict` → `match_report_from_markdown(text) or {}`.

Não reimplementar parsing por regex — só adaptar os dicts retornados para as
linhas do brief.

**c) Estender `_build_interview_brief(...)`** para receber `job_analysis` e
`match_report` e adicionar linhas ao brief (manter as linhas atuais para não
quebrar `_brief_value`/`_question_for_step`). Linhas novas sugeridas (rótulos
em texto simples, sem acento problemático, seguindo o estilo já existente):

```
Vaga analisada (titulo): {analysis.title}
Vaga analisada (empresa): {analysis.company}
Senioridade da vaga: {analysis.seniority}
Responsabilidades da vaga: {join(analysis.responsibilities[:6])}
Requisitos obrigatorios da vaga: {join(analysis.required_requirements[:8])}
Hard skills da vaga: {join(analysis.hard_skills[:8])}
Ferramentas da vaga: {join(analysis.tools[:6])}
Score de aderencia: {report.overall_score}/100
Nivel de prontidao: {report.readiness_level}
Lacunas criticas do match: {join(report.critical_gaps[:6])}
Requisitos ausentes no curriculo: {join(report.missing_requirements[:6])}
Evidencias fortes do curriculo: {join(report.strong_evidence[:6])}
```

> Os agentes de prompt (`_generate_question`, `_evaluate_and_ask`,
> `_final_evaluation`) **já injetam o `interview_brief` inteiro** no prompt do
> LLM — então enriquecer o brief melhora automaticamente as perguntas reais.
> O trabalho extra é só no **fallback determinístico**.

**d) `_question_for_step(...)`** (perguntas de fallback sem LLM): quando houver
contexto de vaga/match, priorizar esses campos. Exemplos:

* **Passo 2 (técnica):** usar `Requisitos obrigatorios da vaga` +
  `Hard skills da vaga` em vez de "requisitos recorrentes" do Scout.
* **Passo 4 (cenário):** usar `Responsabilidades da vaga` e `Lacunas criticas
  do match` em vez de "vagas do Scout".
* Quando os campos da vaga/match estiverem `nao informado`, **cair no texto
  atual** (Scout/perfil). Usar `_brief_value(...)` para ler com default, como já
  é feito.

**e) `QUESTION_PLAN`** — atualizar só as descrições de foco dos passos 2 e 4
para mencionar "requisitos e responsabilidades da vaga analisada" e "lacunas
críticas do relatório de aderência". Não mudar as chaves nem a quantidade.

**f) Gate em `run()`** (linha ~386) — trocar a condição que exige Scout por:

```python
has_scout = bool(job_results.strip()) and "habilidades_faltantes" in job_results
has_job_analysis = bool(job_analysis.strip())
if not has_scout and not has_job_analysis:
    yield "<erro: rode a busca do Scout (A) ou analise uma vaga antes de iniciar a entrevista>"
    return
```

Manter o gate de perfil incompleto como está.

### 4.2 `backend/agents/maestro.py`

**a) `_dispatch_coach_start()`**:
* Ler os dois artefatos: `self._read_file(self.paths.JOB_DESCRIPTION_ANALYSIS_FILE)`
  e `self._read_file(self.paths.RESUME_MATCH_REPORT_FILE)`.
* **Relaxar o gate** (linha ~702): só bloquear quando faltarem Scout **e** vaga
  analisada. Ajustar a mensagem para citar as duas opções (rodar **A** ou colar
  uma vaga).
* **Resolver `interview_context`** pela prioridade da seção 3.3 — preferir
  título+empresa da vaga analisada (parse via `analysis_from_markdown`) antes
  do Scout.
* Passar as chaves novas no `coach.run({...})`:
  `"job_analysis": job_analysis, "match_report": match_report`.

**b) `_handle_coach()`**: ler os mesmos dois artefatos no topo (junto de
profile/job_results/course_recs) e repassá-los nas **duas** chamadas a
`coach.run({...})` (passos 2-5 e passo 6).

> Atenção: `interview_context` é guardado em `self.interview_context` e reusado
> em `_handle_coach`/`_update_interview_session`. Garantir que ele seja
> resolvido no start e persista; o `_handle_coach` não precisa recalcular.

### 4.3 `backend/tests/conftest.py`

Adicionar uma fixture `match_markdown` (não existe), no formato real do
`resume-match-report.md`, para os testes do Coach. Gerar via o serializador
canônico para não acoplar ao texto:

```python
from agents.resume_matcher import ResumeMatcher, match_report_to_markdown

@pytest.fixture
def match_markdown(job_markdown, resume_markdown) -> str:
    report = ResumeMatcher().match(job_markdown, resume_markdown)
    return match_report_to_markdown(report)
```

> **Confirmado:** `ResumeMatcher.match(job_content, resume_content)`
> (`resume_matcher.py:470`) recebe os **dois Markdown brutos** (string) e
> devolve o `dict` do report. A fixture acima está correta como está.

### 4.4 `backend/tests/test_coach.py` (novo)

Não existe teste do Coach hoje. Criar cobrindo a **lógica pura** (sem rede/LLM),
no padrão de `test_scout.py`/`test_curator.py`. Instanciar
`CoachAgent(SessionPaths())` (a fixture autouse `_fake_api_key` já cobre o
cliente OpenAI).

Casos mínimos:

1. `_build_interview_brief` **inclui** título da vaga, requisitos obrigatórios e
   hard skills da vaga quando recebe `job_markdown`.
2. `_build_interview_brief` **inclui** score, nível de prontidão e lacunas
   críticas quando recebe `match_markdown`.
3. `_build_interview_brief` **cai no Scout/perfil** quando os dois artefatos
   novos vêm vazios (não quebra, mantém as linhas antigas).
4. `_question_for_step(2, brief)` e `_question_for_step(4, brief)` mencionam
   requisitos/responsabilidades da vaga quando o brief tem esses campos.
5. Parsers reusados toleram entrada vazia/inválida (`analysis_from_markdown("")`
   e `match_report_from_markdown("")` → `None` → helper devolve `{}`).
6. (Opcional) gate: `run({step:1, profile: completo, job_analysis: <vaga>})`
   **não** retorna o erro "rode a opção A" — ou seja, vaga analisada destrava a
   entrevista sem Scout. Coletar o primeiro chunk do async generator e checar
   que não é o estado de erro.

> **Confirmado:** `pytest-asyncio==1.4.0` está no `requirements-dev.txt`. Para
> os casos que iteram o async generator de `run()`, marcar o teste com
> `@pytest.mark.asyncio` e usar `async for ... in coach.run({...})`. Os casos
> 1-5 (helpers puros `_build_interview_brief`/`_question_for_step`) são síncronos
> e não precisam de marca.

---

## 5. Referência de formato dos artefatos (para conferência)

### `job-description-analysis.md` — `analysis_to_markdown` / `analysis_from_markdown`
Seções `## ...` com bullets `* ...`:
`Resumo` (linhas `* Título:`, `* Empresa:`, `* Senioridade:`, `* Modalidade:`,
`* Localização:`), `Palavras-chave principais`, `Hard skills`, `Soft skills`,
`Ferramentas`, `Responsabilidades`, `Requisitos obrigatórios`,
`Requisitos desejáveis`, `Alertas`, `Próximos passos sugeridos`.
Dict de `analysis_from_markdown`: `title, company, seniority, modality,
location, keywords, hard_skills, soft_skills, tools, responsibilities,
required_requirements, nice_to_have, alerts, next_steps`.

### `resume-match-report.md` — `match_report_to_markdown` / `match_report_from_markdown`
Dict do report (**confirmado em `resume_matcher.py:430-464`**):
`overall_score` (int), `readiness_level`, `job_title`, `resume_summary`,
`score_breakdown` (dict: `hard_skills, tools, soft_skills, keywords,
seniority_area`), `strong_evidence`, `partial_evidence`, `missing_requirements`,
`hard_skills_found`, `hard_skills_missing`, `soft_skills_found`,
`soft_skills_missing`, `tools_found`, `tools_missing`, `matched_keywords`,
`missing_keywords`, `strengths`, `critical_gaps`, `safe_resume_suggestions`,
`do_not_claim`, `next_steps`.

> **Nota:** `match_report_from_markdown` devolve `None` se o `## Resumo` não
> tiver a linha `* Score geral: N/100` válida. O helper `_parse_match_report`
> do Coach deve tratar isso (`... or {}`).

---

## 6. Definição de pronto

* [ ] `coach.py` lê e usa `job-description-analysis.md` e `resume-match-report.md`.
* [ ] `_build_interview_brief` reflete vaga + match; fallback Scout/perfil intacto.
* [ ] `_question_for_step` (fallback) usa requisitos/responsabilidades/lacunas.
* [ ] Maestro lê os dois artefatos e repassa nas 3 chamadas a `coach.run`.
* [ ] `interview_context` prioriza a vaga analisada.
* [ ] Gate aceita iniciar a entrevista com Scout **ou** vaga analisada.
* [ ] `test_coach.py` novo + fixture `match_markdown`; suíte completa passa.
* [ ] `python -m py_compile` nos arquivos alterados + `import main` OK.
* [ ] `python -m pytest` sem regressões (era `112 passed`; deve subir).
* [ ] Atualizar `docs/checklist.md`: marcar os itens "Coach conectado à vaga"
      (seções 1.5, 4.5, 8/Fluxo completo, "Auditoria 2026-06-23") e registrar a
      sessão. Atualizar o `README.md` da raiz se a feature mudar o fluxo descrito.

---

## 7. Fora de escopo (não fazer agora)

* Roteamento conversacional do Maestro para análise de vaga/match/PDI/tailoring
  (item 2 da auditoria — depende disto, mas é etapa separada).
* Caminho real de LLM / bug do `base_url` (registrado para NÃO mexer).
* Frontend: a entrevista continua acessível pelos mesmos comandos/botões atuais.
* Endpoint de foco da candidatura (item separado da reconciliação).
