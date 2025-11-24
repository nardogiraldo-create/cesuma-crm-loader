app.py# app.py - Script de Automatización CRM (Selenium Headless)
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException
import time
import os

app = Flask(__name__)

# --- CONFIGURACIÓN DEL CRM ---
CRM_URL = "https://cesuma.academic.lat/Autenticacion.aspx"
CRM_USER = "jessica.obando@cesuma.mx"
CRM_PASS = "Rafaela2013" # Credencial confirmada
CRM_REGISTRO_URL = "https://cesuma.academic.lat/Modulos/Captacion/RegistroProspecto.aspx" # URL directa del formulario

# --- Mapeo de Selectores Dedudicos (AJUSTAR EN CASO DE ERROR) ---
# Se usan selectores genéricos o parciales (ej. id*=) para mayor robustez
SELECTORS = {
    # Login
    "USER_INPUT": "input[type='email']", 
    "PASS_INPUT": "input[type='password']",
    "LOGIN_BTN": "button[type='submit']", 
    
    # Flujo Familiar (Paso 1)
    "FAMILIA_DROPDOWN": "select[id*='ddlFamilia']", 
    "CONTINUAR_BTN": "input[id*='btnContinuar']", # Busca el botón con ID que contenga 'btnContinuar'
    
    # Formulario Prospecto (Paso 2)
    "NOMBRE": "input[id*='txtNombre']", 
    "APELLIDO_PATERNO": "input[id*='txtApellidoPaterno']",
    "SEXO": "select[id*='ddlSexo']",
    "EMAIL": "input[id*='txtCorreoElectronico']",
    "FECHA_NACIMIENTO": "input[id*='txtFechaNacimiento']",
    "CURP_ID": "input[id*='txtID']", 
    "TEL_CELULAR": "input[id*='txtTelefonoCelular']",
    "TEL_COMUNICARSE_CEL_CHECK": "input[id*='chkCelular']", 
    "TEL_COMUNICARSE_FIJO_CHECK": "input[id*='chkFijo']", 

    # Datos de Programa (Paso 3)
    "OFERTA_EDUCATIVA": "select[id*='ddlOfertaEducativa']",
    "PERIODO": "select[id*='ddlPeriodo']",
    "TIPO_HORARIO": "select[id*='ddlHorario']",
    "DEPARTAMENTO_ASIGNADO": "select[id*='ddlDepartamentoAsignado']",
    "ESTATUS_SEGUIMIENTO": "select[id*='ddlEstatusSeguimiento']",
    "GUARDAR_BTN": "input[id*='btnGuardar']"
}

# --- FUNCIÓN PRINCIPAL DE AUTOMATIZACIÓN ---
def automatizar_crm(data):
    """Automatiza la carga de un prospecto en el CRM."""
    
    # Configuración de opciones Headless para Render
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Render puede requerir especificar la ruta del driver, aunque a menudo lo gestiona
    # Asegúrate de que el entorno de Render tenga el driver de Chrome disponible
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # 1. LOGIN
        driver.get(CRM_URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["USER_INPUT"])))

        driver.find_element(By.CSS_SELECTOR, SELECTORS["USER_INPUT"]).send_keys(CRM_USER)
        driver.find_element(By.CSS_SELECTOR, SELECTORS["PASS_INPUT"]).send_keys(CRM_PASS)
        driver.find_element(By.CSS_SELECTOR, SELECTORS["LOGIN_BTN"]).click()
        
        # Esperar hasta que la URL cambie (éxito en login)
        wait.until(EC.url_to_be("https://cesuma.academic.lat/Menu.aspx")) # Asume que el menú principal es Menu.aspx
        
        # 2. NAVEGACIÓN DIRECTA AL REGISTRO
        driver.get(CRM_REGISTRO_URL)
        time.sleep(2) # Pequeña espera para asegurar la carga

        # 3. PASO 1: INFORMACIÓN FAMILIAR (Familia: No registrar, Clic en Continuar)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["FAMILIA_DROPDOWN"])))
        
        # Seleccionar "No registrar" (Asume que es el valor de la opción, ej. el índice 0 o 1)
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["FAMILIA_DROPDOWN"])).select_by_visible_text("No registrar")
        
        driver.find_element(By.CSS_SELECTOR, SELECTORS["CONTINUAR_BTN"]).click()
        time.sleep(1.5)

        # 4. PASO 2: INFORMACIÓN DEL PROSPECTO (Llenado de datos)
        # Esperar a que el campo de nombre sea visible
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["NOMBRE"])))
        
        # Llenar campos de texto (los datos de Apps Script ya vienen en MAYÚSCULAS)
        driver.find_element(By.CSS_SELECTOR, SELECTORS["NOMBRE"]).send_keys(data['nombre'])
        driver.find_element(By.CSS_SELECTOR, SELECTORS["APELLIDO_PATERNO"]).send_keys(data['apellido_paterno'])
        driver.find_element(By.CSS_SELECTOR, SELECTORS["EMAIL"]).send_keys(data['email'])
        driver.find_element(By.CSS_SELECTOR, SELECTORS["CURP_ID"]).send_keys(data['curp_id'])
        driver.find_element(By.CSS_SELECTOR, SELECTORS["TEL_CELULAR"]).send_keys(data['telefono_celular'])
        
        # Valores fijos:
        driver.find_element(By.CSS_SELECTOR, SELECTORS["FECHA_NACIMIENTO"]).send_keys("01/01/2001")
        
        # Seleccionar Sexo: MASCULINO
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["SEXO"])).select_by_visible_text("Masculino")
        
        # Clic en "Podemos comunicarnos" para Celular y Fijo
        # Se asume que estos son visibles y clickeables
        driver.find_element(By.CSS_SELECTOR, SELECTORS["TEL_COMUNICARSE_CEL_CHECK"]).click() 
        driver.find_element(By.CSS_SELECTOR, SELECTORS["TEL_COMUNICARSE_FIJO_CHECK"]).click()
        
        # 5. PASO 3: DATOS DE PROGRAMA (Selecciones)
        
        # Oferta Educativa: (El valor debe coincidir con el texto de la opción)
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["OFERTA_EDUCATIVA"])).select_by_visible_text(data['oferta_educativa'])

        # Periodo: PRIMERA OPCIÓN - Se selecciona por el texto exacto
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["PERIODO"])).select_by_visible_text(data['periodo'])
        
        # Tipo Horario: Mixto
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["TIPO_HORARIO"])).select_by_visible_text("Mixto")
        
        # Departamento Asignado: COMERCIAL CALI - SEGUNDA OPCIÓN (Usamos texto visible)
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["DEPARTAMENTO_ASIGNADO"])).select_by_visible_text("COMERCIAL CALI")
        
        # Estatus de Seguimiento: PROSPECTO NUEVO - PRIMERA OPCIÓN (Usamos texto visible)
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["ESTATUS_SEGUIMIENTO"])).select_by_visible_text("PROSPECTO NUEVO")
        
        # 6. GUARDAR
        driver.find_element(By.CSS_SELECTOR, SELECTORS["GUARDAR_BTN"]).click()
        
        # Esperar confirmación (ej. URL cambia o aparece un mensaje de éxito)
        # Esto puede variar. Aquí esperamos que el botón "Guardar" desaparezca o la URL cambie.
        wait.until(EC.staleness_of(driver.find_element(By.CSS_SELECTOR, SELECTORS["GUARDAR_BTN"])))
        
        return {"status": "success", "message": "Prospecto cargado exitosamente."}
        
    except NoSuchElementException:
        return {"status": "error", "message": "Fallo Selenium: Selector de elemento no encontrado. Revisar el mapeo del CRM."}
    except TimeoutException:
        return {"status": "error", "message": "Fallo Selenium: Tiempo de espera agotado. El CRM tardó demasiado en cargar."}
    except WebDriverException as e:
        # Errores relacionados con el driver o el navegador (ej. Headless no funciona)
        return {"status": "error", "message": f"Fallo WebDriver: Problema con el navegador o el entorno de Render. {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Error inesperado durante la automatización: {str(e)}"}
    finally:
        driver.quit() # ¡Es VITAL cerrar el navegador Headless!

@app.route('/cargar_prospecto', methods=['POST'])
def cargar_prospecto():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No se recibieron datos JSON"}), 400
        
    resultado = automatizar_crm(data)
    return jsonify(resultado)

# Configuración básica para Render. Render usará Gunicorn para ejecutar esto.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
