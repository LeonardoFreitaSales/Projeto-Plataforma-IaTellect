# Plataforma v1.0 — testes

Esta cópia usa `server.py` em Python, sem pacotes externos. Execute `iniciar.bat` e abra <http://localhost:3006/>. Não abra `index.html` diretamente: a interface precisa da API.

`server.js` permanece como referência da versão Node anterior e não é usado pelo iniciador atual. O banco local `data/database.json` é criado pelo servidor se necessário; ele é ignorado pelo Git e não acompanha este repositório.

Esta é uma versão local de testes, sem autenticação segura nem configuração de produção.