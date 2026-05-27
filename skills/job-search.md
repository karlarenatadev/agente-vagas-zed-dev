# Job Search Skill - Fluxo de Busca de Vagas

## Visão Geral

Esta skill define o fluxo completo que o Scout deve seguir para buscar vagas de emprego, extrair detalhes, realizar correspondência de habilidades e retornar resultados formatados.

## Pré-requisitos

- Firecrawl CLI instalado e configurado
- `FIRECRAWL_API_KEY` definida no ambiente
- Arquivo `data/user-profile.md` existente e populado

## Fluxo de Trabalho Passo a Passo

### 1. Leitura do Perfil do Usuário

Leia o arquivo `data/user-profile.md` usando `read_file` para obter:
- `Área de interesse`
- `Localização`
- `Nível de experiência`
- `Habilidades atuais`

### 2. Descoberta de Vagas (Firecrawl Search)

Execute o comando via `terminal`:

```bash
firecrawl search "vagas [area_de_interesse] [localizacao]" --json
```

**Exemplo**:
```bash
firecrawl search "vagas frontend remoto" --json
```

**Saída esperada**: JSON com campos: `url`, `titulo`, `descricao`, `cargo` para cada resultado.

**Tratamento de erro**: Se o comando falhar, retorne `estado: erro` com a mensagem exata do erro.

### 3. Extração de Detalhes Completos (Firecrawl Scrape)

Para cada URL de vaga nos resultados da busca (máximo 10 URLs para processamento):

```bash
firecrawl scrape <url> --format markdown
```

**Tratamento de falha**: Se o scrape falhar para uma URL específica, use o `titulo` e `descricao` do resultado da busca como fallback. Anote que a extração detalhada falhou.

### 4. Extração de Habilidades Requeridas

A partir da descrição completa da vaga (markdown do scrape ou descrição da busca), extraia:
- Habilidades técnicas mencionadas
- Ferramentas e tecnologias
- Nível de experiência mencionado

**Regra**: Use correspondência de strings case-insensitive.

### 5. Correspondência de Habilidades

Compare as habilidades requeridas da vaga com as `Habilidades atuais` do usuário (de `data/user-profile.md`).

**Algoritmo**:
1. Para cada habilidade requerida, verifique se existe na lista de habilidades atuais (case-insensitive)
2. Liste as habilidades que correspondem → `habilidades_correspondentes`
3. Liste as habilidades que não correspondem → `habilidades_faltantes`
4. Calcule: `contagem_correspondencia: [X] de [Y] habilidades correspondem`

### 6. Filtragem por Nível de Experiência

- Se a vaga mencionar um nível de experiência, prefira vagas que correspondam ao `Nível de experiência` do usuário
- Níveis: Júnior, Pleno, Sênior
- Se não houver vagas do nível correspondente nos primeiros resultados, expanda a busca e inclua vagas de nível adjacente, anotando a discrepância

### 7. Formatação da Resposta

Retorne até 5 vagas no formato de Envelope de Resposta:

```
## RESPOSTA: SCOUT
### estado
sucesso

### resumo
Encontrei [X] vagas correspondentes à sua área de interesse em [localização]. Aqui estão os resultados com correspondência de habilidades.

### dados
1. titulo: [título da vaga]
   empresa: [nome da empresa - extrair da URL ou título]
   localizacao: [cidade ou Remoto]
   link: [URL]
   habilidades_correspondentes: [Python, SQL]
   habilidades_faltantes: [Docker, Kubernetes]
   contagem_correspondencia: 2 de 4 habilidades correspondem

2. titulo: [próximo título]
   ...

### erros
[Vazio se sucesso]
```

## Comandos Firecrawl

### Search
```bash
firecrawl search "query" --json
```
- Retorna JSON com resultados de busca
- Cada resultado tem: url, titulo, descricao, cargo

### Scrape
```bash
firecrawl scrape <url> --format markdown
```
- Retorna markdown limpo da página
- Útil para obter descrição completa e requisitos da vaga

## Regras de Formatação de Saída

- Nunca use tabelas markdown
- Use listas numeradas com pares chave-valor
- Campos obrigatórios: titulo, empresa, localizacao, link, habilidades_correspondentes, habilidades_faltantes, contagem_correspondencia
- Se não conseguir extrair algum campo, use "Não informado"

## Tratamento de Erros

| Erro | Ação |
|------|------|
| `firecrawl search` falha | Retorne `estado: erro` com mensagem exata |
| `firecrawl scrape` falha em URL | Use fallback (título/descrição da busca), anote a falha |
| Nenhum resultado encontrado | Sugira ampliar termos de busca, retorne `estado: erro` |
| Falha ao ler `user-profile.md` | Retorne `estado: erro` indicando arquivo faltante |

## Exemplo de Execução Completa

1. Ler `data/user-profile.md` → Área: Frontend, Localização: Remoto, Nível: Júnior, Habilidades: HTML, CSS, JavaScript
2. Executar: `firecrawl search "vagas frontend remoto" --json`
3. Para cada URL no resultado, executar: `firecrawl scrape <url> --format markdown`
4. Extrair habilidades das descrições (ex: React, TypeScript, HTML, CSS, Git)
5. Corresponder: HTML ✓, CSS ✓, JavaScript ✓, React ✗, TypeScript ✗, Git ✗
6. Formatar: `contagem_correspondencia: 3 de 6 habilidades correspondem`
7. Retornar até 5 vagas formatadas
