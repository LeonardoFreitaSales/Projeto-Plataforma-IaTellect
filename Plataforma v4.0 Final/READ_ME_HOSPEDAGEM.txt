PLATAFORMA V4.0 - PUBLICAR O SITE (SERVIDOR COM DISCO PERSISTENTE)

O que a hospedagem precisa ter
  - Python 3 (sem pacotes extras) e permissao para rodar um processo continuo.
  - DISCO PERSISTENTE: o banco e um arquivo. Em hospedagens sem disco
    persistente o arquivo some a cada novo deploy/reinicio.

Passos
  1. Envie: acesso.html, index.html, server.py, schema_Banco_de_Dados_SQLite.sql
     Nao envie bancos locais, arquivos de senha nem dados de teste.
  2. Comando de inicio: python server.py
  3. Variaveis de ambiente:
       HOST=0.0.0.0              escutar fora da maquina
       PORT=<porta da hospedagem> (muitas hospedagens ja definem sozinhas)
       ADMIN_PASSWORD=<senha forte, minimo 8 caracteres>
       COOKIE_SECURE=1           se o site abre em https://
       TRUST_PROXY=1             se ha proxy reverso confiavel na frente
       ALLOWED_ORIGINS=https://seu-dominio   so se a hospedagem alterar o Host
  4. Abra o site, entre como admin, cadastre os professores e escolha o dono
     de cada materia.
  5. Para trazer os dados atuais, copie o arquivo "Banco de Dados SQLite.db" para
     a pasta data/ ao lado de server.py ANTES do primeiro inicio.
     DATA_DIR externo e ignorado. Monte o disco persistente nessa pasta data/.
     Guarde uma copia de seguranca; contas antigas sem senha ficam bloqueadas.

Teste depois de publicar
  - /api/health deve responder {"status":"ok"}.
  - /server.py e /data/... devem dar "Arquivo nao encontrado".
  - Entre como professor e tente editar materia de outro: deve dar 403/404.
  - Reinicie o servico e confirme que os dados continuam la.

Backup
  Agende copia periodica do arquivo .db (e dos .db-wal/.db-shm se existirem).
