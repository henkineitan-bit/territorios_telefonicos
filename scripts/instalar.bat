@echo off
title Instalar dependencias - Gestor de Territorios Telefonicos
cd /d "%~dp0\.."

echo ===================================================
echo   Instalando dependencias - Gestor de Territorios
echo ===================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] No se encontro Python instalado o no esta en el PATH.
    echo.
    echo Instala Python desde https://www.python.org/downloads/
    echo y durante la instalacion marca la casilla "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

if not exist venv (
    echo Creando entorno virtual en .\venv ...
    python -m venv venv
    echo.
)

echo Instalando librerias necesarias (puede tardar un minuto)...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt

echo.
echo ===================================================
echo   Listo! Ahora podes ejecutar iniciar_app.bat
echo ===================================================
echo.
pause
