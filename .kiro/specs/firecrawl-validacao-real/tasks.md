# Implementation Plan: Validação Real do Firecrawl

## Overview

A integração com o Firecrawl já existe em `backend/firecrawl_client.py`,
`backend/agents/scout.py`, `backend/agents/curator.py` e
`frontend/src/components/ScoutReport.tsx`. Este plano **formaliza os contratos de
proveniência** (campo `source`, `status_busca`, marcadores de "não informado" e
regras de link), **fecha a malha de testes automatizados** que impedem regressões
na sinalização de origem e **cria o roteiro de validação manual** reproduzível.

Linguagens de implementação (definidas no design):
- Backend: **Python** com **pytest** (`backend/tests/`).
- Frontend: **TypeScript** com **vitest** (`frontend/`).

O design não define uma seção de "Correctness Properties"; portanto a estratégia
de teste usa **testes unitários e de integração baseados em exemplo**, conforme os
Requisitos 8, 9 e 10. Como esses requisitos exigem os testes como entregável, as
sub-tarefas de teste que satisfazem diretamente os Requisitos 8/9/10 são parte do
núcleo do plano; sub-tarefas de teste suplementares são marcadas com `*`.

## Tasks

- [x] 1. Garantir invariante de origem das vagas no Scout
  - [x] 1.1 Adicionar guarda de validação de `source` no `ScoutAgent`
    - Em `backend/agents/scout.py`, validar que toda `job_entry` possui `source`
      em `{real, llm, simulated}` antes de emitir o relatório em `run`
    - Bloquear a geração do relatório (levantar erro de domínio controlado) quando
      uma entrada não tiver `source` válido
    - Garantir que, para `source == "real"`, `fallback_reason` e `fallback_message`
      permaneçam vazios; e que `llm`/`simulated` os preencham
    - _Requirements: 1.1, 1.5, 1.6, 1.8_

  - [x] 1.2 Escrever testes unitários da guarda de origem
    - Verificar que uma `job_entry` sem `source` válido impede o relatório
    - Verificar que `source == "real"` mantém campos de fallback vazios
    - _Requirements: 1.6, 1.8_

- [x] 2. Completar cobertura de origem e estado de busca do Scout
  - [x] 2.1 Completar testes de `source` e `status_busca` no Scout
    - Em `backend/tests/test_scout.py`, garantir cobertura dos três valores de
      `source` (`real`, `llm`, `simulated`)
    - Garantir cobertura dos seis valores de `status_busca`: `real_success`,
      `real_empty`, `real_degraded`, `no_credits`, `external_error` e `timeout`
    - Cobrir explicitamente o caso `timeout` e o `real_degraded` com
      `busca_degradada = true`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 8.1, 8.2_

- [x] 3. Normalizar salários e requisitos das vagas (Scout)
  - [x] 3.1 Garantir marcadores de "não informado" e consolidação de requisitos
    - Em `backend/agents/scout.py`, garantir que `salario` e `beneficios` recebam
      "Não informado na descrição" quando ausentes em vagas reais e simuladas
    - Garantir que `habilidades_correspondentes`/`habilidades_faltantes` usem
      "Nenhuma" quando vazias e que `score_aderencia` seja inteiro em `[0, 100]`
    - Garantir que `_recurring_requirements` produza requisitos mais recorrentes
      com a contagem de ocorrências
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 3.2 Escrever testes de normalização de salário/benefícios e requisitos
    - Verificar marcação "Não informado na descrição" para salário/benefícios
      ausentes
    - Verificar consolidação dos requisitos mais recorrentes com contagens
    - Verificar clamp do `score_aderencia` em `[0, 100]` e marcador "Nenhuma"
    - _Requirements: 9.1, 9.2_

- [x] 4. Registro estruturado e conversão de erros do Firecrawl_Client
  - [x] 4.1 Garantir logs JSON e conversão tipada de erros
    - Em `backend/firecrawl_client.py`, garantir log `firecrawl_search_success`
      com `session_id` e `result_count` no sucesso
    - Garantir log de erro com `session_id` e `error_type` na falha
    - Garantir conversão para `FirecrawlCreditError` quando houver sinal de
      crédito e `FirecrawlProviderError` caso contrário
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 4.2 Escrever testes de logging e conversão de erros
    - Verificar emissão dos logs de sucesso/erro com `session_id` (capturando logs)
    - Verificar conversão de falha em `FirecrawlProviderError`/`FirecrawlCreditError`
      conforme indicação de créditos (heurística `_is_credit_exhaustion`)
    - _Requirements: 8.3_

- [x] 5. Origem e normalização dos cursos (Curator)
  - [x] 5.1 Garantir distinção de origem e normalização de atributos dos cursos
    - Em `backend/agents/curator.py`, garantir que recursos de busca real sejam
      marcados como reais e que o motivo de falha seja gravado em
      `SearchOutcome.error`
    - Garantir complemento via `INTERNAL_RECOMMENDATIONS` com marcação de
      recomendação interna (avisos) quando a cobertura externa for insuficiente
    - Garantir normalização de `plataforma`, `nivel`, `preco` e `duracao`
      (com "Nao informado" quando ausente)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 6.1, 6.2, 6.3, 6.4_

  - [x] 5.2 Escrever testes de origem e normalização dos cursos
    - Verificar distinção entre recurso de busca real e recomendação interna no
      relatório
    - Verificar normalização de plataforma, nível, preço e duração, incluindo
      "Nao informado" para duração ausente
    - _Requirements: 9.3_

- [x] 6. Checkpoint - Backend
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Abertura segura de links de vagas (frontend)
  - [x] 7.1 Configurar ambiente de teste do frontend (vitest + jsdom)
    - Criar `frontend/vitest.config.ts` com ambiente `jsdom`
    - Configurar setup do `@testing-library/react` (arquivo de setup, se necessário)
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 7.2 Garantir contrato de `normalizeHttpLink` e renderização segura
    - Em `frontend/src/components/ScoutReport.tsx`, garantir que o link clicável só
      apareça quando `source === 'real'` e a URL tiver esquema `http(s)` válido
    - Garantir que `llm`/`simulated` nunca produzam link clicável e que o `link`
      textual gerado por IA seja não navegável
    - Garantir abertura em nova aba com `rel="noopener noreferrer"`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 7.3 Escrever testes de normalização de links do ScoutReport
    - Criar `frontend/src/components/ScoutReport.test.tsx`
    - Vaga `real` com URL http(s) válida produz link clicável com `noopener
      noreferrer`
    - Vagas `llm`/`simulated` não produzem link clicável
    - Vaga `real` com link sem esquema http(s) válido não produz link clicável
    - _Requirements: 10.1, 10.2, 10.3, 7.5_

- [x] 8. Roteiro de validação manual com chave e créditos reais
  - [x] 8.1 Criar documento versionado do roteiro de validação manual
    - Criar arquivo de roteiro versionado (markdown) no repositório
    - Descrever pré-requisitos de configuração da chave e dos créditos do Firecrawl
    - Descrever passos para busca completa de vagas (Scout) registrando o
      `status_busca` observado
    - Descrever passos para busca real de cursos (Curator) registrando a origem dos
      recursos
    - Definir critérios objetivos de aprovação para salários/requisitos, exibição
      da origem e abertura de links reais no navegador
    - Definir resultado esperado para os casos de ausência de créditos, erro e
      timeout
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 9. Checkpoint final - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tarefas marcadas com `*` são sub-tarefas de teste suplementares e podem ser
  puladas para um MVP mais rápido. As sub-tarefas de teste não marcadas (2.1, 4.2,
  5.2, 7.3) satisfazem diretamente os Requisitos 8, 9 e 10 e fazem parte do núcleo.
- Cada tarefa referencia cláusulas específicas dos requisitos para rastreabilidade.
- O design não possui seção de "Correctness Properties"; portanto a validação usa
  testes unitários e de integração baseados em exemplo, não testes baseados em
  propriedades.
- A execução real consumindo créditos do Firecrawl é coberta pelo roteiro de
  validação manual (tarefa 8) e não por testes automatizados, por depender de
  chave, créditos e serviço externo.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "4.1", "5.1", "7.1", "8.1"] },
    { "id": 1, "tasks": ["1.2", "3.1", "4.2", "5.2", "7.2"] },
    { "id": 2, "tasks": ["2.1", "7.3"] },
    { "id": 3, "tasks": ["3.2"] }
  ]
}
```
