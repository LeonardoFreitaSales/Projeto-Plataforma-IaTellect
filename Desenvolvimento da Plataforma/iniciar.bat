@echo off
cd /d "%~dp0"
title Assistente de uso de IA - Prototipo
where python >nul 2>&1
if errorlevel 1 (
  echo Python 3 nao foi encontrado. Instale Python e marque Add Python to PATH.
  pause
  exit /b 1
)
set PORT=3005
set HOST=127.0.0.1
set "TEST_MODE="
set "TEST_DATA_DIR="
set "DATA_DIR="
if "%ADMIN_PASSWORD%"=="" set ADMIN_PASSWORD=assistente-teste-123
echo Acesse: http://localhost:%PORT%
echo Login inicial de teste: admin / %ADMIN_PASSWORD%
echo Banco exclusivo deste prototipo: %~dp0data\Banco de Dados SQLite.db
echo O servidor ignora DATA_DIR externo e nao compartilha o banco com outras versoes.
echo.
python server.py
pause
