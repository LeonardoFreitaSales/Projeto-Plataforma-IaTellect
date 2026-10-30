# Contexto — Plataforma v1.0 de testes

- `index.html` e `app.js`: interface do navegador.
- `server.py`: servidor Python e API ativa.
- `server.js`: referência legada; o `iniciar.bat` executa Python.
- `iniciar.bat`: inicia na porta 3006.
- `data/database.json`: banco local criado pelo servidor quando necessário; não é versionado.

Execute `iniciar.bat` e acesse `http://localhost:3006`. Preserve os dados locais. Mantenha compatibilidade entre a interface e as rotas da API. Não acrescente regras acadêmicas sem definição do usuário.