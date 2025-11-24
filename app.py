import os
import time
import json
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# ==============================================================================
# 1. CONFIGURACIÓN INICIAL
# Render usará estas variables de entorno, definidas en el dashboard de Render.
# Se usan valores predeterminados de ejemplo si no están definidos.
# ==============================================================================
CRM_URL = os.environ.get("CRM_URL", "https://tucrm.com/pagina_de_login")
CRM_USER = os.environ.get("CRM_USER", "usuario@ejemplo.com")
CRM_PASS = os.environ.get("CRM_PASS", "tu_contraseña_segura")

app = Flask(__name__)

# Mapeo de selectores (IDs o CSS) basado en la estructura de las imágenes del CRM
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
    "SEXO": "select[id*='ddlSexo']",
    "EMAIL": "input[id*='txtCorreoElectronico']",
    "FECHA_NACIMIENTO": "input[id*='txtFechaNacimiento']",
    "CURP_ID": "input[id*='txtID']", 
    "TEL_CELULAR": "input[id*='txtTelefonoCelular']",
    # Casilla para indicar si el celular es para comunicarse
    "TEL_COMUNICARSE_CEL_CHECK": "input[id*='chkCelular']", 
    
    # Datos de Programa (Paso 3)
    "OFERTA_EDUCATIVA": "select[id*='ddlOfertaEducativa']",
    "PERIODO": "select[id*='ddlPeriodo']",
    "TIPO_HORARIO": "select[id*='ddlHorario']",
    "DEPARTAMENTO_ASIGNADO": "select[id*='ddlDepartamentoAsignado']",
    "ESTATUS_SEGUIMIENTO": "select[id*='ddlEstatusSeguimiento']",
    
    # Botones
    "GUARDAR_BTN_XPATH": "//button[contains(., 'Guardar')]", 
    "CONTINUAR_BTN_XPATH": "//button[contains(., 'Continuar')]"
}

# ==============================================================================
# 2. FUNCIÓN PRINCIPAL DE AUTOMATIZACIÓN CON SELENIUM
# ==============================================================================
def automatizar_crm(data):
    """
    Recibe los datos del prospecto y realiza la automatización en el CRM.
    
    Args:
        data (dict): Datos del prospecto desde Google Apps Script.
    """
    
    # 1. Configuración de opciones Headless para Render
    chrome_options = Options()
    # Parámetros cruciales para que Chrome corra en un entorno Linux Headless
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Configuración específica para Render usando CHROME_BIN
    # Esto ayuda a Selenium a encontrar el binario de Chrome instalado
    if 'CHROME_BIN' in os.environ:
        chrome_options.binary_location = os.environ['CHROME_BIN']
        
    driver = None # Inicializar driver fuera del try para el finally
    
    try:
        # Inicializar el driver de Chrome con las opciones configuradas
        driver = webdriver.Chrome(options=chrome_options)
        # Espera implícita y explícita para cargar elementos
        driver.implicitly_wait(10)
        wait = WebDriverWait(driver, 20)
        
        # 1. LOGIN
        driver.get(CRM_URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["USER_INPUT"])))
        
        driver.find_element(By.CSS_SELECTOR, SELECTORS["USER_INPUT"]).send_keys(CRM_USER)
        driver.find_element(By.CSS_SELECTOR, SELECTORS["PASS_INPUT"]).send_keys(CRM_PASS)
        driver.find_element(By.CSS_SELECTOR, SELECTORS["LOGIN_BTN"]).click()
        
        # Esperar a que el login sea exitoso (cambio de URL o aparición de un elemento post-login)
        wait.until(EC.url_changes(CRM_URL))
        
        # Navegar a la página de nuevo prospecto (Ajustar según la URL real)
        # Si esta URL no existe o es incorrecta, el script fallará.
        driver.get(CRM_URL + "/Prospecto/Nuevo") 
        time.sleep(2) # Pausa para asegurar que la página de prospecto cargue
        
        # 2. PASO 1: INFORMACIÓN FAMILIAR
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["FAMILIA_DROPDOWN"])))
        
        # Seleccionar "No registrar" en el dropdown de familia
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["FAMILIA_DROPDOWN"])).select_by_visible_text("No registrar")
        
        # Clic en el botón "Continuar" usando XPath para buscar el texto del botón
        wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["CONTINUAR_BTN_XPATH"]))).click()
        
        # 3. PASO 2: INFORMACIÓN DEL PROSPECTO 
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["NOMBRE"])))
        
        # Llenar campos de texto
        driver.find_element(By.CSS_SELECTOR, SELECTORS["NOMBRE"]).send_keys(data.get("Nombre", ""))
        driver.find_element(By.CSS_SELECTOR, SELECTORS["APELLIDO_PATERNO"]).send_keys(data.get("Apellido Paterno", ""))
        driver.find_element(By.CSS_SELECTOR, SELECTORS["EMAIL"]).send_keys(data.get("Correo Electronico", ""))
        driver.find_element(By.CSS_SELECTOR, SELECTORS["FECHA_NACIMIENTO"]).send_keys(data.get("Fecha Nacimiento", ""))
        driver.find_element(By.CSS_SELECTOR, SELECTORS["CURP_ID"]).send_keys(data.get("CURP_ID", ""))
        driver.find_element(By.CSS_SELECTOR, SELECTORS["TEL_CELULAR"]).send_keys(data.get("Telefono Celular", ""))

        # Seleccionar Sexo
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["SEXO"])).select_by_visible_text(data.get("Sexo", "Indistinto"))
        
        # Marcar casilla "Comunicarse"
        cel_checkbox = driver.find_element(By.CSS_SELECTOR, SELECTORS["TEL_COMUNICARSE_CEL_CHECK"])
        if not cel_checkbox.is_selected():
             cel_checkbox.click()
             
        # Clic en "Continuar" para pasar al paso 3
        wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["CONTINUAR_BTN_XPATH"]))).click()

        # 4. PASO 3: DATOS DE PROGRAMA
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["OFERTA_EDUCATIVA"])))
        
        # Seleccionar campos fijos o predeterminados
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["OFERTA_EDUCATIVA"])).select_by_visible_text("DOCTORADO EN EDUCACIÓN")
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["PERIODO"])).select_by_visible_text("MIXTO")
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["TIPO_HORARIO"])).select_by_visible_text("COMERCIAL CALI")
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["DEPARTAMENTO_ASIGNADO"])).select_by_visible_text("COMERCIAL CALI")
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["ESTATUS_SEGUIMIENTO"])).select_by_visible_text("PROSPECTO NUEVO")
        
        # 5. GUARDAR
        # Clic en el botón "Guardar"
        wait.until(EC.element_to_be_clickable((By.XPATH, SELECTORS["GUARDAR_BTN_XPATH"]))).click()
        
        # Esperar a que la URL cambie (confirmando que la acción de guardar fue exitosa)
        wait.until(EC.url_changes(driver.current_url)) 
        
        return {"status": "success", "message": "Prospecto cargado exitosamente."}
        
    except TimeoutException:
        print("Error: Timeout al esperar un elemento.")
        return {"status": "error", "message": "Tiempo de espera agotado (Timeout) durante la automatización."}
    except NoSuchElementException as e:
        print(f"Error: Elemento no encontrado: {e}")
        return {"status": "error", "message": f"Elemento no encontrado en el CRM. El selector falló: {e}"}
    except WebDriverException as e:
        print(f"Error del WebDriver: {e}")
        return {"status": "error", "message": f"Fallo del navegador (WebDriver): {e}"}
    except Exception as e:
        print(f"Error general: {e}")
        return {"status": "error", "message": f"Error inesperado: {e}"}
    finally:
        if driver:
            # Asegurar que el navegador se cierre para liberar recursos en Render
            driver.quit()

# ==============================================================================
# 3. RUTAS DE FLASK
# ==============================================================================
@app.route('/cargar_prospecto', methods=['POST'])
def handle_cargar_prospecto():
    """
    Endpoint principal llamado por Google Apps Script.
    Recibe un JSON con los datos del prospecto y llama a la automatización.
    """
    # Manejar solicitud OPTIONS (preflight CORS)
    if request.method == 'OPTIONS':
        # Responder con éxito y los encabezados CORS necesarios
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    # Manejar solicitud POST
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "Datos JSON no recibidos."}), 400
        
        print(f"Iniciando carga de prospecto: {data.get('Nombre')}")
        
        # Ejecutar la lógica de automatización
        resultado = automatizar_crm(data)
        
        # Devolver la respuesta a Google Apps Script
        response = jsonify(resultado)
        response.headers.add('Access-Control-Allow-Origin', '*') # CORS
        return response, 200

    except Exception as e:
        print(f"Error en el endpoint: {e}")
        response = jsonify({"status": "error", "message": f"Fallo interno del servidor: {e}"})
        response.headers.add('Access-Control-Allow-Origin', '*') # CORS
        return response, 500

@app.route('/')
def health_check():
    """Ruta para verificar que el servicio está corriendo (Health Check de Render)."""
    return "CRM Loader Service is running.", 200

# ==============================================================================
# 4. INICIO DE LA APLICACIÓN (Solo para testing local, Gunicorn la ignora)
# ==============================================================================
if __name__ == '__main__':
    # Nota: Render usa Gunicorn, esta parte solo es útil para pruebas locales
    app.run(host='0.0.0.0', port=5000)
