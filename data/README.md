# Dados locais do agente

Esta pasta guarda arquivos Markdown gerados durante o uso do agente, como perfil, resultados de vagas, analises e planos.

Esses arquivos sao estado local de cada pessoa e nao devem ser versionados, porque podem conter dados pessoais e variam por usuario, cidade e sessao.

Se precisar documentar o formato esperado de algum arquivo, crie um `*.example.md` nesta pasta.

## Allowlist e sanitização

Somente estes arquivos podem ser versionados em `data/`:

1. `data/README.md`;
2. `data/*.example.md`, diretamente na raiz e com conteúdo sanitizado.

Todo conteúdo sob `data/sessions/` é bloqueado porque representa estado real de
execução e pode conter perfil, currículo, vagas, notas e histórico da pessoa.

Um exemplo sanitizado deve:

1. usar nomes e valores claramente fictícios;
2. remover currículos, e-mails, telefones, URLs privadas e identificadores reais;
3. nunca conter chave, token, senha, private key ou credencial;
4. usar marcadores como `[valor de exemplo]` quando o formato for suficiente.

Antes do commit, execute na raiz do projeto:

```bash
python scripts/validate_data_guard.py
```

Para validar o comportamento do próprio guard:

```bash
python -m unittest discover -s scripts/tests -p "test_*.py" -v
```

## Política de sessões e legado

A raiz de `data/` não é mais um diretório de sessão. Os artefatos de runtime
ficam em `data/sessions/{session_id}/`, e as chamadas sem header `X-Session-Id`
usam a sessão default em `data/sessions/_default/`.

Os arquivos Markdown soltos diretamente em `data/*.md` são considerados LEGADO:
não são consumidos automaticamente por nenhuma sessão (é preciso regerá-los
dentro da sessão). Nenhum arquivo legado é apagado automaticamente. A migração é
manual e opcional — se quiser reaproveitar um artefato antigo, mova-o para
`data/sessions/_default/`.

