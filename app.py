import os
import re
import time
import logging
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
CRM_URL = os.environ.get("CRM_URL", "").strip()
CRM_USER = os.environ.get("CRM_USER", "").strip()
CRM_PASS = os.environ.get("CRM_PASS", "").strip()

CHROME_BIN = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

DEFAULT_TIMEOUT = int(os.environ.get("SELENIUM_TIMEOUT", "40"))
MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("crm-loader")

# Validate env early
if not all([CRM_URL, CRM_USER, CRM_PASS]):
    logger.warning("⚠️ Faltan variables de entorno CRM_URL, CRM_USER o CRM_PASS. El servicio fallará al cargar.")

# ------------------------------------------------------------
# APP
# ------------------------------------------------------------
app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return "ok", 200

@app.get("/health")
def health():
    # health simple para que puedas probar en navegador
    return jsonify({"status": "ok"}), 200


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def validate_payload(data: Dict[str, Any]) -> Optional[str]:
    required = ["nombre", "apellido_paterno", "email", "celular", "curp_id", "oferta"]
    for k in required:
        if k not in data or str(data[k]).strip() == "":
            return f"Falta o está vacío el campo: {k}"

    # email simple
    email = str(data["email"]).strip()
    if "@" not in email or "." not in email:
        return "Email inválido"

    # celular: mínimo 10 dígitos
    celular = re.sub(r"\D", "", str(data["celular"]))
    if len(celular) < 10:
        return "Celular inválido (mínimo 10 dígitos)"

    return None


def make_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1366,768")
    chrome_options.add_argument("--lang=es-ES")
    chrome_options.add_argument("--disable-notifications")

    # buscar binario de chrome en varias rutas
    chrome_candidates = [
        os.environ.get("CHROME_BIN", ""),
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome"
    ]
    for p in chrome_candidates:
        if p and os.path.exists(p):
            chrome_options.binary_location = p
            logger.info(f"✅ Chrome encontrado en: {p}")
            break

    # buscar chromedriver en varias rutas
    driver_candidates = [
        os.environ.get("CHROMEDRIVER_PATH", ""),
        "/usr/bin/chromedriver",
        "/usr/lib/chromium/chromedriver",
        "/usr/lib/chromium-browser/chromedriver"
    ]
    driver_path = None
    for p in driver_candidates:
        if p and os.path.exists(p):
            driver_path = p
            logger.info(f"✅ ChromeDriver encontrado en: {p}")
            break

    if not driver_path:
        raise RuntimeError(f"❌ ChromeDriver no encontrado. Revisar rutas: {driver_candidates}")

    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(90)
    return driver



def wait(driver, t=DEFAULT_TIMEOUT):
    return WebDriverWait(driver, t)


def safe_quit(driver):
    try:
        driver.quit()
    except Exception:
        pass


def login_crm(driver):
    driver.get(CRM_URL)

    # Ajusta estos selectores a tu CRM real:
    # (son ejemplos robustos con múltiples posibilidades)

    # Usuario
    user_input = wait(driver).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "input[type='email'], input[name='username'], input[id*='usuario'], input[id*='user']"
        ))
    )
    user_input.clear()
    user_input.send_keys(CRM_USER)

    # Password
    pass_input = wait(driver).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "input[type='password'], input[name='password'], input[id*='contrasena'], input[id*='pass']"
        ))
    )
    pass_input.clear()
    pass_input.send_keys(CRM_PASS)

    # Botón login
    login_btn = wait(driver).until(
        EC.element_to_be_clickable((
            By.CSS_SELECTOR,
            "button[type='submit'], button[id*='login'], input[type='submit']"
        ))
    )
    login_btn.click()

    # Esperar panel/logueo
    wait(driver, 60).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    logger.info("✅ Login OK")


def open_registrar_prospecto(driver):
    # Ajusta navegación real si tu CRM requiere ir a menú específico.
    # Aquí buscamos un botón/label "Registrar prospecto"
    btn = wait(driver, 60).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'registrar prospecto') or contains(@aria-label,'Registrar prospecto')]"
        ))
    )
    btn.click()
    logger.info("✅ Abierta pantalla de registro")


def fill_form(driver, data: Dict[str, Any]):
    # ---- Paso 1 / Datos personales ----
    # NOTA: Ajusta selectores según HTML real del CRM.

    def type_in(css_list, value):
        for css in css_list:
            els = driver.find_elements(By.CSS_SELECTOR, css)
            if els:
                el = els[0]
                el.clear()
                el.send_keys(value)
                return True
        raise NoSuchElementException(f"No se encontró input para {css_list}")

    # nombre
    type_in(["input[id*='Nombre']", "input[name*='nombre']", "input[placeholder*='Nombre']"],
            data["nombre"])

    # apellido paterno
    type_in(["input[id*='Apellido']", "input[name*='apellido']", "input[placeholder*='Apellido']"],
            data["apellido_paterno"])

    # email
    type_in(["input[type='email']", "input[id*='Correo']", "input[name*='email']"],
            data["email"])

    # fecha nacimiento (fija)
    type_in(["input[id*='Fecha']", "input[name*='nacimiento']"],
            "01/01/2000")

    # curp / id
    type_in(["input[id*='CURP']", "input[name*='curp']", "input[id*='ID']"],
            data["curp_id"])

    # celular
    type_in(["input[id*='Celular']", "input[name*='celular']", "input[id*='Movil']"],
            data["celular"])

    # checkboxes “Podemos comunicarnos”
    for chk in driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
        try:
            if not chk.is_selected():
                chk.click()
        except Exception:
            continue

    # ---- Paso 2 / Oferta educativa ----
    # Oferta educativa
    oferta_select = wait(driver, 40).until(
        EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "select[id*='Oferta'], select[name*='oferta'], select"
        ))
    )
    Select(oferta_select).select_by_visible_text(data["oferta"])

    # esperar cascada si hay
    time.sleep(1)

    # Periodo (si existe, toma primera opción no vacía)
    periodos = driver.find_elements(By.CSS_SELECTOR, "select[id*='Periodo'], select[name*='periodo']")
    if periodos:
        sel = Select(periodos[0])
        for opt in sel.options:
            if opt.get_attribute("value") and opt.text.strip():
                sel.select_by_visible_text(opt.text)
                break

    # Tipo de horario mixto (si existe)
    horarios = driver.find_elements(By.CSS_SELECTOR, "select[id*='Horario'], select[name*='horario']")
    if horarios:
        sel = Select(horarios[0])
        try:
            sel.select_by_visible_text("Mixto")
        except Exception:
            # fallback primera opción válida
            for opt in sel.options:
                if opt.get_attribute("value") and opt.text.strip():
                    sel.select_by_visible_text(opt.text)
                    break

    # Departamento asignado (si existe)
    deptos = driver.find_elements(By.CSS_SELECTOR, "select[id*='Departamento'], select[name*='departamento']")
    if deptos:
        sel = Select(deptos[0])
        try:
            sel.select_by_visible_text("COMERCIAL CALI")
        except Exception:
            pass

    # Estatus seguimiento (si existe)
    estatus = driver.find_elements(By.CSS_SELECTOR, "select[id*='Estatus'], select[name*='estatus']")
    if estatus:
        sel = Select(estatus[0])
        try:
            sel.select_by_visible_text("PROSPECTO NUEVO")
        except Exception:
            pass

    # Guardar
    guardar_btn = wait(driver, 40).until(
        EC.element_to_be_clickable((
            By.XPATH,
            "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'guardar') or contains(@aria-label,'Guardar')]"
        ))
    )
    guardar_btn.click()

    # Confirmación / éxito
    wait(driver, 60).until(
        EC.presence_of_element_located((
            By.XPATH,
            "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'exitoso') or contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'guardado')]"
        ))
    )
    logger.info(f"✅ Prospecto creado: {data['nombre']} {data['apellido_paterno']}")


def process_prospect(data: Dict[str, Any]) -> Dict[str, Any]:
    driver = None
    try:
        driver = make_driver()
        login_crm(driver)
        open_registrar_prospecto(driver)
        fill_form(driver, data)
        return {"status": "success"}
    finally:
        if driver:
            safe_quit(driver)


# ------------------------------------------------------------
# ENDPOINT
# ------------------------------------------------------------
@app.post("/cargar_prospecto")
def cargar_prospecto():
    data = request.get_json(force=True, silent=True) or {}
    logger.info(f"➡️ Iniciando carga de prospecto: {data.get('nombre','(sin nombre)')}")

    err = validate_payload(data)
    if err:
        return jsonify({"status": "error", "detail": err}), 400

    last_error = None

    for intento in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"🔁 Intento {intento}/{MAX_RETRIES}")
            resp = process_prospect(data)
            return jsonify(resp), 200
        except (TimeoutException, WebDriverException, NoSuchElementException) as e:
            last_error = str(e)
            logger.warning(f"⚠️ Error temporal: {last_error}")

            if intento < MAX_RETRIES:
                backoff = 2 ** intento
                time.sleep(backoff)
                continue
        except Exception as e:
            last_error = str(e)
            logger.exception("❌ Error no controlado")
            break

    return jsonify({"status": "error", "detail": last_error or "Error desconocido"}), 500


# Para apps WSGI tipo Render/Gunicorn, no hace falta app.run()
