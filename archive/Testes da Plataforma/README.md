# Plataforma de Gestão de Políticas Acadêmicas

## Tema e propósito do projeto

Este projeto é um protótipo de uma plataforma para organizar políticas acadêmicas sobre o uso de inteligência artificial (IA) em atividades de disciplinas. A ideia central é permitir que a comunidade consulte e mantenha orientações que indiquem se o uso de IA é **permitido**, **permitido com restrições** ou **proibido** em cada contexto acadêmico.

A plataforma reúne informações por disciplina, permite consultar políticas aplicáveis a atividades e inclui recursos de apoio à gestão, como comunicados e histórico. As pastas numeradas registram a evolução dos protótipos; cada uma é uma versão de teste independente.

## Recursos e tecnologias utilizados

- **HTML** para a estrutura e o conteúdo das telas.
- **CSS** para cores, tipografia, layout responsivo e apresentação visual. Nas versões iniciais está em `style.css`; nas versões mais recentes parte ou todo o estilo fica embutido no HTML.
- **JavaScript** no navegador para interação, formulários, navegação, filtros e comunicação com a API.
- **Python** para o servidor local e as rotas da API. As versões iniciais usam módulos da biblioteca padrão, como `http.server`.
- **Node.js** como implementação alternativa do servidor na versão 1.0 (`server.js`).
- **JSON** como formato de armazenamento nos protótipos anteriores à v3.0 e como formato de troca de dados entre navegador e API.
- **SQLite** na v3.0 para armazenar os dados em um banco relacional local. A biblioteca `sqlite3` faz parte do Python; não é necessário instalar um servidor de banco separado.
- **Arquivos `.bat`** para iniciar cada protótipo no Windows com suas configurações de execução.

## Pastas e finalidade

### `Plataforma v0.0 - Testes`

Primeiro protótipo funcional e enxuto. Apresenta a proposta de políticas de IA por disciplina e os estados permitido, restrito e proibido. Usa `index.html`, `style.css` e `app.js` na interface, com um servidor Python simples (`server.py`) que disponibiliza os arquivos e salva os dados em `data/database.json`.

**Finalidade:** experimentar o fluxo e os conceitos básicos antes de expandir a interface e as funcionalidades.

### `Plataforma v0.5 - Testes`

Evolução da primeira versão, com uma estrutura de aplicação mais completa, menu de navegação e áreas adicionais, incluindo a publicação de comunicados. Mantém os arquivos separados de HTML, CSS, JavaScript e servidor Python, e continua usando JSON para persistência.

**Finalidade:** testar a organização da navegação e ampliar o conjunto de tarefas que o protótipo pode representar.

### `Plataforma v1.0 - Testes`

Versão mais estruturada da plataforma. A interface e o servidor se comunicam por rotas de API; há arquivos de dados em `data`. A pasta contém `server.py` e também `server.js`, duas implementações de servidor disponíveis no protótipo. O armazenamento continua sendo `data/database.json`.

**Finalidade:** consolidar a aplicação com uma API e testar a gestão de disciplinas, políticas e informações associadas.

### `Plataforma v2.0 - Testes`

Protótipo visual e funcional mais completo. Inclui o painel Intellecta AI, telas e ações de gestão, consultas sobre o uso de IA, comunicados, histórico e opções de acessibilidade. O servidor Python atende a interface pela API e persiste as coleções no arquivo JSON dentro de `data`.

**Finalidade:** testar a experiência integrada do painel e amadurecer os fluxos de consulta e administração antes da troca da camada de armazenamento.

### `Plataforma v3.0 - Testes`

Versão derivada da interface da v2.0 com o servidor adaptado para SQLite. Os dados de disciplinas, políticas, comunicados e histórico ficam em `data/Banco de Dados SQLite.db`. O arquivo `schema_Banco_de_Dados_SQLite.sql` descreve as tabelas e suas relações; `server.py` usa `sqlite3` para ler e gravar o banco. O JSON de dados não é necessário para executar esta versão.

**Finalidade:** substituir o armazenamento em arquivo JSON pelo banco SQLite sem alterar o fluxo principal da interface.

## Como executar a versão atual

1. Abra a pasta `Plataforma v3.0 - Testes`.
2. Execute `iniciar.bat` em um computador com Python 3 instalado.
3. Acesse `http://localhost:3002` no navegador.

O `iniciar.bat` chama `server.py`, que usa o banco localizado na pasta `data`. O arquivo SQLite é o armazenamento persistente da v3.0. A API ainda recebe e devolve JSON para a comunicação com o navegador; isso não significa que os dados sejam gravados em arquivos JSON.

## Observação sobre as versões

As pastas v0.0 a v3.0 são protótipos de teste e preservam etapas diferentes do desenvolvimento. Para executar a versão mais recente, use a pasta v3.0. Os dados das versões antigas em JSON não são compartilhados automaticamente com as versões seguintes.
