# Plataforma v1.0 — cópia de testes

## Como iniciar

Requer Python 3; não precisa instalar pacotes. Execute `iniciar.bat` e abra <http://localhost:3006/>. Mantenha a janela do servidor aberta. Esta cópia usa a porta 3006 para não conflitar com a versão comercial v2.0 (3001), a v2.0 de testes (3002), a v0.0 (3003), a v0.5 (3004) e a v1.0 comercial (3005).

No PowerShell, nesta pasta:

```powershell
$env:PORT=3006
python server.py
```

Não abra `index.html` diretamente como arquivo: a interface precisa da API local.

## Dados e API

O banco fica em `data/database.json` e é exclusivo desta cópia. Preserve-o durante verificações. O servidor oferece as rotas de disciplinas, políticas, comunicados, histórico, painel e consulta por atividade; consulte `server.py` e os exemplos deste README para detalhes. As regras e respostas mantêm o contrato usado por `app.js`.

Esta é uma cópia local de testes, sem autenticação segura nem suporte para implantação pública.

## Arquivos antigos

`server.js` foi mantido como referência histórica e não é usado pelo `iniciar.bat`. O servidor ativo desta cópia é `server.py`.