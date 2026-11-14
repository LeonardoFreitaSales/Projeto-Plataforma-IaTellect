# Revisao da entrega v4.0

- Python: 104 verificacoes OK, nenhuma falha (`python test_permissoes.py`).
- Sintaxe Python: server.py e test_permissoes.py analisados sem erro.
- JavaScript: node --check aprovado nos seis blocos inline de index.html e acesso.html.
- Banco temporario separado nos testes; banco local excluido do pacote.

## Cobertura funcional

Permissoes de aluno, professor e administrador; login ausente, invalido e expirado;
contas antigas sem senha e sessoes legadas bloqueadas; definicao de senha por responsavel;
preservacao da matricula antiga; troca de senha e revogacao de outras sessoes; limites de tentativas;
cadastro com resposta identica em conflito de nome; aprovacao de matricula; privacidade de anotacoes
e historico; exclusao autorizada de turma remove matriculas e preserva contas.

Papel ausente e testado em objetos incompletos, sem desligar restricoes do banco.
NOT NULL rejeita papel nulo; CHECK rejeita papel desconhecido. Ambos permanecem ativos.

## Revisao visual real em servidor local

Navegador em 1366x900 e 390x844; verificacao adicional de dialogos com viewport solicitado de 320x740
(o navegador reportou largura interna de 321 pixels). Login/cadastro, barra de usuario,
Alterar senha, Definir senha e confirmacao de exclusao foram inspecionados.

Corrigidos: ciclo de Tab/Shift+Tab nos dialogos, espacamento entre titulo e botao Fechar,
nome acessivel do dialogo principal, fechamento do menu movel na gestao e apresentacao neutra
da resposta de cadastro. Escape devolve o foco ao acionador; exclusao abre com foco em Cancelar.
Campos invalidos recebem foco. Nao houve overflow horizontal nos estados moveis medidos.

A revisao visual usou dados ficticios. A gravacao de novas senhas, a aprovacao e a exclusao efetiva
foram validadas pela suite HTTP; a interface dos dialogos foi verificada com abertura/cancelamento.
A v4 conserva a interface revisada, com atualizacao de identificadores e documentacao da versao.

## Limites e integridade

Emulacao de largura no navegador nao substitui aparelho fisico ou leitor de tela. Os prototipos
historicos e a implantacao publica nao foram integralmente validados. O painel Node segue separado.

Nao foram encontrados arquivos .db ou senha_admin_inicial.txt rastreados no indice nem nos caminhos
do historico Git local consultado. Isso nao equivale a uma auditoria completa de todo segredo possivel.
.gitignore exclui bancos e senhas, inclusive modelos .db. git fsck nao encontrou corrupcao;
indicou apenas arvores soltas preexistentes. Este relatorio descreve a validacao anterior a publicacao no GitHub.
