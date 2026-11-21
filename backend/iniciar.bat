@echo off
cd /d "%~dp0"
set "HOST=127.0.0.1"
set "PORT=3002"
set "TEST_MODE="
set "TEST_DATA_DIR="
echo Abra http://127.0.0.1:3002/acesso.html
python server.py
pause
