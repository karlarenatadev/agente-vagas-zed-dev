# Firecrawl Skill - Comandos e Regras

## Visão Geral

Esta skill define os comandos e regras para usar o Firecrawl CLI, ferramenta primária de acesso à web para o sistema Recoloca IA.

## Pré-requisitos

- Firecrawl CLI instalado (`npm install -g firecrawl` ou equivalente)
- `FIRECRAWL_API_KEY` definida no ambiente
- Acesso à internet

## Comandos Principais

### 1. Firecrawl Search

**Propósito**: Busca URLs e conteúdo na web, agregando resultados de múltiplas fontes (Indeed, Catho, LinkedIn, Glassdoor, Infojobs, etc.)

**Sintaxe**:
```bash
firecrawl search "query de busca" --json
```

**Exemplos**:
```bash
firecrawl search "vagas frontend remoto" --json
firecrawl search "cursos python alura" --json
firecrawl search "entrevista desenvolvedor backend" --json
```

**Saída JSON**:
```json
[
  {
    "url": "https://exemplo.com/vaga1",
    "titulo": "Vaga Frontend React",
    "descricao": "Descrição resumida da vaga...",
    "cargo": "Desenvolvedor Frontend"
  },
  ...
]
```

**Regras**:
- Sempre use `--json` para facilitar o processamento
- A query deve ser específica o suficiente para retornar resultados relevantes
- Se não houver resultados, o comando retorna uma lista vazia `[]`

### 2. Firecrawl Scrape

**Propósito**: Extrai o conteúdo completo de uma URL específica em formato markdown limpo (sem JavaScript, sem anúncios, sem elementos de navegação).

**Sintaxe**:
```bash
firecrawl scrape <url> --format markdown
```

**Exemplos**:
```bash
firecrawl scrape https://exemplo.com/vaga1 --format markdown
firecrawl scrape https://cursos.alura.com.br/course/python --format markdown
```

**Saída**:
- Markdown limpo com o conteúdo principal da página
- Remove elementos de navegação, anúncios, scripts

**Regras**:
- Use para obter descrições completas de vagas, detalhes de cursos, etc.
- Se a extração falhar, use o título e descrição do resultado da busca como fallback
- Timeout padrão: 30 segundos

## Fallback para Firecrawl

Se o Firecrawl falhar consistentemente (ex: API key inválida, sem internet, etc.), você PODE usar `curl` ou `wget` como fallback.

**Limitações do Fallback**:
- Sem renderização JavaScript (alguns sites não carregam conteúdo dinâmico)
- Possíveis bloqueios anti-bot
- HTML bruto em vez de markdown limpo
- Menos confiável que o Firecrawl

**Exemplo de Fallback com curl**:
```bash
curl -s "https://exemplo.com" > temp.html
```

**Regra**: Prefira sempre o Firecrawl primeiro. Use curl/wget apenas como recuperação em caso de falha total do Firecrawl.

## Tratamento de Erros

| Erro | Causa Provável | Ação |
|------|----------------|------|
| `FIRECRAWL_API_KEY not found` | Variável de ambiente não definida | Reporte ao usuário para configurar a API key |
| `timeout` | Site lento ou indisponível | Tente novamente ou use fallback |
| `no results found` | Query muito específica ou sem resultados | Sugira ampliar os termos de busca |
| `invalid URL` | URL mal formatada | Verifique a URL e tente novamente |

## Regras de Uso

1. **Sempre use Firecrawl como método primário** de acesso à web
2. **Nunca invente dados** se o Firecrawl falhar - reporte o erro exato
3. **Use fallback apenas quando o Firecrawl falhar consistentemente**
4. **Sempre processe a saída JSON** do `firecrawl search` para extrair campos relevantes
5. **Sempre use `--json`** no comando search para facilitar o processamento
6. **Limite o número de URLs para scrape** (máximo 10 por busca) para evitar timeouts

## Integração com o Sistema

- **Scout**: Usa `firecrawl search` para buscar vagas, `firecrawl scrape` para detalhes
- **Curator**: Usa `firecrawl search` para buscar cursos, `firecrawl scrape` para detalhes
- **Coach**: Pode usar `firecrawl search` para buscar dicas de entrevista (opcional)

## Exemplo de Fluxo Completo (Scout)

1. `firecrawl search "vagas frontend remoto" --json` → Obtém lista de vagas
2. Para cada vaga na lista (máximo 5):
   - `firecrawl scrape <url> --format markdown` → Obtém descrição completa
   - Extrai habilidades da descrição
   - Compara com perfil do usuário
3. Retorna resultados formatados

## Notas Importantes

- O Firecrawl é uma ferramenta de terceiros - respeite os limites de uso da API
- Não faça muitas requisições em sequência muito rápida (rate limiting)
- Sempre verifique se a `FIRECRAWL_API_KEY` está configurada antes de usar
