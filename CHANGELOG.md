# Changelog do IaTellect

Histórico consultado em 21/11/2026, do primeiro commit até `2b6f929` na `origin/main`. São 77 commits, incluindo seis merges de pull requests. A coluna **Histórico** identifica os 45 commits da linha principal pelo primeiro pai e os 32 que chegaram pelas branches integradas. A data é a de autoria de cada commit. Cada hash abre o diff no GitHub.

## Estado ao final deste histórico

A v4 serve `prototipo-ux/index.html` para login e painel. A interface consulta a API Python, e o SQLite local guarda os dados. A suíte passou de 104 para 117 verificações. Os experimentos com Turso e Vercel e os dados simulados do protótipo aparecem abaixo nas etapas em que fizeram parte do projeto.

## Primeiros protótipos e documentação

| Data | Commit | Histórico | Mudança |
|---|---|---|---|
| 2026-10-25 | [332b249](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/332b249bb25ead4b7cdab1c648edaa1ba17dc874) | Principal | Reuniu as primeiras telas de acesso, os painéis de teste e seus servidores em um repositório. |
| 2026-10-25 | [92020aa](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/92020aa65857b5a0b4436999490cbcaffc150aa4) | Principal | Removeu comentários de `plataforma_terminal.py`, simplificando a leitura do protótipo de terminal. |
| 2026-10-25 | [5503eb7](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/5503eb7f70e32c78b35a0a5e4a80471c77de4a9c) | Principal | Atualizou a tela de acesso v2 e incluiu servidor Python e inicializador para Windows. |
| 2026-10-26 | [39fadf9](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/39fadf9c9367cabc927c802cd32f6ef5346ee669) | Principal | Removeu o changelog específico da primeira tela de login. |
| 2026-10-26 | [608fe7f](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/608fe7f64253f5ee4df0615d7666c20e3e9ed9cc) | Principal | Adicionou a experiência de login com assistente em `login-assistente.html`. |
| 2026-10-26 | [3a22184](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/3a22184d0735238fa18002f57fdbf28d9b497c6c) | Principal | Removeu a antiga página de cadastro da tela de login v1. |
| 2026-10-26 | [720c5e8](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/720c5e8910f190131c3a0447cd9502566e2b2659) | Principal | Atualizou o HTML de acesso v2 e adicionou o inicializador `iniciar-acesso-python.bat`. |
| 2026-10-26 | [6f8b6f8](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/6f8b6f8a0a11ee11e795dd2c539b3a92f74947a9) | Principal | Retirou o inicializador genérico da tela de login v2 após a entrada do inicializador específico. |
| 2026-10-26 | [acc4d87](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/acc4d87f79eb4ea35c07358bcad3660399f1afb1) | Principal | Removeu o README local do painel de testes v2. |
| 2026-10-26 | [3c7bedb](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/3c7bedbe74f7679b4963caffc83e6e522e89cf39) | Principal | Atualizou o painel HTML, o servidor Python e as regras de arquivos ignorados dos testes v2. |
| 2026-10-30 | [51b7983](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/51b79837c812c540ae3f0fa3664024e16a1b00b8) | Principal | Organizou as versões de teste, telas de login e documentação em pastas e incluiu o backlog do projeto. |
| 2026-11-07 | [3cfe604](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/3cfe60413928e2b45f3370900cc147f76257d74c) | Principal | Registrou a v3 de testes com painel, servidor, esquema SQLite, teste de permissões e guias de banco e hospedagem. |
| 2026-11-07 | [bedc22a](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/bedc22a8bbe0b8a3f2359cd2444ad0ee6009b82a) | Principal | Retirou da v3 o antigo guia de banco chamado `LEIA-ME_Banco_de_Dados_SQLite.txt`. |
| 2026-11-07 | [55357db](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/55357dbd2efd2ab412209b0edc5ff68d849bf7a1) | Principal | Removeu a versão anterior do PDF de documentação geral. |
| 2026-11-07 | [83fb42c](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/83fb42cf9b670f6245bf78444152109248c94096) | Principal | Adicionou o PDF revisado da documentação geral do projeto. |
| 2026-11-07 | [7d20372](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/7d203724265b61aa87f4f656f195e1d1fe56efdf) | Principal | Atualizou a apresentação do projeto no README da raiz. |
| 2026-11-07 | [57c951b](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/57c951b88c7fd6f72266ffb7f5bfd7fbf6eb6d66) | Principal | Ampliou os padrões do Git para ignorar arquivos locais. |

## Primeira entrega da plataforma v4

| Data | Commit | Histórico | Mudança |
|---|---|---|---|
| 2026-11-13 | [e75429c](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/e75429c18138255b1e5d41dfb540e59858718f62) | Principal | Definiu exclusões para bancos, credenciais e arquivos gerados da v4. |
| 2026-11-13 | [2875363](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/2875363941eaf509059d50123849a1d0f7933c43) | Principal | Criou o esquema SQLite que representa os dados da plataforma. |
| 2026-11-13 | [9d46fb0](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/9d46fb074f2b622a7af655ea0f66f90b70b24193) | Principal | Implementou a API da v4 com autenticação e autorização por perfil. |
| 2026-11-13 | [2836519](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/2836519896aa78e2703d9e9c5ca7abfa8bd8de10) | Principal | Criou a interface para entrar com senha e solicitar cadastro. |
| 2026-11-13 | [10eab31](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/10eab31a5f7cd5242989282c0d9002a986ad460f) | Principal | Adicionou o painel de gestão e diálogos acessíveis para as operações da plataforma. |
| 2026-11-13 | [442502c](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/442502cb111801fab48af2a08ba14bf2b436925e) | Principal | Introduziu 104 verificações de permissões e sessões para detectar regressões. |
| 2026-11-13 | [2e47d38](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/2e47d38200a643ef5fd7e393047d5bdf6eb551d1) | Principal | Incluiu o inicializador da v4 para Windows. |
| 2026-11-13 | [093ca9c](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/093ca9c285dc9e07cfd0a0877378be840973078b) | Principal | Documentou execução, migração de dados e opções de hospedagem. |
| 2026-11-13 | [77f6a78](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/77f6a78216653308678411938338675358628dd2) | Principal | Registrou os resultados da revisão visual e da suíte de testes. |
| 2026-11-14 | [dc98583](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/dc98583cfba0bb4d869f87b429bb5f5334a3eeca) | Principal | Corrigiu a apresentação dos indicadores de status que quebravam no painel. |
| 2026-11-14 | [7bf5bce](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/7bf5bce9d5051d5d6eb1e473f0efcbc7cee9bd4b) | Principal | Removeu da v4 o arquivo independente de revisão `REVISAO.md`. |

## Experimentos de hospedagem com Turso e Vercel

| Data | Commit | Histórico | Mudança |
|---|---|---|---|
| 2026-11-14 | [66c2295](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/66c2295f03e05a485753a72818904d8b4f3af1ed) | Principal | Adicionou integração com Turso e configuração para executar a v4 na Vercel. |
| 2026-11-16 | [de729cf](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/de729cfb2d94bb9c3ffa91be069f789db8b6b4d2) | Principal | Criou o ponto de entrada Python usado pela Vercel para receber requisições. |
| 2026-11-17 | [700247f](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/700247f0ea993c41c1e41302df478a9d3aa046fc) | Principal | Restringiu o roteamento da Vercel para impedir a exposição de arquivos internos. |
| 2026-11-17 | [236e17f](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/236e17f8f00c14aaa62c69d1905f7932a020e5a5) | Principal | Ajustou a inicialização do Python e passou a preparar o banco durante a requisição. |
| 2026-11-17 | [098c020](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/098c020599e741b93e2e3469cebdc8c6e9e2065b) | Principal | Adaptou as transações remotas do Turso para funcionar por HTTPS. |
| 2026-11-17 | [2b5565e](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/2b5565e8d55778554e5ca1b03f4f250ece994111) | Principal | Dividiu a aplicação do esquema em comandos SQL individuais para o banco remoto. |
| 2026-11-17 | [5ffc613](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/5ffc6131b010b39bbb6a5f842e961fa6fda73424) | Principal | Acrescentou diagnóstico para identificar comandos SQL incompatíveis no servidor. |
| 2026-11-17 | [7499ae9](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/7499ae9129f94e305dcf5c1ccbf1a0235eacff90) | Principal | Limitou a leitura ou alteração de `PRAGMA user_version` ao SQLite local. |
| 2026-11-17 | [2e7e28a](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/2e7e28a292e16dc4a3642fb0cee056d71a7c0b72) | Principal | Retirou o cliente WebSocket e documentou o funcionamento do deploy por HTTPS. |

## Protótipo UX e identidade visual

| Data | Commit | Histórico | Mudança |
|---|---|---|---|
| 2026-11-18 | [11e5ef7](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/11e5ef7997f25f12f303f021d5af651a9b821a5b) | Branch integrada | Criou o HTML navegável do protótipo que depois se tornaria o front-end da v4. |
| 2026-11-18 | [a4998fd](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/a4998fd83751e0c8fa7f9955d8835403947b1877) | Branch integrada | Definiu a identidade visual e adaptou a organização das telas para diferentes tamanhos. |
| 2026-11-18 | [9d7db9d](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/9d7db9d3ebb108184db982df3429c73290f55907) | Branch integrada | Adicionou ao protótipo o fluxo de entrada e os atalhos de demonstração por perfil. |
| 2026-11-18 | [15e6607](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/15e66072b4f083fbd3a5540ae6a0a179fe1be21d) | Branch integrada | Diferenciou o painel inicial de administrador, professor e aluno no protótipo. |
| 2026-11-18 | [d19201a](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/d19201aa20b79e771535ff2fd4fc40103f3f1a4c) | Branch integrada | Redesenhou a lista de disciplinas e a consulta às políticas de cada atividade. |
| 2026-11-18 | [59441e3](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/59441e393963473e091a44acbc6661facedb8c1f) | Branch integrada | Introduziu no protótipo a publicação guiada de políticas em etapas. |
| 2026-11-18 | [9385410](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/93854104660d6d06da7e27e13d915bf5e417c6a4) | Branch integrada | Revisou a interface de análise e decisão sobre matrículas. |
| 2026-11-18 | [13369ea](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/13369ea3958b81df10da3e1fe96a34d449a5bd98) | Branch integrada | Criou telas para revisar a clareza das políticas e orientar o uso responsável de IA. |
| 2026-11-18 | [72c864f](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/72c864f969590ddd1ed1e4f3139c2faf7222dd6e) | Branch integrada | Adaptou a assistente Lia ao contexto da tela e às fontes das orientações. |
| 2026-11-18 | [3bcf321](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/3bcf32188de62744e4aa3bb3f84bba224e1f7df3) | Branch integrada | Organizou a consulta e a gestão de comunicados por perfil no protótipo. |
| 2026-11-18 | [7f683e0](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/7f683e011ee774f57096b01bf60e88c19547e128) | Branch integrada | Adicionou filtros de auditoria, delimitação dos registros visíveis e exportação do histórico no protótipo. |
| 2026-11-18 | [8662d2e](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/8662d2e24e0cc4578eb454e58711f590e8f5a5cc) | Branch integrada | Modelou no protótipo a gestão de contas e a atribuição de escopos de acesso. |
| 2026-11-18 | [b14a66b](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/b14a66b4605766ad9f976b4356fc147efcb4ea98) | Branch integrada | Criou na interface de demonstração a gestão de turmas e dos vínculos com disciplinas. |
| 2026-11-18 | [8ebcac2](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/8ebcac2b0210d76c011bae3a20b46875b60df8b6) | Branch integrada | Completou as telas de cadastro de disciplinas e atribuição de responsáveis. |
| 2026-11-18 | [2dea715](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/2dea715c089bc4c41a2f4d00402ef0cccbd3dc5d) | Branch integrada | Revisou foco de teclado, semântica dos elementos e preferências de movimento. |
| 2026-11-20 | [a3023dd](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/a3023dd60b984b6e7ced642455beb93bf1828855) | Branch integrada | Redesenhou o README para apresentar visualmente a identidade do IaTellect. |
| 2026-11-20 | [89e2f0c](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/89e2f0c09bfbe627776938d0141f23f3cb40549d) | Branch integrada | Consolidou o guia de identidade para alinhar documentação e materiais de comunicação. |

## Modularização do backend

| Data | Commit | Histórico | Mudança |
|---|---|---|---|
| 2026-11-20 | [45aa3d5](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/45aa3d58f253eb69a8f36351c83ee98019e01d33) | Branch integrada | Extraiu de `server.py` as constantes de configuração e as funções utilitárias. |
| 2026-11-20 | [e43cef2](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/e43cef29403f1b95cf77fee69ebbfdcb8763532e) | Branch integrada | Separou a lógica de segurança e o controle de tentativas de acesso. |
| 2026-11-20 | [2e1b2c9](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/2e1b2c94bac32dc012ea0963b9e4d6d171b49f84) | Branch integrada | Isolou a conexão, a preparação e a inicialização do banco de dados. |
| 2026-11-20 | [0f1b4c3](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/0f1b4c3ef03fcc02830d7b3096d982c6826588f7) | Branch integrada | Moveu o registro das alterações para um módulo de auditoria. |
| 2026-11-20 | [6ef48df](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/6ef48df2d6bba810705032678f99e354bdbdd361) | Branch integrada | Agrupou as regras de autorização em um módulo de permissões. |
| 2026-11-20 | [e7173a9](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/e7173a9f9aba967c110d8120f0e2606818b709d5) | Branch integrada | Extraiu o contexto usado para processar cada requisição. |
| 2026-11-20 | [011b6a5](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/011b6a5279cd7be4b17bf95c350b19960d47f72b) | Branch integrada | Separou os endpoints da API por domínio, como autenticação, políticas, turmas e usuários. |
| 2026-11-20 | [89ada5d](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/89ada5dfd6bac0b154e6d3dc8c049799c951027e) | Branch integrada | Separou o tratamento HTTP da inicialização local e preservou `server.py` como entrada. |
| 2026-11-20 | [0c4ca7b](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/0c4ca7b858e4ccaf29b64063ad520f55fed61cfa) | Branch integrada | Acrescentou testes para o painel e a consulta de políticas conforme o escopo do professor. |
| 2026-11-20 | [cf68a5b](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/cf68a5b39d2f34f9216857912b81f892e268ff42) | Principal | Integrou à main a modularização do backend e os novos testes do professor pelo PR #6. |

## Organização da v4 e execução local

| Data | Commit | Histórico | Mudança |
|---|---|---|---|
| 2026-11-21 | [f4cffc6](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/f4cffc6ec49602177e33231ca7f62f3a85288e0c) | Branch integrada | Organizou a interface, o esquema SQL e os documentos da v4 em diretórios próprios. |
| 2026-11-21 | [805961e](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/805961ec68ca4e1d20dc1c03a251755e2d43794e) | Principal | Revisou o servidor histórico da pasta v0.5, incluindo o tratamento de JSON corrompido e dos arquivos estáticos. |
| 2026-11-21 | [541cb85](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/541cb856338163f0e0b7566773ad223bcc4a7dac) | Principal | Integrou à main a organização da v4 pelo PR #7. |
| 2026-11-21 | [f2a66b1](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/f2a66b100aab98ca13e0686b3dbe4eddc4ca552f) | Principal | Removeu da pasta da v4 o manifesto de dependências Python usado nessa fase. |
| 2026-11-21 | [437fa88](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/437fa88cb7cded62e89acebf5b325196ccea0ac2) | Principal | Removeu a fixação da versão do Python em `.python-version` na v4. |
| 2026-11-21 | [d50b6f2](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/d50b6f2f1feec71f6ade80311554e911cec05adc) | Branch integrada | Retirou a integração de deploy da v4 e concentrou a execução no servidor Python com SQLite local. |
| 2026-11-21 | [3a34444](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/3a3444428edb10b569ea3c7f8873156a84701a90) | Principal | Integrou à main o retorno à execução local pelo PR #8. |

## Integração da documentação e do front-end final

| Data | Commit | Histórico | Mudança |
|---|---|---|---|
| 2026-11-21 | [89a75ac](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/89a75acfd7af2154080350ce8cb19c86d8ef2d39) | Branch integrada | Esclareceu na documentação como executar a v4 e como experimentar o protótipo visual, então separados. |
| 2026-11-21 | [ae0f7c1](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/ae0f7c103c567256e4fbfdb42f16870d10c59bd0) | Branch integrada | Integrou pelo PR #5 o README redesenhado e o guia de identidade visual. |
| 2026-11-21 | [4c36228](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/4c36228d1c596f198a20d4efa87feddd01d2adf5) | Principal | Integrou pelo PR #4 o protótipo UX e suas telas demonstrativas. |
| 2026-11-21 | [9475bf2](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/9475bf2d6a36bf37a39d2621c174e0a3b3c8552e) | Branch integrada | Aplicou a identidade do protótipo às páginas que a v4 já utilizava. Foi a etapa intermediária da integração visual. |
| 2026-11-21 | [fcc78bc](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/fcc78bc7f53eab6242294ed37d500a038c4f36ec) | Branch integrada | Passou a servir o próprio HTML de `prototipo-ux/` no acesso e no painel. Conectou os fluxos à API local, retirou as páginas substituídas e acrescentou verificações para as rotas da interface. |
| 2026-11-21 | [2b6f929](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/commit/2b6f929dfc6c9ddacbcde33454628db0125696d7) | Principal | Integrou o front-end UX conectado ao backend na main pelo PR #9. A árvore resultante corresponde ao commit de integração `fcc78bc`. |

## [PR #10](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/pull/10) — Reorganização do repositório

O servidor e os testes passaram para backend/, a interface para frontend/ e os dados locais para data/ na raiz. O cookie passou a se chamar iatellect_sessao. Entre novamente após atualizar. Com o servidor encerrado, instalações existentes devem transferir a pasta de dados anterior para data/ antes de iniciar a nova versão.

- `33c98b2` — Moveu o servidor, o esquema SQL e a suíte de testes para backend/.
- `07712ae` — Reuniu a interface, seus módulos e imagens em frontend/.
- `c09a515` — Organizou identidade visual, referências, backlog e documentação técnica em docs/.
- `e3cda70` — Transferiu os experimentos anteriores para archive/ e documentou sua finalidade.
- `12b7ae8` — Corrigiu os caminhos de execução, dos dados e dos arquivos estáticos e adotou o cookie de sessão neutro.

## 21/11/2026 — Execução local, testes e navegação

- `fc8e431` — O servidor passou a escutar em `127.0.0.1` por padrão e a informar a porta aberta na inicialização. A variável `HOST` permite escolher outro endereço.
- `1e8b3e0` — Cada execução da suíte de permissões usa uma porta livre. O GitHub Actions passou a executar a suíte nos pull requests.
- `65d6c6d` — A interface passou a buscar os dados necessários para cada tela. A tela de uso responsável abre sem fazer requisições à API.

As mudanças entraram na `main` pelo [PR #11](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/pull/11), no commit `f34dcd8`.

## [PR #12](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/pull/12) — Registro das mudanças do PR #11

- `f187ecc` — Documentou a inicialização local, o isolamento dos testes por porta e o carregamento de dados por tela.

## [PR #13](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/pull/13) — Teste de matrícula no navegador

- `e4b163e` — Automatizou o cadastro do aluno, a aprovação pelo professor e a consulta à política pelo aluno após a aprovação.
- `6817a2e` — Incluiu o teste de navegador no GitHub Actions e documentou sua execução local.
- `c29d165` — Ajustou o job para usar o Chrome disponível no runner do GitHub.

## [PR #14](https://github.com/LeonardoFreitaSales/Projeto-Plataforma-IaTellect/pull/14) — Segurança do backend e distribuição

- `624fee7` — Passou a exigir uma origem permitida nas escritas da API e a considerar o IP encaminhado apenas quando a conexão vem de um proxy autorizado. Acrescentou regras de permissões do navegador e testes para os novos controles.
- `67952ed` — Passou a renderizar os avisos de sucesso e erro como texto, preservando a apresentação de caracteres especiais.
- `dd7c5aa` — Documentou a configuração por variáveis de ambiente, a geração do ZIP, o relato de problemas de segurança e as decisões pendentes sobre retenção de dados.
- `docs: exigir changelog em todos os pull requests` — Registrou as mudanças por commit e adicionou um lembrete no formulário de PR e uma verificação automática de atualização do changelog.

## Lia — Consulta local de políticas

- `feat: integrar a Lia à consulta de políticas` — O chat pesquisa no backend as políticas visíveis ao usuário, incluindo condições e detalhes. Exibe a fonte e oferece escolhas quando há várias correspondências. A suíte cobre busca, autenticação e isolamento entre perfis.
- A Lia numera os resultados da busca e aceita a escolha pelo teclado. Limpar a conversa descarta as opções anteriores. O teste de navegador cobre a seleção e a recuperação após um número inválido.
- `docs: registrar avaliação da busca da Lia` — Documentou cinco perguntas testadas no navegador e os limites observados em continuações e reformulações.
- `feat: manter contexto da Lia e oferecer reformulação com Groq` — Continua uma busca na disciplina escolhida, descarta o contexto ao limpar o chat e permite solicitar termos de busca à Groq quando a consulta local não encontra políticas.
- `feat: orientar a navegação da Lia e limitar o escopo` — Reconhece referências à mesma matéria, oferece atalhos conforme o perfil e delimita perguntas enviadas para reformulação.
- O limite de reformulações por usuário também é aplicado entre requisições simultâneas.

## Revisão da documentação

- `docs: corrigir link do guia e identificar referência visual` — Corrige o acesso ao README pelo guia do banco e dá um nome descritivo à ilustração da lâmpada sobre o livro.

## Lia — acessibilidade e consultas acadêmicas

- `feat: consolidar consultas acadêmicas e interface acessível da Lia` — Integra busca autorizada de matérias e turmas, contexto da disciplina, perguntas sugeridas, contraste, menu ajustável por teclado e arraste, gerenciamento de foco e estados de envio. Inclui os testes de regressão das quatro etapas.

## Guia de acesso local

- Documenta como abrir e atualizar cópias da main e do piloto fictício no Git Bash.
