# Dados locais do agente

Esta pasta guarda arquivos Markdown gerados durante o uso do agente, como perfil, resultados de vagas, analises e planos.

Esses arquivos sao estado local de cada pessoa e nao devem ser versionados, porque podem conter dados pessoais e variam por usuario, cidade e sessao.

Se precisar documentar o formato esperado de algum arquivo, crie um `*.example.md` nesta pasta.

## Política de sessões e legado

A raiz de `data/` não é mais um diretório de sessão. Os artefatos de runtime
ficam em `data/sessions/{session_id}/`, e as chamadas sem header `X-Session-Id`
usam a sessão default em `data/sessions/_default/`.

Os arquivos Markdown soltos diretamente em `data/*.md` são considerados LEGADO:
não são consumidos automaticamente por nenhuma sessão (é preciso regerá-los
dentro da sessão). Nenhum arquivo legado é apagado automaticamente. A migração é
manual e opcional — se quiser reaproveitar um artefato antigo, mova-o para
`data/sessions/_default/`.

