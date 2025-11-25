import os
import time
import json
from flask import Flask, request, jsonify

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)

# ==============================================================================
# 1) CONFIGURACIÓN INICIAL (Render Environment Variables)
# ==============================================================================
CRM_URL = os.environ.get("CRM_URL", "").strip()  # Debe ser tu URL real de login
CRM_USER = os.environ.get("CRM_USER", "").strip()
CRM_PASS = os.environ.get("CRM_PASS", "").strip()

# Ubicación de binarios en Render (agregar en Environment Variables)
CHROME_BIN = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

app = Flask(__name__)

# ==============================================================================
# 2) SELECTORES (ajusta si el CRM cambia IDs)
# ==============================================================================
SELECTORS = {
    # Login
    "USER_INPUT": "input[type='email']",
    "PASS_INPUT": "input[type='password']",
    "LOGIN_BTN": "button[type='submit']",

    # Flujo Familiar (Paso 1)
    "FAMILIA_DROPDOWN": "select[id*='ddlFamilia']",

    # Formulario Prospecto (Paso 2)
    "NOMBRE": "input[id*='txtNombre']",
    "APELLIDO_PATERNO": "input[id*='txtApellidoPaterno']",
    "SEXO": "select[id*='ddlSexo']",  # ya NO lo usaremos si es default en CRM
    "EMAIL": "input[id*='txtCorreoElectronico']",
    "FECHA_NACIMIENTO": "input[id*='txtFechaNacimiento']",
    "CURP_ID": "input[id*='txtID']",
    "TEL_CELULAR": "input[id*='txtTelefonoCelular']",
    "TEL_COMUNICARSE_CEL_CHECK": "input[id*='chkCelular']",

    # Datos de Programa (Paso 3)
    "OFERTA_EDUCATIVA": "select[id*='ddlOfertaEducativa']",
    "PERIODO": "select[id*='ddlPeriodo']",
    "TIPO_HORARIO": "select[id*='ddlHorario']",
    "DEPARTAMENTO_ASIGNADO": "select[id*='ddlDepartamentoAsignado']",
    "ESTATUS_SEGUIMIENTO": "select[id*='ddlEstatusSeguimiento']",

    # Botones
    "GUARDAR_BTN_XPATH": "//button[contains(., 'Guardar')]",
    "CONTINUAR_BTN_XPATH": "//button[contains(., 'Continuar')]",
}

# ==============================================================================
# 3) FUNCIÓN PRINCIPAL DE AUTOMATIZACIÓN
# ==============================================================================
def automatizar_crm(data: dict):
    """
    Recibe datos del prospecto y realiza la automatización en el CRM con Selenium.
    """
    if not CRM_URL or not CRM_USER or not CRM_PASS:
        return {
            "status": "error",
            "message": "Faltan variables de entorno CRM_URL, CRM_USER o CRM_PASS en Render."
        }

    chrome_options = Options()
    # Headless moderno para Chrome reciente
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = CHROME_BIN

    driver = None
    try:
        # Iniciar Chrome indicando ruta de chromedriver
        service = webdriver.chrome.service.Service(CHROMEDRIVER_PATH)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        driver.implicitly_wait(10)
        wait = WebDriverWait(driver, 25)

        # ---------------------------
        # 1) LOGIN
        # ---------------------------
        driver.get(CRM_URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["USER_INPUT"])))

        driver.find_element(By.CSS_SELECTOR, SELECTORS["USER_INPUT"]).send_keys(CRM_USER)
        driver.find_element(By.CSS_SELECTOR, SELECTORS["PASS_INPUT"]).send_keys(CRM_PASS)
        driver.find_element(By.CSS_SELECTOR, SELECTORS["LOGIN_BTN"]).click()

        wait.until(EC.url_changes(CRM_URL))

        # ---------------------------
        # 2) IR A NUEVO PROSPECTO
        # Ajusta la ruta si tu CRM usa otra URL interna
        # ---------------------------
        driver.get(CRM_URL.rstrip("/") + "/Prospecto/Nuevo")
        time.sleep(2)

        # ---------------------------
        # 3) PASO 1: FAMILIA
        # ---------------------------
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["FAMILIA_DROPDOWN"])))
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["FAMILIA_DROPDOWN"])) \
            .select_by_visible_text("No registrar")

        wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["CONTINUAR_BTN_XPATH"]))).click()

        # ---------------------------
        # 4) PASO 2: DATOS PERSONALES
        # ---------------------------
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["NOMBRE"])))

        driver.find_element(By.CSS_SELECTOR, SELECTORS["NOMBRE"]).send_keys(data.get("Nombre", ""))
        driver.find_element(By.CSS_SELECTOR, SELECTORS["APELLIDO_PATERNO"]).send_keys(data.get("Apellido Paterno", ""))
        driver.find_element(By.CSS_SELECTOR, SELECTORS["EMAIL"]).send_keys(data.get("Correo Electronico", ""))

        # Fecha fija siempre
        fecha_input = driver.find_element(By.CSS_SELECTOR, SELECTORS["FECHA_NACIMIENTO"])
        try:
            fecha_input.clear()
        except Exception:
            pass
        fecha_input.send_keys("01/01/2000")

        driver.find_element(By.CSS_SELECTOR, SELECTORS["CURP_ID"]).send_keys(data.get("CURP_ID", ""))
        driver.find_element(By.CSS_SELECTOR, SELECTORS["TEL_CELULAR"]).send_keys(data.get("Telefono Celular", ""))

        # ⚠️ Sexo NO se toca: el CRM lo deja por defecto.
        # Si alguna vez quieres activarlo dinámico, descomenta:
        # Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["SEXO"])) \
        #     .select_by_visible_text(data.get("Sexo", "Indistinto"))

        # Marcar casilla "Comunicarse"
        try:
            cel_checkbox = driver.find_element(By.CSS_SELECTOR, SELECTORS["TEL_COMUNICARSE_CEL_CHECK"])
            if not cel_checkbox.is_selected():
                cel_checkbox.click()
        except Exception:
            pass

        wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["CONTINUAR_BTN_XPATH"]))).click()

        # ---------------------------
        # 5) PASO 3: DATOS DE PROGRAMA
        # ---------------------------
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["OFERTA_EDUCATIVA"])))

        # Oferta educativa dinámica (viene de la hoja)
        oferta_value = (data.get("OFERTA_EDUCATIVA") or "").strip()
        if not oferta_value:
            return {
                "status": "error",
                "message": "OFERTA_EDUCATIVA viene vacía desde la hoja."
            }

        try:
            Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["OFERTA_EDUCATIVA"])) \
                .select_by_visible_text(oferta_value)
        except Exception:
            return {
                "status": "error",
                "message": f"La oferta educativa '{oferta_value}' no existe en el CRM o no coincide exactamente."
            }

        # Selects fijos (ajusta textos si en el CRM se llaman distinto)
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["PERIODO"])) \
            .select_by_visible_text("MIXTO")
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["TIPO_HORARIO"])) \
            .select_by_visible_text("MIXTO")
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["DEPARTAMENTO_ASIGNADO"])) \
            .select_by_visible_text("COMERCIAL CALI")
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["ESTATUS_SEGUIMIENTO"])) \
            .select_by_visible_text("PROSPECTO NUEVO")

        # ---------------------------
        # 6) GUARDAR
        # ---------------------------
        wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["GUARDAR_BTN_XPATH"]))).click()
        wait.until(EC.url_changes(driver.current_url))

        return {"status": "success", "message": "Prospecto cargado exitosamente."}

    except TimeoutException:
        return {"status": "error", "message": "Timeout esperando elementos del CRM."}
    except NoSuchElementException as e:
        return {"status": "error", "message": f"Elemento no encontrado en el CRM: {e}"}
    except WebDriverException as e:
        return {"status": "error", "message": f"Fallo del navegador (WebDriver): {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Error inesperado: {e}"}
    finally:
        if driver:
            driver.quit()


# ==============================================================================
# 4) RUTAS FLASK
# ==============================================================================
@app.route("/cargar_prospecto", methods=["POST", "OPTIONS"])
def handle_cargar_prospecto():
    # Preflight CORS
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Datos JSON no recibidos."}), 400

        resultado = automatizar_crm(data)
        response = jsonify(resultado)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 200

    except Exception as e:
        response = jsonify({"status": "error", "message": f"Fallo interno del servidor: {e}"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500


@app.route("/")
def health_check():
    return "CRM Loader Service is running.", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
