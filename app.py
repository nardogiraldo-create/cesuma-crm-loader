import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# ============================================
#               CONFIG FLASK
# ============================================

app = Flask(__name__)
CORS(app)

CRM_URL = os.getenv("CRM_URL")
CRM_USER = os.getenv("CRM_USER")
CRM_PASS = os.getenv("CRM_PASS")

# ============================================
#               DRIVER CONFIG
# ============================================

def make_driver():
    chrome_options = Options()
    chrome_options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--remote-debugging-port=9222")

    service = Service(os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver

# ==============================================
#         SELECTORES DEL CRM
# ==============================================

SELECTORS = {
    "USUARIO": 'input[id*="Usuario"]',
    "PASSWORD": 'input[id*="Password"]',
    "BTN_LOGIN": 'input[id*="Ingresar"]',

    # formulario único
    "NOMBRE": 'input[id*="Nombre"]',
    "APELLIDO_PATERNO": 'input[id*="ApellidoPaterno"]',
    "EMAIL": 'input[id*="Correo"]',
    "CURP_ID": 'input[id*="CURP"]',
    "CELULAR": 'input[id*="Celular"]',
    "FECHA_NACIMIENTO": 'input[id*="FechaNacimiento"]',
    "POD_COM": 'input[type="checkbox"][id*="chkAcepta"]',

    # académicos
    "OFERTA_EDUCATIVA": 'select[id*="Programa"]',
    "PERIODO": 'select[id*="Periodo"]',
    "TIPO_HORARIO": 'select[id*="Horario"]',
    "DEPTO": 'select[id*="Departamento"]',
    "ESTATUS": 'select[id*="Estatus"]',

    "BTN_GUARDAR": 'input[id*="Guardar"]'
}

# ==============================================
#         LOGIN AL CRM
# ==============================================

def login_crm(driver):
    print("[STEP] Entrando a CRM_URL", flush=True)
    driver.get(CRM_URL)

    wait = WebDriverWait(driver, 30)

    user = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["USUARIO"])))
    password = driver.find_element(By.CSS_SELECTOR, SELECTORS["PASSWORD"])
    btn_login = driver.find_element(By.CSS_SELECTOR, SELECTORS["BTN_LOGIN"])

    user.clear()
    user.send_keys(CRM_USER)

    password.clear()
    password.send_keys(CRM_PASS)

    btn_login.click()
    print("[STEP] Login exitoso", flush=True)
    time.sleep(3)

# ==============================================
#         NAVEGAR A NUEVO PROSPECTO
# ==============================================

def ir_a_nuevo_prospecto(driver):
    print("[STEP] Navegando a Nuevo Prospecto", flush=True)
    driver.get("https://cesuma.academic.lat/Admin/RegistrarProspecto.aspx")
    time.sleep(3)

# ==============================================
#         LLENAR FORMULARIO DE UNA SOLA INTERFAZ
# ==============================================

def llenar_formulario(driver, data):
    wait = WebDriverWait(driver, 30)

    print("[STEP] Llenando Datos Personales", flush=True)

    # --- Nombre
    try:
        driver.find_element(By.CSS_SELECTOR, SELECTORS["NOMBRE"]).clear()
        driver.find_element(By.CSS_SELECTOR, SELECTORS["NOMBRE"]).send_keys(data["nombre"])
    except Exception as e:
        print("Error llenando nombre:", e, flush=True)
        raise

    # --- Apellido paterno
    try:
        driver.find_element(By.CSS_SELECTOR, SELECTORS["APELLIDO_PATERNO"]).clear()
        driver.find_element(By.CSS_SELECTOR, SELECTORS["APELLIDO_PATERNO"]).send_keys(data["apellido_paterno"])
    except Exception as e:
        print("Error llenando apellido paterno:", e, flush=True)
        raise

    # --- Email
    try:
        driver.find_element(By.CSS_SELECTOR, SELECTORS["EMAIL"]).clear()
        driver.find_element(By.CSS_SELECTOR, SELECTORS["EMAIL"]).send_keys(data["email"])
    except Exception as e:
        print("Error llenando email:", e, flush=True)
        raise

    # --- Fecha nacimiento fija
    try:
        fn = driver.find_element(By.CSS_SELECTOR, SELECTORS["FECHA_NACIMIENTO"])
        fn.clear()
        fn.send_keys("01/01/2000")
    except Exception as e:
        print("Error llenando fecha nacimiento:", e, flush=True)
        raise

    # --- CURP / ID
    try:
        driver.find_element(By.CSS_SELECTOR, SELECTORS["CURP_ID"]).clear()
        driver.find_element(By.CSS_SELECTOR, SELECTORS["CURP_ID"]).send_keys(data["curp_id"])
    except Exception as e:
        print("Error llenando CURP:", e, flush=True)
        raise

    # --- Celular
    try:
        driver.find_element(By.CSS_SELECTOR, SELECTORS["CELULAR"]).clear()
        driver.find_element(By.CSS_SELECTOR, SELECTORS["CELULAR"]).send_keys(data["celular"])
    except Exception as e:
        print("Error llenando celular:", e, flush=True)
        raise

    # --- Checkbox podemos comunicarnos
    try:
        chk = driver.find_element(By.CSS_SELECTOR, SELECTORS["POD_COM"])
        if not chk.is_selected():
            chk.click()
    except Exception as e:
        print("Error clic POD_COM:", e, flush=True)
        raise

    print("[STEP] Llenando Datos Académicos", flush=True)

    # --- Oferta educativa
    sel_oferta_el = driver.find_element(By.CSS_SELECTOR, SELECTORS["OFERTA_EDUCATIVA"])
    select_oferta = Select(sel_oferta_el)
    select_oferta.select_by_visible_text(data["oferta"])
    time.sleep(3)  # recarga obligatoria

    # --- Periodo: primera opción disponible
    periodo_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["PERIODO"])))
    select_periodo = Select(periodo_el)
    select_periodo.select_by_index(1)

    # --- Tipo horario
    Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["TIPO_HORARIO"])).select_by_visible_text("MIXTO")

    # --- Departamento
    Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["DEPTO"])).select_by_visible_text("COMERCIAL CALI")

    # --- Estatus
    Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["ESTATUS"])).select_by_visible_text("PROSPECTO NUEVO")

    print("[STEP] Guardando", flush=True)
    btn_guardar = driver.find_element(By.CSS_SELECTOR, SELECTORS["BTN_GUARDAR"])
    driver.execute_script("arguments[0].scrollIntoView(true);", btn_guardar)
    time.sleep(1)
    driver.execute_script("arguments[0].click();", btn_guardar)
    time.sleep(4)

# ==============================================
#                 ENDPOINT
# ==============================================

@app.route("/cargar_prospecto", methods=["POST"])
def cargar_prospecto():
    if not CRM_URL or not CRM_USER or not CRM_PASS:
        return jsonify({"error": "Faltan variables de entorno CRM_URL, CRM_USER o CRM_PASS"}), 500

    data = request.get_json()
    print(f"Iniciando carga de prospecto: {data.get('nombre')}", flush=True)

    try:
        driver = make_driver()
        login_crm(driver)
        ir_a_nuevo_prospecto(driver)
        llenar_formulario(driver, data)
        driver.quit()
        return jsonify({"status": "success"})
    except Exception as e:
        print("Error total:", str(e), flush=True)
        try:
            driver.quit()
        except:
            pass
        return jsonify({"status": "error", "detail": str(e)}), 500

# ==============================================

@app.route("/")
def home():
    return "CRM Loader OK"

# ==============================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
