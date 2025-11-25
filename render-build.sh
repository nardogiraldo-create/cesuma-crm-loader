#!/usr/bin/env bash
set -e

echo "===== Iniciando build de Chrome en Render ====="

apt-get update
apt-get install -y chromium chromium-driver

echo "===== Verificando instalacion ====="
which chromium || echo "Chromium no está en PATH"
which chromedriver || echo "Chromedriver no está en PATH"

pip install --upgrade pip
pip install -r requirements.txt

echo "===== Build finalizado correctamente ====="
