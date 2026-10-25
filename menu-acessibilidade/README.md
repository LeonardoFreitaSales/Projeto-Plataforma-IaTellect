# Menu de acessibilidade

Arquivos:
- `index.html`: marcação do menu (e script curto no `<head>` que aplica o tema salvo antes da página aparecer, evitando "piscar").
- `acessibilidade.css`: variáveis de tema (claro/escuro), tamanho de fonte, espaçamento, alto contraste e estilos do menu.
- `acessibilidade.js`: lógica; salva as preferências em `localStorage` na chave `painel-acessibilidade`.

Para usar em outra página: copie o `<section id="accessibility-menu">`, inclua o CSS e o JS, e mantenha o script do `<head>`.
Basta abrir `index.html` no navegador (não precisa de servidor). As fontes DM Sans e Playfair Display vêm do Google Fonts.
