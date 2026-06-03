# Course Analysis Skill - Busca de Cursos e Materiais

## Visao Geral

Esta skill define o fluxo completo que o Curator deve seguir para buscar cursos, videos e materiais online que ajudem o usuario a preencher lacunas de habilidades identificadas nas vagas.

O objetivo nao e limitar a recomendacao a uma plataforma. O Curator deve priorizar materiais acessiveis, com bom custo-beneficio, incluindo:

1. cursos gratuitos;
2. videos ou playlists no YouTube;
3. documentacao oficial;
4. cursos pagos com preco acessivel;
5. formacoes premium, quando forem claramente relevantes.

## Pre-requisitos

1. Firecrawl CLI instalado e configurado.
2. `FIRECRAWL_API_KEY` definida no ambiente.
3. Arquivo `data/job-search-results.md` existente com habilidades faltantes.
4. Arquivo `data/user-profile.md` existente e populado.

## Fluxo de Trabalho Passo a Passo

### 1. Validar dados de entrada

Use `find_path` para verificar se `data/job-search-results.md` existe.

Se o arquivo nao existir ou estiver vazio, retorne:

```
## RESPOSTA: CURATOR
### estado
erro

### resumo
Ainda nao tenho lacunas de habilidades para transformar em trilha de estudos.

### dados

### erros
data/job-search-results.md ausente ou vazio. Peca ao usuario para buscar vagas primeiro pela opcao A.
```

### 2. Extrair habilidades faltantes

Leia `data/job-search-results.md` e extraia todas as linhas `habilidades_faltantes:`.

Regras:

1. separar habilidades por virgula ou ponto e virgula;
2. remover valores vazios;
3. ignorar `Nenhuma`, `Nao informado` e `Não informado`;
4. deduplicar sem perder o texto original;
5. priorizar habilidades que aparecem em mais vagas;
6. limitar a 3-5 habilidades principais para nao sobrecarregar o usuario.

### 3. Ler perfil do usuario

Leia `data/user-profile.md` e extraia:

1. `Area de interesse` ou `Área de interesse`;
2. `Nivel de experiencia` ou `Nível de experiência`;
3. `Habilidades atuais`;
4. `Objetivo de carreira`.

Use esses campos para contextualizar a busca. Exemplo: para uma pessoa junior, priorize conteudo introdutorio e projetos guiados.

### 4. Buscar materiais com Firecrawl

Para cada habilidade faltante, execute buscas nesta ordem:

1. Gratuito ou rapido:

```bash
firecrawl search "[habilidade] curso gratuito iniciante youtube portugues" --json
```

2. Documentacao oficial ou tutorial:

```bash
firecrawl search "[habilidade] documentacao oficial tutorial" --json
```

3. Curso pago acessivel:

```bash
firecrawl search "[habilidade] curso barato alura udemy coursera" --json
```

4. Fallback amplo:

```bash
firecrawl search "[habilidade] curso tutorial projeto" --json
```

Se uma busca falhar, registre o erro parcial e tente a proxima busca da mesma habilidade. Nao interrompa todo o fluxo por uma unica falha.

## Fontes recomendadas

Priorize fontes com boa utilidade para alguem em evolucao de carreira:

1. YouTube: videos, playlists e aulas praticas gratuitas.
2. Documentacao oficial: guias, quickstarts e tutoriais mantidos pela ferramenta.
3. Alura: cursos e formacoes em portugues.
4. Udemy: cursos pagos com preco acessivel, quando o resultado indicar relevancia.
5. Coursera ou edX: cursos gratuitos para assistir ou com certificado opcional pago.
6. FreeCodeCamp, Microsoft Learn, Google Cloud Skills Boost, Kaggle Learn e Mozilla MDN, quando aplicavel.

## Extracao de Detalhes

Para URLs promissoras, execute:

```bash
firecrawl scrape <url> --format markdown
```

Extraia, quando disponivel:

1. nome do material;
2. plataforma;
3. preco ou tipo: gratuito, acessivel, premium ou certificado opcional;
4. duracao;
5. nivel;
6. habilidade abordada;
7. link.

Se o scrape falhar para uma URL especifica, use titulo e descricao da busca como fallback e registre o erro parcial.

## Classificacao de Nivel

Use correspondencia case-insensitive.

1. `iniciante`: titulo ou descricao contem Introducao, Introdução, Primeiros Passos, Fundamentos, Basico, Básico, Para Iniciantes, Beginner ou Getting Started.
2. `intermediario`: titulo ou descricao contem Intermediario, Intermediário, Projeto, Pipeline, Pratico, Prático, Hands-on ou implica conhecimento previo.
3. `avancado`: titulo ou descricao contem Avancado, Avançado, Profundo, Expert, Arquitetura, Especialista ou Advanced.

Se nao houver sinal claro, use `iniciante` para usuarios junior e `intermediario` para usuarios pleno/senior.

## Criterios de Seleção

Para cada habilidade, tente retornar ate 2 recomendacoes:

1. uma opcao gratuita ou rapida;
2. uma opcao paga acessivel ou premium, se houver boa correspondencia.

Limite total: ate 8 recomendacoes.

Priorize:

1. conteudo em portugues quando a qualidade for equivalente;
2. conteudo gratuito para o primeiro passo;
3. materiais com projeto pratico;
4. links de fonte confiavel;
5. aderencia direta a habilidade faltante.

Nunca invente nome, duracao, preco ou link. Se nao houver dado, use `Nao informado`.

## Ordenacao

Ordene a trilha por:

1. nivel: iniciante, intermediario, avancado;
2. custo: gratuito, acessivel, premium;
3. recorrencia da habilidade nas vagas;
4. aderencia ao perfil do usuario.

## Formato de Resposta

Retorne sempre o Envelope de Resposta:

```
## RESPOSTA: CURATOR
### estado
sucesso

### resumo
Encontrei [X] materiais para desenvolver as principais lacunas das vagas. Priorizei opcoes gratuitas, acessiveis e praticas para reduzir atrito de aprendizado.

### dados
1. nome_curso: [titulo do curso, video ou material]
   plataforma: [YouTube | Alura | Udemy | Coursera | Documentacao Oficial | outra]
   preco: [gratuito | acessivel | premium | certificado opcional | Nao informado]
   duracao: [ex: 20 horas | 45 minutos | Nao informado]
   nivel: [iniciante | intermediario | avancado]
   aborda_habilidade: [nome da habilidade]
   link: [URL]

2. nome_curso: [proximo material]
   plataforma: [plataforma]
   preco: [preco]
   duracao: [duracao]
   nivel: [nivel]
   aborda_habilidade: [habilidade]
   link: [URL]

Ordem sugerida:
1. [nome do primeiro material]
2. [nome do segundo material]

### erros
[Nenhum erro parcial ou lista numerada de falhas por habilidade/fonte]
```

## Tratamento de Erros

1. Se `data/job-search-results.md` nao existir, retorne `estado: erro` e peca busca de vagas primeiro.
2. Se uma busca falhar para uma habilidade, tente a proxima query da mesma habilidade.
3. Se todas as buscas de uma habilidade falharem, registre a habilidade em `erros` e continue com as demais.
4. Se nenhum material for encontrado para nenhuma habilidade, retorne `estado: erro`.
5. Se houver resultados parciais, retorne `estado: sucesso`, mostre os resultados disponiveis e liste falhas em `erros`.
