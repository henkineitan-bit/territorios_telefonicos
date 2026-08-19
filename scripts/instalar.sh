#!/usr/bin/env bash
# Instala las dependencias del proyecto en un entorno virtual (./venv),
# para no mezclar librerías con el resto del sistema.
set -e
cd "$(dirname "$0")/.."

echo "==================================================="
echo "  Instalando dependencias - Gestor de Territorios"
echo "==================================================="
echo

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] No se encontró python3 instalado."
    echo "Instalalo desde https://www.python.org/downloads/"
    echo "o con el gestor de paquetes de tu sistema (apt, brew, etc.)."
    exit 1
fi

if [ ! -d venv ]; then
    echo "Creando entorno virtual en ./venv ..."
    python3 -m venv venv
    echo
fi

echo "Instalando librerías necesarias (puede tardar un minuto)..."
source venv/bin/activate
pip install --upgrade pip > /dev/null
pip install -r requirements.txt

echo
echo "==================================================="
echo "  Listo! Ahora podés ejecutar: ./scripts/iniciar_app.sh"
echo "==================================================="
