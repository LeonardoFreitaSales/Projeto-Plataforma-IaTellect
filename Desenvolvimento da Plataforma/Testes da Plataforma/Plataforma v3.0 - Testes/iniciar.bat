@echo off
cd /d "%~dp0"
title Plataforma v3.0 - Testes

where python >nul 2>&1
if errorlevel 1 (
  echo Python 3 nao foi encontrado. Instale em https://www.python.org e marque "Add Python to PATH".
  pause
  exit /b 1
)

rem --- Configuracao de TESTE (somente neste computador) ---
set PORT=3002
set HOST=127.0.0.1
set "TEST_MODE="
set "TEST_DATA_DIR="
set "DATA_DIR="
rem Senha do administrador usada so na PRIMEIRA execucao (quando o banco ainda nao tem admin).
if "%ADMIN_PASSWORD%"=="" set ADMIN_PASSWORD=admin1234
rem Para outras pessoas da mesma rede testarem, troque HOST para 0.0.0.0
rem e escolha uma senha diferente de admin1234.

echo Acesse: http://localhost:%PORT%
echo Login de teste: admin / %ADMIN_PASSWORD%  (so vale se o admin ainda nao existia)
echo Banco exclusivo desta versao: %~dp0data\Banco de Dados SQLite.db
echo O servidor ignora DATA_DIR externo e nao compartilha o banco com outras versoes.
echo.
python server.py
pause
