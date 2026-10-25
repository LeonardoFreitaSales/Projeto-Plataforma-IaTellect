# Contexto do projeto — Plataforma v1.0 de testes

## Estrutura

- `index.html` e `app.js`: interface e interações no navegador.
- `server.py`: servidor HTTP e API em Python, usando somente a biblioteca padrão.
- `iniciar.bat`: inicia a cópia na porta 3006.
- `data/database.json`: dados exclusivos da cópia de testes; preserve o arquivo.
- `README.md`: execução, rotas e limites conhecidos.
- `server.js`: versão Node legada mantida como referência, não usada pelo iniciador atual.

## Execução

Execute `iniciar.bat` e acesse `http://localhost:3006`. No PowerShell, pode executar `$env:PORT=3006` e depois `python server.py`. Não abra o HTML por `file://`, pois o painel usa a API do servidor.

## Regras de manutenção

- Mantenha HTML, CSS e JavaScript do navegador sem conversões para Python.
- Não invente regras acadêmicas nem dados.
- Preserve o `data/database.json` desta cópia e não o misture com o banco comercial.
- Consulte o README antes de alterar endpoints ou formatos da API.
- Não altere outras versões como parte de uma mudança limitada a esta cópia.