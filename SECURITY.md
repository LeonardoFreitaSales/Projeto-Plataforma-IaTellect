# Segurança do IaTellect

## Comunicar um problema

Em uma instalação local, contate o responsável que forneceu o acesso por um canal privado. Informe a versão, a funcionalidade e o impacto observado usando dados fictícios. A equipe deve definir e divulgar um contato institucional antes do piloto.

## Configuração

A execução padrão escuta em 127.0.0.1. Requisições de escrita à API exigem o cabeçalho Origin. O navegador o envia nos fluxos da plataforma. Clientes de integração devem enviar a origem completa da instalação, incluindo esquema e porta. ALLOWED_ORIGINS aceita origens adicionais separadas por vírgulas. A autenticação e as permissões continuam obrigatórias para as rotas protegidas.

Em uma instalação HTTPS, configure COOKIE_SECURE=1, preserve o host público no proxy e envie Strict-Transport-Security nas respostas HTTPS no ponto que termina a conexão TLS. O servidor Python local usa HTTP. A política de permissões desativa câmera, microfone e geolocalização.

Habilite TRUST_PROXY=1 somente atrás de um proxy administrado pela equipe e informe os IPs autorizados em TRUSTED_PROXY_IPS. Configure cada proxy para registrar o endereço real do salto anterior e restrinja o acesso direto ao servidor. A aplicação percorre a cadeia da direita para a esquerda enquanto os saltos forem confiáveis.

## Publicar o código

Gere o pacote pela árvore versionada do Git. A pasta de dados contém o banco e pode conter a senha inicial em texto claro. Guarde backups privados com acesso restrito. Após entrar, troque a senha inicial e remova o arquivo de senha.
