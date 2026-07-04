# ADR — Linhagem e invalidação de artefatos

## Status

Aceito

## Contexto

O sistema gera artefatos derivados a partir de perfil, currículo, vaga, match e foco. Esses artefatos não podem ser tratados como atuais apenas porque o arquivo existe.

## Decisão

Centralizar um grafo de dependências que define quais artefatos devem ser invalidados, marcados como obsoletos ou recalculados quando uma entrada muda.

## Grafo inicial

- perfil → vagas, cursos, match, reconciliação, tailoring, PDI e entrevista
- currículo → match, reconciliação, tailoring, PDI e entrevista
- vaga → match, reconciliação, tailoring, PDI e entrevista
- match/foco → reconciliação, tailoring, PDI e entrevista
- tailoring → PDI

## Consequências

- Routers não devem manter listas próprias de invalidação.
- A próxima etapa deve criar um registro central de artefatos.
- O frontend deve deixar de considerar uma etapa concluída apenas pela existência de arquivo.
