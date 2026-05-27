# Course Analysis Skill - Busca de Cursos

## Visão Geral

Esta skill define o fluxo completo que o Curator deve seguir para buscar cursos online, analisar relevância e retornar recomendações curadas.

## Pré-requisitos

- Firecrawl CLI instalado e configurado
- `FIRECRAWL_API_KEY` definida no ambiente
- Arquivo `data/job-search-results.md` existente com habilidades faltantes
- Arquivo `data/user-profile.md` existente e populado

## Fluxo de Trabalho Passo a Passo

### 1. Leitura de Resultados de Busca

Leia o arquivo `data/job-search-results.md` usando `read_file` para obter:
- Todas as habilidades faltantes de todas as vagas
- Extraia uma lista única (sem duplicatas) de habilidades faltantes

### 2. Leitura do Perfil do Usuário

Leia o arquivo `data/user-profile.md` usando `read_file` para obter:
- `Área de interesse`
- `Nível de experiência`

### 3. Descoberta de Cursos (Firecrawl Search)

Para cada habilidade faltante (ou para as principais 3-5 habilidades), execute:

```bash
firecrawl search "site:alura.com.br [habilidade_faltante] curso" --json
```

**Exemplo**:
```bash
firecrawl search "site:alura.com.br Machine Learning curso" --json
firecrawl search "site:alura.com.br Tableau curso" --json
```

**Saída esperada**: JSON com campos: `url`, `titulo`, `descricao` para cada resultado.

**Tratamento de erro**: Se o comando falhar, tente busca genérica sem `site:`:
```bash
firecrawl search "curso [habilidade_faltante] alura" --json
```

### 4. Extração de Detalhes Completos (Firecrawl Scrape)

Para cada URL de curso nos resultados da busca (máximo 5 URLs por habilidade):

```bash
firecrawl scrape <url> --format markdown
```

**Tratamento de falha**: Se o scrape falhar para uma URL específica, use o `titulo` e `descricao` do resultado da busca como fallback.

### 5. Análise de Relevância

A partir da descrição completa do curso (markdown do scrape ou descrição da busca), verifique:
- Se o curso aborda a habilidade faltante
- Nível do curso (iniciante, intermediário, avançado)
- Duração estimada
- Requisitos prévios

**Regra**: Use correspondência de strings case-insensitive.

### 6. Seleção e Classificação

- Selecione cursos que abordem as habilidades faltantes
- Classifique por nível (iniciante → intermediário → avançado)
- Priorize cursos da Alura (conforme solicitado no menu)
- Limite a até 5 cursos no total

### 7. Formatação da Resposta

Retorne até 5 cursos no formato de Envelope de Resposta:

```
## RESPOSTA: CURATOR
### estado
sucesso

### resumo
Encontrei [X] cursos que abordam suas lacunas de habilidades. Aqui estão as recomendações curadas e ordenadas por nível.

### dados
1. nome_curso: [título do curso]
   duracao: [ex: 20 horas]
   nivel: [iniciante | intermediario | avancado]
   aborda_habilidade: [nome da habilidade]
   link: [URL]

2. nome_curso: [próximo título]
   ...

Ordem sugerida:
1. [nome do curso]
2. [nome do curso]
3. [nome do curso]

### erros
[Vazio se sucesso]
```

## Comandos Firecrawl para Cursos

### Search Específico (Alura)
```bash
firecrawl search "site:alura.com.br [habilidade] curso" --json
```
- Busca apenas no site da Alura
- Retorna cursos relevantes

### Search Genérico (Fallback)
```bash
firecrawl search "curso [habilidade] alura" --json
```
- Busca mais ampla se a busca específica falhar

### Scrape
```bash
firecrawl scrape <url> --format markdown
```
- Retorna markdown limpo da página do curso
- Útil para obter descrição completa, currículo, nível e duração

## Regras de Formatação de Saída

- Nunca use tabelas markdown
- Use listas numeradas com pares chave-valor
- Campos obrigatórios: nome_curso, duracao, nivel, aborda_habilidade, link
- Se não conseguir extrair algum campo, use "Não informado"
- Sempre inclua a seção "Ordem sugerida" com a sequência recomendada de cursos

## Tratamento de Erros

| Erro | Ação |
|------|------|
| `firecrawl search` falha | Tente busca genérica sem `site:`, ou reporte erro |
| `firecrawl scrape` falha em URL | Use fallback (título/descrição da busca), anote a falha |
| Nenhum resultado encontrado | Tente termos alternativos para a habilidade |
| Falha ao ler `job-search-results.md` | Retorne `estado: erro` indicando arquivo faltante |

## Fallback para Habilidades sem Cursos na Alura

Se não encontrar cursos na Alura para uma habilidade específica:
1. Tente buscar em outras plataformas (Coursera, Udemy, etc.)
2. Se não encontrar nada, pule essa habilidade e continue com as restantes
3. No resumo, mencione quais habilidades não tiveram cursos encontrados

## Exemplo de Execução Completa

1. Ler `data/job-search-results.md` → Habilidades faltantes: Tableau, Machine Learning, pandas, numpy
2. Para cada habilidade, executar: `firecrawl search "site:alura.com.br [habilidade] curso" --json`
3. Para cada URL no resultado, executar: `firecrawl scrape <url> --format markdown`
4. Analisar: Verificar se o curso aborda a habilidade, extrair nível e duração
5. Selecionar: Escolher até 5 melhores cursos
6. Classificar: Ordenar por nível (iniciante → avançado)
7. Formatar: Retornar cursos formatados com ordem sugerida
