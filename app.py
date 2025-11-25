import os
from flask import Flask, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# =======================================================
# 1. CONFIGURACIÓN BÁSICA DE LA APLICACIÓN
# =======================================================

# Inicialización de la aplicación Flask
app = Flask(__name__)
# Habilitar CORS para permitir peticiones desde diferentes orígenes
CORS(app)

# Obtener variables de entorno
# Estas variables son las que configuraste manualmente en Render
CRM_URL = os.environ.get("CRM_URL", "http://placeholder.com")
CRM_USER = os.environ.get("CRM_USER", "usuario_no_definido")
CRM_PASSWORD = os.environ.get("CRM_PASSWORD", "password_no_definido")
PORT = os.environ.get("PORT", "5000")

# =======================================================
# 2. CONFIGURACIÓN DEL DRIVER (SELENIUM/CHROMIUM)
# =======================================================

def get_chrome_options():
    """Configura las opciones de Chrome para ejecución Headless en Render."""
    chrome_options = Options()
    # Ejecución sin interfaz gráfica
    chrome_options.add_argument("--headless")
    # Argumentos de seguridad y estabilidad necesarios en entornos Linux/Docker
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Tamaño de ventana para simular un escritorio
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Asignar la ruta del binario de Chrome (instalado por Dockerfile)
    # Se usa la variable de entorno que también está en el Dockerfile
    chrome_options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    
    return chrome_options

# =======================================================
# 3. ENDPOINTS DE LA APLICACIÓN
# =======================================================

# -------------------------------------------------------
# RUTA PRINCIPAL (CORRECCIÓN DEL ERROR 'home')
# -------------------------------------------------------
# Función renombrada a 'index' para evitar el conflicto
@app.route("/")
def index():
    """Ruta de bienvenida para verificar que la app de Flask está corriendo."""
    return jsonify({
        "status": "Service Running",
        "message": "CRM Loader API is operational. Check /health for driver status.",
        "crm_target": CRM_URL,
        "env": os.environ.get("ENV", "DEV")
    })

# -------------------------------------------------------
# RUTA DE HEALTH CHECK (CRÍTICA PARA RENDER)
# -------------------------------------------------------
# Función renombrada a 'health_check' (evita el conflicto 'home')
@app.route("/health")
def health_check():
    """Verifica si Gunicorn está activo y si Chromium/ChromeDriver funcionan."""
    chrome_available = False
    
    try:
        chrome_options = get_chrome_options()
        # Inicializa el driver usando la ruta del Dockerfile/Variable de Entorno
        driver = webdriver.Chrome(
            options=chrome_options, 
            executable_path=os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
        )
        driver.quit()
        chrome_available = True
        
    except Exception as e:
        # Si el driver falla, el error se registra, pero el servidor sigue vivo
        print(f"Health Check FAILED. Driver error: {e}")
        
    # Devuelve el estado del servicio
    return jsonify({
        "status": "healthy",
        "chrome_available": chrome_available
    })

# -------------------------------------------------------
# LÓGICA DEL LOADER (EJEMPLO DE UNA RUTA DE TRABAJO)
# -------------------------------------------------------
@app.route("/api/load_data", methods=["POST"])
def load_data():
    """Función para iniciar el proceso de carga de datos en el CRM (Lógica principal)."""
    # **AQUÍ IRÍA TU LÓGICA DE SELENIUM PARA LOGIN Y CARGA DE DATOS**
    
    if os.environ.get("ENV") != "PROD":
        return jsonify({"message": "Running in non-production mode, task simulated."})
        
    # Aquí puedes llamar a una función de la lógica del CRM Loader
    # try:
    #     iniciar_proceso(CRM_URL, CRM_USER, CRM_PASSWORD)
    #     return jsonify({"status": "success", "message": "Data load initiated."})
    # except Exception as e:
    #     return jsonify({"status": "error", "message": str(e)}), 500
        
    return jsonify({"status": "pending", "message": "Implementación pendiente de la lógica de Selenium."})


# =======================================================
# 4. INICIO DEL SERVIDOR
# =======================================================

# Solo para ejecución local (Gunicorn se encarga de esto en Render)
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(PORT))
