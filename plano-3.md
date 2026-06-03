# Aula 3: Curator - Agente de Trilha de Aprendizado Acessivel

## Visao Geral

Este documento define o Curator, agente acionado pela opcao B do menu. O Curator analisa lacunas de habilidades vindas das vagas e monta uma trilha de aprendizado que respeita a dor do usuario: pouco tempo, custo sensivel e necessidade de evoluir rapido para se candidatar melhor.

O foco nao e vender uma plataforma especifica. O foco e recomendar o melhor proximo passo para cada lacuna:

1. conteudo gratuito;
2. videos ou playlists no YouTube;
3. documentacao oficial;
4. cursos pagos acessiveis;
5. cursos premium quando forem claramente relevantes.

## Diretrizes para Modelos MoE

1. Sem instrucoes ambiguas. Cada etapa deve especificar exatamente o que fazer, qual ferramenta usar e qual formato de saida produzir.
2. Nunca use tabelas markdown. Use listas numeradas com pares chave-valor.
3. Todos os caminhos de arquivo devem ser relativos a raiz do projeto com prefixo `data/`.
4. Se uma busca falhar para uma habilidade, tente fallbacks e continue com as demais.
5. Nunca invente dados. Nomes, links, precos e duracoes devem vir da busca/scrape ou ser `Nao informado`.
6. O agente nao deve escrever scripts para implementar a persona. Ele personifica o papel conversacionalmente.

## Dor do Usuario

1. A pessoa encontra vagas, mas nao sabe quais lacunas estudar primeiro.
2. A pessoa pode nao ter dinheiro para assinar plataformas premium.
3. A pessoa precisa de um caminho curto e pratico, nao uma lista enorme.
4. A pessoa precisa entender a ordem de estudo para nao comecar pelo conteudo errado.
5. A pessoa precisa de links reais e confiaveis.

## Responsabilidade do Curator

1. Ler `data/job-search-results.md`.
2. Extrair habilidades faltantes.
3. Priorizar habilidades mais recorrentes nas vagas.
4. Ler `data/user-profile.md` para considerar area, nivel e objetivo.
5. Buscar materiais com Firecrawl.
6. Classificar por nivel e custo.
7. Retornar ate 8 recomendacoes com ordem sugerida.
8. Salvar a resposta final em `data/course-recommendations.md` via Maestro.

## Fontes Preferenciais

1. YouTube.
2. Documentacao oficial.
3. FreeCodeCamp.
4. Microsoft Learn.
5. Google Cloud Skills Boost.
6. Kaggle Learn.
7. MDN.
8. Alura.
9. Udemy.
10. Coursera.
11. edX.

## Fluxo de Execucao

1. O usuario seleciona B no menu.
2. O Maestro verifica se `data/job-search-results.md` existe e contem `habilidades_faltantes`.
3. Se nao houver vagas analisadas, o Maestro informa que a pessoa deve executar a opcao A primeiro.
4. O Maestro le `data/user-profile.md` e `data/job-search-results.md`.
5. O Maestro despacha o Curator com perfil e resultados de vagas.
6. O Curator extrai habilidades faltantes, deduplica e prioriza recorrencia.
7. Para cada habilidade priorizada, o Curator executa buscas:

```bash
firecrawl search "[habilidade] curso gratuito iniciante youtube portugues" --json
firecrawl search "[habilidade] tutorial gratuito projeto" --json
firecrawl search "[habilidade] documentacao oficial tutorial" --json
firecrawl search "[habilidade] curso barato alura udemy coursera [area]" --json
firecrawl search "[habilidade] curso tutorial projeto [area]" --json
```

8. O Curator classifica cada resultado:

1. `preco`: gratuito, acessivel, premium, certificado opcional ou Nao informado.
2. `nivel`: iniciante, intermediario ou avancado.
3. `plataforma`: YouTube, Alura, Udemy, Coursera, Documentacao Oficial ou outra.

9. O Curator seleciona ate 2 materiais por habilidade, tentando incluir:

1. uma opcao gratuita ou rapida;
2. uma opcao paga acessivel ou premium quando for relevante.

10. O Curator retorna o Envelope de Resposta.
11. O Maestro salva em `data/course-recommendations.md` com `Data da Busca`.
12. O Maestro exibe o resultado e volta ao menu.

## Envelope de Despacho

```text
## DESPACHO: CURATOR
### referencia_persona
[Conteudo completo de personas/curator.md]

### tarefa
Buscar materiais acessiveis para preencher lacunas de habilidades.

### perfil_usuario
[Conteudo de data/user-profile.md]

### contexto
Habilidades faltantes: [lista de data/job-search-results.md]
Area de interesse: [area]
Nivel de experiencia: [nivel]

### saida_esperada
Envelope de resposta com estado, resumo, dados, ordem sugerida e erros parciais.
```

## Envelope de Resposta

```text
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

Ordem sugerida:
1. [nome do primeiro material]
2. [nome do segundo material]

### erros
[Nenhum erro parcial ou lista numerada de falhas]
```

## Esquema de Dados

`data/course-recommendations.md` deve armazenar a ultima resposta do Curator:

```text
Data da Busca: [AAAA-MM-DD HH:MM]

## RESPOSTA: CURATOR
### estado
[sucesso | erro]

### resumo
[resumo]

### dados
[recomendacoes]

### erros
[erros]
```

## Tasks da Aula 3

1. Escrever `skills/course-analysis.md` com extracao de lacunas, busca hibrida, classificacao de custo/nivel, ordenacao e tratamento de erros.
2. Escrever `personas/curator.md` com papel, ferramentas, fontes, envelope e regras de erro.
3. Atualizar o Maestro para acionar o Curator na opcao B.
4. Salvar recomendacoes em `data/course-recommendations.md`.
5. Atualizar mock/testes para refletir recomendacoes acessiveis.
6. Validar build do frontend e sintaxe do backend.

## Criterios de Aceite

1. Se o usuario escolher B antes de buscar vagas, recebe uma mensagem clara pedindo a opcao A.
2. Se existirem lacunas, o Curator busca materiais reais com Firecrawl.
3. A resposta inclui `plataforma`, `preco`, `duracao`, `nivel`, `aborda_habilidade` e `link`.
4. A resposta prioriza gratuito/acessivel antes de premium.
5. Erros parciais nao derrubam o fluxo.
6. O Maestro retorna ao menu apos finalizar.
