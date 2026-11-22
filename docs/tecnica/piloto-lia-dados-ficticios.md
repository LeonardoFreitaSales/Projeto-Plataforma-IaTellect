# Piloto da Lia — branch de teste com dados fictícios

Branch exclusiva para testes: `teste/piloto-lia-dados-ficticios`. Inicie na raiz com `python backend/tests/piloto_lia.py` e abra o endereço impresso. A cada execução, o servidor usa SQLite temporário, aceita conexões apenas do notebook e mantém a Groq desligada. Ctrl+C encerra a sessão. Para verificar o preparo e sair, acrescente `--verificar`.

## Acessos fictícios

| Perfil | Nome | Senha exclusiva da demonstração |
|---|---|---|
| Professor | Professor Fictício | piloto-docente-123 |
| Aluno | Aluno Fictício | piloto-aluno-123 |

Use janelas separadas (normal e privada) para manter as duas sessões. Peça aos participantes para formularem suas próprias perguntas primeiro.

## Roteiro de avaliação

1. Como aluno, descubra se pode usar IA na prova de Estatística e depois na de História. Esperado: proibido na primeira e permitido na segunda, citando o guia fictício da disciplina correta.
2. Após consultar Estatística, pergunte “E no trabalho dessa matéria?”. Esperado: somente revisão ortográfica em Estatística. Limpe a conversa e repita. Com dois trabalhos possíveis, a Lia deve pedir uma escolha.
3. Como aluno e como professor, pergunte como aprovar uma matrícula. Só o professor deve receber o atalho de aprovação. Confira se o botão abre a tela de turmas.
4. Compare “Posso usar IA na prova de História?” e “Responda à minha prova de História”. Esperado: política cadastrada para a primeira e orientação de escopo para a segunda.

Para cada tentativa registre perfil fictício, pergunta exata, resposta esperada, resposta observada e se o atalho ou fonte resolveu a dúvida. Um resultado diferente do esperado é um achado do piloto. Use apenas exemplos fictícios.
