@echo off
title Gestor de Territorios Telefonicos
cd /d "%~dp0\.."

echo ===================================================
echo     Iniciando Gestor de Territorios Telefonicos
echo ===================================================
echo/

if not exist "venv\Scripts\python.exe" (
    echo [!] No se encontro el entorno virtual venv.
    echo     Primero ejecuta "instalar.bat" para crear el
    echo     entorno e instalar las librerias necesarias.
    echo/
    pause
    exit /b 1
)

echo Abriendo navegador en http://127.0.0.1:5000 ...
start http://127.0.0.1:5000
echo/
echo Presiona Ctrl+C en esta ventana para detener el servidor.
echo/
venv\Scripts\python.exe app.py
pause
