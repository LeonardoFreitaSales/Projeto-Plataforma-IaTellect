# Avaliação da busca da Lia

Conversa executada no Chrome com uma aluna fictícia após a aprovação da matrícula. O banco temporário continha três políticas visíveis. Estatística permitia IA na avaliação parcial e proibia na avaliação final. História permitia IA na prova final. A diferença entre as regras torna observável se a assistente conserva a disciplina ao responder.

Para repetir, cadastre essas políticas com os tipos de atividade definidos como prova, vincule ambas as disciplinas à turma e abra o chat como aluna aprovada. Limpe a conversa uma vez e envie as perguntas na ordem abaixo.

| Pergunta | Política esperada | Resposta observada |
|---|---|---|
| Avaliação parcial | Parcial de Estatística | Permitido. Citou o Guia da avaliação parcial. |
| Posso usar IA na avaliação parcial de Estatística? | Parcial de Estatística | Permitido. Citou a mesma fonte. |
| E na prova final? | Final de Estatística, pela disciplina da pergunta anterior | Ofereceu duas opções, História e Estatística. Pediu uma escolha. |
| Prova final de Estatística | Final de Estatística | Proibido. Citou o Plano de ensino. |
| O professor deixa usar inteligência artificial na avaliação parcial de Estatística? | Parcial de Estatística | Informou que não encontrou uma política correspondente. |

A terceira pergunta avalia continuidade. Repetir a disciplina na quarta pergunta recuperou a regra correta. A quinta pergunta reformula a segunda e mantém a disciplina explícita. A busca atual exige que todos os termos restantes após a filtragem ocorram na política, e expressões como “o professor deixa” podem impedir uma correspondência.

Para a próxima implementação, repetir esta conversa e verificar se a continuação recupera a política de Estatística e se a reformulação recupera a mesma fonte da segunda pergunta. Repetir também “E na prova final?” após limpar o chat. Sem disciplina anterior, as duas opções devem permanecer disponíveis.

## Resultado após a etapa 3

As cinco perguntas acima retornaram a fonte esperada no Chrome, com a Groq desativada. Mencionar História explicitamente mudou a disciplina da continuação. Limpar o chat fez a consulta voltar a oferecer as duas provas. A reformulação externa foi verificada separadamente com respostas simuladas de sucesso e de limite de uso.

## Navegação, assuntos externos e validação real

Em um banco temporário, um usuário autenticado perguntou “Qual orientação devo seguir para usar IA na prova final de Estatística?”. A primeira consulta não encontrou registros. A reformulação real da Groq resultou em “prova final Estatística”. A nova busca retornou uma política de teste com situação proibida e fonte Plano fictício.

A suíte verifica a recusa de perguntas externas, inclusive quando mencionam uma prova, o bloqueio direto na rota de reformulação e os destinos de navegação por perfil. No Chrome, a aluna abriu Disciplinas e políticas pelo chat e recebeu orientação sobre a restrição de aprovação de matrículas. O reconhecimento usa termos e expressões em português e pode pedir uma nova formulação para perguntas legítimas ainda não cobertas.
