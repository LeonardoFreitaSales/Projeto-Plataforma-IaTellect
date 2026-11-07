# Protótipo-SI-IA

Protótipo de uma plataforma para organizar e consultar políticas acadêmicas sobre o uso de inteligência artificial (IA) em atividades de disciplinas. O sistema permite registrar regras por atividade e apoiar a comunicação entre administração, docentes e estudantes.

> **Status:** projeto experimental/em desenvolvimento. Não foi comprovada publicação institucional. Não utilize com dados reais de estudantes nem disponibilize publicamente como serviço sem revisar autenticação, privacidade, segurança, hospedagem e backups.

## O que o sistema faz

- Registra disciplinas e políticas com um dos seguintes estados: **permitido**, **permitido com restrições** ou **proibido**.

- Permite informar atividade, condições, detalhes e fonte da política.

- Organiza turmas, disciplinas vinculadas e solicitações de matrícula, que podem ficar pendentes, ser aprovadas ou recusadas.

- Apresenta ao estudante as disciplinas associadas às matrículas aprovadas e permite consultar as políticas cadastradas.

- Inclui um **assistente guiado** de consulta e autorreflexão. Nesta versão, o fluxo segue regras e textos cadastrados; **não utiliza modelo generativo**, não envia respostas a serviços externos e não detecta nem comprova autoria ou uso de IA.

- Oferece gestão de comunicados e histórico de operações.

- Possui controles de acesso por perfil e por disciplina no servidor, além de testes automatizados de permissões.

## Versão recomendada para experimentar

A implementação mais recente descrita neste repositório está em:

```
Desenvolvimento da Plataforma/Assistente de uso de IA - Protótipo/
```

Essa pasta é uma cópia isolada derivada da versão 3.0 de testes. Ela utiliza um banco SQLite e uma porta próprios; não compartilha automaticamente os dados com a pasta `Plataforma v3.0 - Testes` nem com o protótipo de terminal.

## Requisitos

- Windows para usar o arquivo de inicialização incluído (`iniciar.bat`).

- Python 3 instalado e disponível no `PATH`.

- Navegador web atualizado.

O servidor usa módulos da biblioteca padrão do Python, incluindo `sqlite3`; não é necessário instalar um servidor de banco de dados separado.

## Como executar localmente

1. Abra o Prompt de Comando.

1. Entre na pasta do protótipo isolado:

   ```
   cd "Desenvolvimento da Plataforma\Assistente de uso de IA - Protótipo"
   ```

1. **Antes da primeira execução**, configure uma senha forte para o administrador. Substitua o texto de exemplo por uma senha própria e não a inclua em arquivos versionados:

   ```
   set "ADMIN_PASSWORD=SUBSTITUA_POR_UMA_SENHA_FORTE"
   ```

1. Inicie o servidor:

   ```
   iniciar.bat
   ```

1. Abra no navegador:

   ```
   http://localhost:3005
   ```

O iniciador exibe informações de execução no terminal. Se `ADMIN_PASSWORD` não estiver configurada, o arquivo de inicialização utiliza uma credencial de demonstração. **Não use a configuração padrão fora de um teste local.** A variável deve ser definida antes da criação inicial do banco; mudar a variável depois não necessariamente altera a senha de uma conta já existente.

## Perfis de acesso

- **Administrador:** administra comunicados e usuários docentes e associa responsáveis às disciplinas.

- **Professor:** gerencia as disciplinas sob sua responsabilidade e as turmas permitidas; pode tratar matrículas e consultar as informações autorizadas para seu perfil.

- **Aluno:** solicita matrícula em uma turma. Depois da aprovação, pode consultar as disciplinas correspondentes e suas políticas.

### Limitação importante do login de estudante

No protótipo atual, o estudante entra usando o nome completo, sem senha. Portanto, o nome não comprova a identidade da pessoa: alguém que conheça o nome de outro estudante pode tentar se passar por ele. Essa limitação torna a versão inadequada para uso com dados reais ou para publicação institucional sem alteração do mecanismo de autenticação.

## Estrutura do repositório

```
BackLogs/                                      Planejamento e backlog do projeto
Desenvolvimento da Plataforma/
  Assistente de uso de IA - Protótipo/          Cópia isolada recomendada para teste
  Testes da Plataforma/                         Histórico dos protótipos v0.0 a v3.0
  Tela de Login/                                Experimentos visuais de login
  menu-acessibilidade/                          Componente de preferências de acessibilidade
  plataforma_terminal.py                        Protótipo de linha de comando
Referências para o projeto/                     Pesquisa e referências do projeto
```

Cada versão pode ter seu próprio servidor e armazenamento. O banco SQLite da versão isolada fica em `Desenvolvimento da Plataforma/Assistente de uso de IA - Protótipo/data/`; os bancos e arquivos de dados locais não são sincronizados automaticamente entre versões.

## Testes

A pasta da implementação isolada contém testes automatizados de autenticação, permissões, turmas e matrículas, visibilidade de dados e outras regras do servidor. Para executá-los, use:

```
cd "Desenvolvimento da Plataforma\Assistente de uso de IA - Protótipo"
python test_permissoes.py
```

Os testes criam um banco temporário e não devem alterar o banco de desenvolvimento. Na revisão documental de 7 de novembro de 2026, a suíte existente terminou com sucesso (`Tudo certo`). Isso não substitui uma auditoria de segurança, testes de carga, validação de acessibilidade ou teste de implantação pública.

## Dados e publicação no GitHub

O sistema guarda dados no arquivo SQLite local. Antes de enviar o repositório ao GitHub:

- Não inclua bancos de dados com dados reais, respostas de estudantes, anotações, senhas, tokens ou outros segredos.

- Revise se arquivos `.db`, `.db-wal` e `.db-shm`, arquivos de configuração local e variáveis secretas estão excluídos do versionamento.

- Use apenas dados fictícios em capturas de tela, demonstrações e bancos de exemplo.

- Não coloque `ADMIN_PASSWORD` nem outras credenciais no código, no histórico de commits, em screenshots ou neste README.

O assistente registra respostas de autorreflexão localmente. Essas respostas são declarações dos próprios estudantes: não comprovam fatos, autoria ou uso de IA e não devem ser tratadas como decisões disciplinares automáticas. Antes de qualquer piloto com estudantes, é necessário definir finalidade, aviso de privacidade, controle de acesso, retenção e descarte dos dados.

## Acessibilidade

O repositório inclui um componente separado de preferências de apresentação, com opções como tema, tamanho da fonte, espaçamento, sublinhado de links, redução de movimento e alto contraste. Há referências de projeto a WCAG 2.2 e eMAG; a existência dessas opções e referências **não significa que o sistema esteja certificado ou que sua conformidade tenha sido validada**. São necessários testes automáticos e manuais, incluindo teclado, leitores de tela, contraste e avaliação com pessoas com deficiência.

## Próximos passos recomendados

1. Substituir o login de estudantes baseado somente em nome por autenticação adequada ao contexto.

1. Definir e documentar regras de privacidade, retenção e descarte das respostas e anotações.

1. Revisar configuração de segredos, HTTPS, sessões e implantação antes de qualquer acesso externo.

1. Planejar hospedagem com armazenamento persistente, backups e testes de restauração.

1. Ampliar testes de segurança, acessibilidade, usabilidade e implantação.

1. Atualizar o backlog para refletir as implementações e pendências reais.

## Licença

Nenhuma licença de distribuição foi identificada nos arquivos analisados. Defina e inclua uma licença antes de autorizar reutilização, modificação ou redistribuição do código.
