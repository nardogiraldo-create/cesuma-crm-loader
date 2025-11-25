import os
import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# ============================================
#               LOGGING CONFIG
# ============================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================
#               CONFIG FLASK
# ============================================
app = Flask(__name__)
CORS(app)

# Validación de variables de entorno al inicio
CRM_URL = os.getenv("CRM_URL")
CRM_USER = os.getenv("CRM_USER")
CRM_PASS = os.getenv("CRM_PASS")

if not all([CRM_URL, CRM_USER, CRM_PASS]):
    logger.error("❌ Faltan variables de entorno críticas")
    raise ValueError("Se requieren CRM_URL, CRM_USER y CRM_PASS")

logger.info(f"✅ Configuración cargada - CRM: {CRM_URL}")

# ============================================
#               DRIVER CONFIG
# ============================================
def make_driver():
    chrome_options = Options()
    
    # ✅ CORRECCIÓN: Usar chromium en Render
    chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    if os.path.exists(chrome_bin):
        chrome_options.binary_location = chrome_bin
    elif os.path.exists("/usr/bin/chromium-browser"):
        chrome_options.binary_location = "/usr/bin/chromium-browser"
    else:
        logger.warning("⚠️ No se encontró Chrome/Chromium, usando default")

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    service = Service(chromedriver_path)
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(90)  # ✅ Mayor timeout para Render
    return driver

# ✅ Context manager para cerrar driver siempre
@contextmanager
def get_driver():
    driver = None
    try:
        driver = make_driver()
        yield driver
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("✅ Driver cerrado correctamente")
            except Exception as e:
                logger.error(f"Error cerrando driver: {e}")

# ==============================================
#         SELECTORES DEL CRM
# ==============================================
SELECTORS = {
    "USUARIO": 'input[id*="Usuario"]',
    "PASSWORD": 'input[id*="Password"]',
    "BTN_LOGIN": 'input[id*="Ingresar"]',
    
    "NOMBRE": 'input[id*="Nombre"]',
    "APELLIDO_PATERNO": 'input[id*="ApellidoPaterno"]',
    "EMAIL": 'input[id*="Correo"]',
    "CURP_ID": 'input[id*="CURP"]',
    "CELULAR": 'input[id*="Celular"]',
    "FECHA_NACIMIENTO": 'input[id*="FechaNacimiento"]',
    "POD_COM": 'input[type="checkbox"][id*="chkAcepta"]',
    
    "OFERTA_EDUCATIVA": 'select[id*="Programa"]',
    "PERIODO": 'select[id*="Periodo"]',
    "TIPO_HORARIO": 'select[id*="Horario"]',
    "DEPTO": 'select[id*="Departamento"]',
    "ESTATUS": 'select[id*="Estatus"]',
    
    "BTN_GUARDAR": 'input[id*="Guardar"]'
}

# ==============================================
#         VALIDACIÓN DE DATOS
# ==============================================
def validar_datos(data):
    """Valida que los datos recibidos sean correctos"""
    errores = []
    
    # Campos obligatorios
    campos_requeridos = ["nombre", "apellido_paterno", "email", "celular", "curp_id", "oferta"]
    for campo in campos_requeridos:
        if not data.get(campo) or not str(data[campo]).strip():
            errores.append(f"Campo '{campo}' es obligatorio")
    
    # Validar email
    email = str(data.get("email", "")).strip()
    if email and "@" not in email:
        errores.append("Email inválido")
    
    # Validar celular (mínimo 10 dígitos)
    celular = str(data.get("celular", "")).strip()
    digitos = ''.join(filter(str.isdigit, celular))
    if len(digitos) < 10:
        errores.append("Celular debe tener al menos 10 dígitos")
    
    # Validar longitud de CURP
    curp = str(data.get("curp_id", "")).strip()
    if curp and len(curp) < 5:
        errores.append("CURP/ID debe tener al menos 5 caracteres")
    
    return errores

# ==============================================
#         LOGIN AL CRM (CON REINTENTOS)
# ==============================================
def login_crm(driver, max_intentos=3):
    """Login con reintentos y mejor manejo de errores"""
    for intento in range(1, max_intentos + 1):
        try:
            logger.info(f"[LOGIN] Intento {intento}/{max_intentos}")
            driver.get(CRM_URL)
            
            wait = WebDriverWait(driver, 30)
            
            user = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["USUARIO"])))
            password = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["PASSWORD"])))
            btn_login = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["BTN_LOGIN"])))
            
            user.clear()
            user.send_keys(CRM_USER)
            
            password.clear()
            password.send_keys(CRM_PASS)
            
            btn_login.click()
            
            # ✅ Esperar a que la página cargue después del login
            time.sleep(3)
            logger.info("✅ Login exitoso")
            return True
            
        except TimeoutException as e:
            logger.warning(f"⚠️ Timeout en login intento {intento}: {e}")
            if intento < max_intentos:
                time.sleep(2 ** intento)  # Backoff exponencial
            else:
                raise
        except Exception as e:
            logger.error(f"❌ Error en login intento {intento}: {e}")
            if intento >= max_intentos:
                raise

# ==============================================
#         NAVEGAR A NUEVO PROSPECTO
# ==============================================
def ir_a_nuevo_prospecto(driver):
    logger.info("[NAVEGACIÓN] Ir a Nuevo Prospecto")
    driver.get("https://cesuma.academic.lat/Admin/RegistrarProspecto.aspx")
    
    wait = WebDriverWait(driver, 30)
    # ✅ Esperar a que el formulario esté listo
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["NOMBRE"])))
    logger.info("✅ Formulario cargado")

# ==============================================
#         LLENAR FORMULARIO (MEJORADO)
# ==============================================
def llenar_formulario(driver, data):
    wait = WebDriverWait(driver, 30)
    
    logger.info("[FORM] Llenando datos personales")
    
    # ✅ Helper para llenar campos con mejor manejo de errores
    def llenar_campo(selector, valor, nombre_campo):
        try:
            elemento = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            elemento.clear()
            elemento.send_keys(str(valor).strip())
            logger.info(f"✅ {nombre_campo}: {valor}")
        except Exception as e:
            logger.error(f"❌ Error en {nombre_campo}: {e}")
            raise ValueError(f"No se pudo llenar el campo {nombre_campo}")
    
    # Llenar campos de texto
    llenar_campo(SELECTORS["NOMBRE"], data["nombre"], "Nombre")
    llenar_campo(SELECTORS["APELLIDO_PATERNO"], data["apellido_paterno"], "Apellido")
    llenar_campo(SELECTORS["EMAIL"], data["email"], "Email")
    llenar_campo(SELECTORS["CURP_ID"], data["curp_id"], "CURP")
    llenar_campo(SELECTORS["CELULAR"], data["celular"], "Celular")
    
    # ✅ Fecha de nacimiento configurable
    fecha_nac = data.get("fecha_nacimiento", "01/01/2000")
    llenar_campo(SELECTORS["FECHA_NACIMIENTO"], fecha_nac, "Fecha Nacimiento")
    
    # Checkbox
    try:
        chk = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["POD_COM"])))
        if not chk.is_selected():
            chk.click()
        logger.info("✅ Checkbox POD_COM marcado")
    except Exception as e:
        logger.error(f"❌ Error en checkbox: {e}")
        raise
    
    logger.info("[FORM] Llenando datos académicos")
    
    # ✅ Oferta educativa con espera dinámica
    try:
        sel_oferta_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["OFERTA_EDUCATIVA"])))
        select_oferta = Select(sel_oferta_el)
        select_oferta.select_by_visible_text(data["oferta"])
        logger.info(f"✅ Oferta: {data['oferta']}")
        
        # ✅ Esperar a que se recargue el periodo (en vez de sleep fijo)
        time.sleep(1)
        wait.until(lambda d: len(Select(d.find_element(By.CSS_SELECTOR, SELECTORS["PERIODO"])).options) > 1)
        
    except Exception as e:
        logger.error(f"❌ Error seleccionando oferta: {e}")
        raise ValueError(f"No se encontró la oferta '{data['oferta']}'")
    
    # Periodo
    try:
        periodo_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["PERIODO"])))
        select_periodo = Select(periodo_el)
        select_periodo.select_by_index(1)
        logger.info("✅ Periodo seleccionado")
    except Exception as e:
        logger.error(f"❌ Error en periodo: {e}")
        raise
    
    # Tipo horario, Departamento, Estatus
    Select(wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["TIPO_HORARIO"])))).select_by_visible_text("MIXTO")
    Select(wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["DEPTO"])))).select_by_visible_text("COMERCIAL CALI")
    Select(wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["ESTATUS"])))).select_by_visible_text("PROSPECTO NUEVO")
    
    logger.info("[FORM] Guardando prospecto")
    
    # ✅ Guardar con mejor manejo
    btn_guardar = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTORS["BTN_GUARDAR"])))
    driver.execute_script("arguments[0].scrollIntoView(true);", btn_guardar)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", btn_guardar)
    
    # ✅ Esperar confirmación de guardado
    time.sleep(4)
    logger.info("✅ Formulario guardado")

# ==============================================
#                 ENDPOINT
# ==============================================
@app.route("/cargar_prospecto", methods=["POST"])
def cargar_prospecto():
    data = request.get_json()
    
    if not data:
        logger.error("❌ Request sin datos JSON")
        return jsonify({"status": "error", "detail": "Se requiere JSON en el body"}), 400
    
    logger.info(f"📥 Recibido prospecto: {data.get('nombre')} {data.get('apellido_paterno')}")
    
    # ✅ Validar datos
    errores = validar_datos(data)
    if errores:
        logger.error(f"❌ Validación fallida: {errores}")
        return jsonify({"status": "error", "detail": ", ".join(errores)}), 400
    
    # ✅ Usar context manager para garantizar cierre de driver
    try:
        with get_driver() as driver:
            login_crm(driver)
            ir_a_nuevo_prospecto(driver)
            llenar_formulario(driver, data)
            
        logger.info(f"✅ Prospecto cargado exitosamente: {data.get('nombre')}")
        return jsonify({"status": "success", "message": "Prospecto cargado correctamente"}), 200
        
    except ValueError as e:
        # Errores de validación o datos incorrectos
        logger.error(f"❌ Error de validación: {str(e)}")
        return jsonify({"status": "error", "detail": str(e)}), 400
        
    except TimeoutException as e:
        # Timeouts específicos
        logger.error(f"❌ Timeout: {str(e)}")
        return jsonify({"status": "error", "detail": "El CRM tardó demasiado en responder"}), 504
        
    except WebDriverException as e:
        # Errores de Selenium
        logger.error(f"❌ Error de WebDriver: {str(e)}")
        return jsonify({"status": "error", "detail": "Error al interactuar con el navegador"}), 500
        
    except Exception as e:
        # Cualquier otro error
        logger.error(f"❌ Error inesperado: {str(e)}", exc_info=True)
        return jsonify({"status": "error", "detail": f"Error interno: {str(e)}"}), 500

# ==============================================
#         HEALTH CHECK
# ==============================================
@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "service": "CRM Loader",
        "version": "2.0"
    })

@app.route("/health")
def health():
    """Endpoint para monitoring de Render"""
    return jsonify({
        "status": "healthy",
        "chrome_available": os.path.exists("/usr/bin/chromium") or os.path.exists("/usr/bin/chromium-browser")
    }), 200

# ==============================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
