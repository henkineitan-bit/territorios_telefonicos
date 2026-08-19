#!/usr/bin/env bash
cd "$(dirname "$0")/.."

echo "==================================================="
echo "    Iniciando Gestor de Territorios Telefónicos"
echo "==================================================="
echo

if [ -d venv ]; then
    source venv/bin/activate
else
    echo "[AVISO] No se encontró el entorno virtual todavía."
    echo "Ejecutá primero: ./scripts/instalar.sh"
    echo "Intentando usar el Python del sistema por las dudas..."
    echo
fi

# Abre el navegador 2 segundos después de arrancar, en paralelo al servidor
( sleep 2 && python3 -c "import webbrowser; webbrowser.open('http://127.0.0.1:5000')" ) &

echo "Presioná Ctrl+C en esta ventana para detener el servidor."
echo
python3 app.py
