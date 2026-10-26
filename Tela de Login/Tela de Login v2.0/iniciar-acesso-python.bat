@echo off
title Intellecta AI - Tela de acesso
rem Coloque este arquivo na mesma pasta do server.py e do acesso.html.
cd /d "%~dp0"

if not exist "server.py" (
  echo Nao encontrei o server.py nesta pasta.
  pause
  exit /b 1
)
if not exist "acesso.html" (
  echo Nao encontrei o acesso.html nesta pasta.
  pause
  exit /b 1
)

set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
  echo Python nao encontrado. Instale em https://www.python.org/downloads/ e marque "Add Python to PATH".
  pause
  exit /b 1
)

if not defined PORT set PORT=3001
start "" /min cmd /c "ping -n 3 127.0.0.1 >nul & start http://localhost:%PORT%"
echo Tela de acesso em http://localhost:%PORT%  (feche esta janela para encerrar)
%PY% server.py
pause
