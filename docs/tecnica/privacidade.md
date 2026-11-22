# Dados e retenção na instalação local

O SQLite da instalação registra nomes de acesso, perfis, verificadores de senha, matrículas, vínculos de turmas, políticas de disciplinas, comunicados, histórico de alterações e anotações privadas de professores. O servidor usa o endereço de origem para limitar tentativas de acesso. Um cookie identifica a sessão do navegador. O arquivo de senha inicial, quando gerado, exige proteção até a troca da senha.

Os perfis controlam a visibilidade. Estudantes consultam matérias após a aprovação da matrícula. Professores administram as turmas autorizadas e consultam suas próprias anotações. Quem tem acesso direto ao banco ou a seus backups também pode ler esses registros.

As sessões expiram em sete dias. O encerramento da sessão invalida seu token. A plataforma não implementa expurgo geral por idade para cadastros, anotações e auditoria. Os backups têm ciclo de vida próprio.

Antes de usar dados reais, a instituição deve informar aos participantes a finalidade de cada coleta, o responsável e seu canal de contato, quem pode acessar os registros, os prazos de conservação e o procedimento para pedidos de acesso, correção ou exclusão. A equipe deve aplicar os prazos aprovados também aos backups e documentar como verificar o descarte. Esses prazos e o contato institucional aguardam definição dos responsáveis.

O chat mantém a disciplina em memória na página e descarta o contexto ao limpar a conversa. Quando a integração opcional está habilitada, o botão de reformulação envia o texto integral daquela pergunta à Groq. O pedido ao provedor inclui instruções de busca e a pergunta; o histórico, o cadastro e as políticas ficam na instalação. Evite incluir dados pessoais na pergunta enviada.
