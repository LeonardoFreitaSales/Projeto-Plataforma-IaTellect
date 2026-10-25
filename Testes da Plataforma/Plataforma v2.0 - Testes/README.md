# Plataforma v2.0 — cópia de testes

Painel local para consultar e gerenciar políticas de uso de IA por disciplina. Esta cópia usa servidor Python e dados próprios para testes.

## Requisitos

- Python 3.
- Não é necessário instalar pacotes: o servidor usa a biblioteca padrão.

## Como iniciar

No Windows, execute `iniciar.bat` e abra <http://localhost:3002/>. Mantenha aberta a janela do servidor.

No PowerShell, nesta pasta:

```powershell
$env:PORT=3002
python server.py
```

O servidor usa a porta 3001 se `PORT` não estiver definida. Não abra `index.html` diretamente como `file://`, pois a interface precisa da API.

## Dados de teste

O banco fica em `data/database.json`. Se ele não existir, o servidor cria um banco vazio ao iniciar. Esse arquivo é ignorado pelo Git, mas os cadastros continuam gravados neste computador e persistem entre execuções. Para recomeçar um teste sem dados, faça uma cópia de segurança e limpe o banco conscientemente.

## API

A API local inclui consulta do painel e CRUD de disciplinas, políticas e comunicados, além de histórico e consulta de política por disciplina e atividade. Todas as rotas começam com `/api/`; os detalhes estão em `server.py`.

## Tela de acesso

No projeto completo, `/acesso.html` é servida a partir da pasta irmã `Site\Tela de Login\Tela de Login v2.0\acesso.html`. Essa tela não está incluída nesta cópia isolada; ao clonar somente este repositório, a rota pode não estar disponível até que o arquivo de acesso seja colocado no caminho correspondente.

A tela de acesso é um protótipo demonstrativo, não uma autenticação segura para produção.
