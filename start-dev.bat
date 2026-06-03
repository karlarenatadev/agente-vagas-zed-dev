@echo off
setlocal

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

if not exist "%BACKEND%\.venv\Scripts\activate.bat" (
    echo Backend .venv nao encontrado em "%BACKEND%\.venv".
    echo Crie o ambiente virtual e instale os requirements antes de iniciar.
    pause
    exit /b 1
)

if not exist "%FRONTEND%\package.json" (
    echo Frontend nao encontrado em "%FRONTEND%".
    pause
    exit /b 1
)

start "Backend - import vagas" cmd /k "cd /d ""%BACKEND%"" && call .venv\Scripts\activate.bat && python run.py"
start "Frontend - import vagas" cmd /k "cd /d ""%FRONTEND%"" && npm run dev"

echo Backend iniciando em http://localhost:8000
echo Frontend iniciando em http://localhost:5173
echo.
timeout /t 3 /nobreak >nul
start "" "http://localhost:5173"

echo Feche as duas janelas abertas para parar os servidores.

endlocal
