@echo off
cd /d "%~dp0"
set PY=
where py >nul 2>nul && set PY=py
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
  echo Python nao encontrado. Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
  pause
  exit /b 1
)
start "" /min cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:3001/acesso.html"
%PY% server.py
pause
