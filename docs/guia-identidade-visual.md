# Guia de identidade visual — IaTellect

- **Nome oficial:** IaTellect
- **Descritor:** Políticas acadêmicas de uso de IA
- **Assinatura:** Clareza e confiança acadêmica.

> [!NOTE]
> Este guia considera o protótipo do repositório e as capturas do Google Sites fornecidas em 20 de novembro de 2026. As fontes e os códigos hexadecimais do Google Sites não puderam ser confirmados pelo painel de tema; as comparações visuais com o site são aproximadas. O Trello não foi acessado diretamente.

## Essência e tom de voz

O IaTellect organiza orientações acadêmicas para que estudantes, docentes e gestores consultem regras antes de cada atividade. A comunicação deve ser institucional, direta, acolhedora e cautelosa, sem sugerir validação, segurança ou resultados que o protótipo ainda não comprova.

| Faça | Evite |
| --- | --- |
| Explique a regra, a condição e a fonte em linguagem direta. | Prometer segurança, detecção de autoria ou impacto educacional comprovado. |
| Identifique claramente quando algo é demonstrativo, experimental ou ainda precisa de validação. | Usar linguagem promocional, futurista ou excessivamente tecnológica. |
| Oriente a próxima ação: consultar, confirmar, revisar ou procurar o responsável. | Culpabilizar estudantes ou apresentar decisões automáticas como conclusivas. |

## Paleta

| Grupo | Cor | Uso recomendado |
| --- | --- | --- |
| Primária | Teal `#08758A` | Ações principais, links, foco e elementos de marca. |
| Primária clara | Teal claro `#46BDC9` | Ícones, detalhes e fundos suaves. |
| Institucional | Azul-marinho `#10243B` | Cabeçalhos, navegação e fundos escuros. |
| Destaque | Âmbar `#D98218` | Ênfase editorial pontual; nunca representar política. |
| Texto | Azul-escuro `#14243A` | Texto principal sobre superfícies claras. |
| Texto secundário | Cinza-azulado `#637188` | Legendas e informações auxiliares. |
| Linha | Cinza-claro `#D8E1EB` | Bordas e divisores. |
| Fundo | Cinza muito claro `#F3F6F9` | Fundo geral. |
| Superfície | Branco `#FFFFFF` | Cards, formulários e tabelas. |

### Cores de estado

| Estado | Cor | Regra |
| --- | --- | --- |
| Permitido | Verde `#3E9C6A` | Somente para indicar que o uso está permitido. |
| Com restrições | Amarelo `#E0A13E` | Somente para indicar uso condicionado. |
| Proibido | Vermelho `#CE5365` | Somente para indicar que o uso não é permitido. |

- Nunca usar verde, amarelo ou vermelho como decoração de página.
- Nunca comunicar um estado apenas pela cor: incluir sempre rótulo textual e, quando possível, ícone.
- Não alterar o significado das cores entre site, protótipo, README, Trello ou apresentações.
- Estados de interface que não sejam políticas devem preferir teal ou neutros para evitar ambiguidade.

## Tipografia

- **Família principal:** Inter.
- **Alternativas:** `ui-sans-serif`, `system-ui`, `Segoe UI`, `sans-serif`.
- Títulos com peso 700 ou 800; corpo com peso 400 ou 500; rótulos com peso 600 ou 700.
- Corpo mínimo de 16 px nos canais digitais, entrelinha de aproximadamente 1,5 e parágrafos curtos.
- Evitar misturar fontes serifadas, itálico prolongado, caixa alta em frases e textos muito pequenos.

## Logo

- Usar o ícone cerebral teal com o nome **IaTellect** e o descritor **Políticas acadêmicas de uso de IA**.
- Preferir `logo.svg`; usar `logo.png` apenas onde SVG não for aceito.
- Manter área livre mínima equivalente a um quarto da largura do ícone.
- Tamanho mínimo recomendado do ícone: 32 px em interfaces e 48 px em materiais de apresentação.
- Não aplicar cores de estado, sombras intensas, distorções, rotações ou fundos com pouco contraste.

## Imagens e componentes

- **Imagens:** capturas reais do protótipo, com dados fictícios, enquadramento consistente e legenda objetiva. Evitar bancos de imagem genéricos, robôs, cérebros hiper-realistas e fundos de circuitos.
- **Cards:** superfície branca, borda `#D8E1EB`, raio de 16 px, sombra discreta e título curto.
- **Badges:** compactos, com texto explícito. As três cores semânticas ficam restritas aos estados de política.
- **Chips:** usar teal ou neutros para filtros, perfis e categorias; não reutilizar a aparência dos estados.
- **Ações:** botão principal teal, botão secundário branco com borda e foco visível.

## Inconsistências e correções recomendadas

| Canal | Situação observada | Correção recomendada |
| --- | --- | --- |
| Google Sites | Nome principal “Políticas de uso de IA” e título “Políticas de IA”. | Adotar “IaTellect” e o descritor “Políticas acadêmicas de uso de IA”. |
| Google Sites | Selo circular verde diferente do ícone usado no protótipo. | Substituir pelo `logo.svg` oficial, sem cor de estado. |
| Google Sites | Fundo preto com circuitos verdes e linhas douradas decorativas. | Usar azul-marinho e teal; retirar verde e amarelo de elementos decorativos. |
| Google Sites | Tipografia serifada, itálicos e mistura de estilos. | Padronizar em Inter ou, se indisponível, Arial/sans-serif. |
| Google Sites | Textos pequenos, grandes vazios e miniaturas difíceis de ler. | Aumentar corpo, limitar largura de leitura e organizar materiais em cards com títulos. |
| Google Sites | “Intellecta”, “IaTellect” e “Intellecta AI” aparecem na documentação e no rodapé. | Substituir por “IaTellect” e manter “Intellecta” apenas em registros históricos claramente identificados. |
| Trello | Board informado como “Intellecta AI”; aparência não verificada. | Renomear para “IaTellect — Projeto acadêmico” e aplicar capa teal/azul-marinho. |
| Repositório | Nome técnico contém IaTellect, mas o histórico usa “Protótipo-SI-IA”. | Manter o nome do repositório e usar IaTellect em título, descrição e documentação atual. |
| README | Título já corrigido para IaTellect no PR de identidade. | Acrescentar descritor oficial, fluxo em três passos, tabela de estados e rodapé institucional. |
| Protótipo | Usa IaTellect, Inter e a paleta teal/azul-marinho. | Torná-lo a referência visual para os demais canais. |
| Conteúdo | Site e README descrevem formas de login diferentes da implementação v4. | Não harmonizar por suposição; validar com a equipe qual versão é a referência funcional. |

## Checklist de coerência

- [ ] O nome aparece como **IaTellect** em todos os canais.
- [ ] O descritor aparece como **Políticas acadêmicas de uso de IA**.
- [ ] O logo cerebral teal substitui selos e marcas provisórias.
- [ ] Inter ou uma alternativa sans-serif é usada de forma consistente.
- [ ] Verde, amarelo e vermelho aparecem somente em estados e sempre com texto.
- [ ] O fluxo é apresentado como selecionar disciplina, consultar regras e verificar o nível.
- [ ] Site, README e apresentações usam o mesmo texto para cada estado.
- [ ] Capturas usam somente dados fictícios.
- [ ] Avisos de protótipo, segurança, privacidade, autenticação e ausência de validação permanecem visíveis.
- [ ] O rodapé contém **Projeto acadêmico — CESAR School**.
- [ ] Links de Figma, Trello, MoSCoW e Método 635 ficam em Materiais do projeto.
- [ ] Afirmações sobre resultados são publicadas somente após testes e evidências documentadas.
