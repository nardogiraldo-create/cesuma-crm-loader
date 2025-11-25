#!/usr/bin/env bash
set -e

echo "===== Iniciando build de Chrome en Render ====="

# Actualizar repositorios
echo "Actualizando repositorios..."
apt-get update

# Instalar Chromium y ChromeDriver
echo "Instalando Chromium y ChromeDriver..."
apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg

echo "===== Verificando instalación ====="

# Verificar Chromium
if [ -f /usr/bin/chromium ]; then
    echo "✅ Chromium encontrado en: /usr/bin/chromium"
    /usr/bin/chromium --version || echo "⚠️ No se pudo obtener versión"
elif [ -f /usr/bin/chromium-browser ]; then
    echo "✅ Chromium encontrado en: /usr/bin/chromium-browser"
    /usr/bin/chromium-browser --version || echo "⚠️ No se pudo obtener versión"
    # Crear symlink
    ln -sf /usr/bin/chromium-browser /usr/bin/chromium
else
    echo "❌ ERROR: Chromium no encontrado"
    exit 1
fi

# Verificar ChromeDriver
if [ -f /usr/bin/chromedriver ]; then
    echo "✅ ChromeDriver encontrado en: /usr/bin/chromedriver"
    /usr/bin/chromedriver --version || echo "⚠️ No se pudo obtener versión"
else
    echo "❌ ERROR: ChromeDriver no encontrado"
    exit 1
fi

# Instalar dependencias de Python
echo "===== Instalando dependencias de Python ====="
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements.txt

# Verificar instalación de Selenium
echo "===== Verificando Selenium ====="
python3 -c "import selenium; print('✅ Selenium version:', selenium.__version__)"

echo "===== Build finalizado correctamente ====="
echo "Chromium: $(which chromium || which chromium-browser || echo 'Not found')"
echo "ChromeDriver: $(which chromedriver || echo 'Not found')"
