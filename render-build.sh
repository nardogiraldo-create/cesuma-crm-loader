#!/usr/bin/env bash
set -e

echo "===== Iniciando build de Chrome en Render ====="

# Actualizar repositorios
apt-get update

# Instalar Chromium y ChromeDriver
echo "Instalando Chromium y ChromeDriver..."
apt-get install -y chromium chromium-driver

# Verificar instalación
echo "===== Verificando instalación ====="
if which chromium; then
    echo "✅ Chromium instalado en: $(which chromium)"
    chromium --version
else
    echo "⚠️ Chromium no está en PATH, buscando..."
    if [ -f /usr/bin/chromium-browser ]; then
        echo "✅ Encontrado en /usr/bin/chromium-browser"
    fi
fi

if which chromedriver; then
    echo "✅ ChromeDriver instalado en: $(which chromedriver)"
    chromedriver --version
else
    echo "❌ ChromeDriver no encontrado"
    exit 1
fi

# Instalar dependencias de Python
echo "===== Instalando dependencias de Python ====="
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalación de Selenium
python3 -c "import selenium; print('✅ Selenium version:', selenium.__version__)"

echo "===== Build finalizado correctamente ====="
echo "Chromium path: $(which chromium || which chromium-browser || echo 'Not found')"
echo "ChromeDriver path: $(which chromedriver || echo 'Not found')"
