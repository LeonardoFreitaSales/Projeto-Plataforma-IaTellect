# Assistente de uso de IA — protótipo isolado

Esta pasta é uma cópia independente da Plataforma v3.0 de testes. A v3.0 original não foi alterada.

## O que o protótipo faz

- O aluno escolhe uma disciplina, depois o tipo de atividade e então a atividade cadastrada desse tipo.
- Mostra o status, as condições, os detalhes e a fonte registrada.
- Faz um questionário de autorreflexão com escolhas e campos opcionais.
- Salva as respostas no banco SQLite isolado desta cópia; o professor responsável e administradores podem consultá-las.
- Não envia respostas para serviços externos.
- Não detecta autoria nem comprova se o aluno usou IA; o resultado é informativo e não substitui o professor.
- Nesta etapa, o assistente é guiado por regras e textos cadastrados. Não há modelo generativo conectado.

## Como iniciar

1. Execute `iniciar.bat`.
2. Abra `http://localhost:3005`.
3. No primeiro acesso ao banco novo, use `admin` e a senha inicial mostrada no terminal (`assistente-teste-123`, salvo se a variável `ADMIN_PASSWORD` já estiver definida).
4. Cadastre disciplinas, políticas e um professor para experimentar o fluxo com diferentes perfis.

O banco exclusivo desta cópia é `data/Banco de Dados SQLite.db`, dentro desta pasta; ele é um arquivo diferente do banco de `Testes da Plataforma/Plataforma v3.0 - Testes`. Nenhum banco da v3.0 é aberto por este servidor. O servidor ignora a variável externa `DATA_DIR`, recusa atalhos na pasta do banco e sempre usa o arquivo dentro desta pasta. O login está integrado à tela e é servido pelo servidor desta pasta.

## Arquivos

- `index.html`: interface, estilos e scripts do protótipo.
- `server.py`: API, autenticação, permissões, SQLite, assistente e consulta protegida das reflexões.
- `schema_Banco_de_Dados_SQLite.sql`: estrutura do banco.
- `iniciar.bat`: início local isolado na porta 3005.
- `test_permissoes.py`: verificações existentes do servidor, usando banco temporário.

## Limites e privacidade

As respostas são autodeclarações; não comprovam autoria, não confirmam os fatos nem determinam infrações. Cada professor consulta somente reflexões das disciplinas sob sua responsabilidade; administradores podem consultar todas. Alunos não têm acesso à lista de respostas de outras pessoas. A tabela de reflexões é criada automaticamente no banco desta pasta.

## Limite e próxima etapa

Para conectar ChatGPT, Claude ou outro modelo, ainda é preciso escolher o provedor e decidir quais dados podem ser enviados a ele. A chave deverá ficar em variável segura no servidor; não deve ser colocada no HTML nem no Git. A configuração de um provedor pode gerar custos e exige revisar a privacidade antes de enviar dados de alunos.
