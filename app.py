from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

app = FastAPI(title="Academic CRM Uploader")

API_TOKEN = os.getenv("API_TOKEN", "cambia-esto-por-tu-token")
CRM_URL   = "https://cesuma.academic.lat/Autenticacion.aspx"
CRM_USER  = os.getenv("CRM_USER", "")
CRM_PASS  = os.getenv("CRM_PASSWORD", "")


class ProcessRowRequest(BaseModel):
    token: str
    spreadsheet_id: str
    spreadsheet_name: str
    sheet_name: str
    row_number: int
    nombre: str
    apellido: str
    correo: str
    telefono: str


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    options.binary_location = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    driver = webdriver.Chrome(
        executable_path=os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"),
        options=options
    )
    driver.set_page_load_timeout(30)
    return driver


def wait_for(driver, by, selector, timeout=15):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )


def registrar_en_crm(nombre, apellido, correo, telefono):
    driver = get_driver()
    try:
        # ── 1. LOGIN ──────────────────────────────────────────────────────────
        driver.get(CRM_URL)
        wait_for(driver, By.ID, "txtUsuario")

        driver.find_element(By.ID, "txtUsuario").clear()
        driver.find_element(By.ID, "txtUsuario").send_keys(CRM_USER)
        driver.find_element(By.ID, "txtContrasenia").clear()
        driver.find_element(By.ID, "txtContrasenia").send_keys(CRM_PASS)
        driver.find_element(By.ID, "lnkEntrar").click()

        WebDriverWait(driver, 20).until(
            EC.url_contains("Principal.aspx")
        )

        # ── 2. NAVEGAR A CAPTACIÓN ────────────────────────────────────────────
        driver.get("https://cesuma.academic.lat/Admin/Principal.aspx")
        time.sleep(2)

        wait_for(driver, By.XPATH, "//a[contains(text(),'Captación y atención') or contains(text(),'Captacion y atencion')]")
        driver.find_element(By.XPATH, "//a[contains(text(),'Captación y atención') or contains(text(),'Captacion y atencion')]").click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//a[contains(text(),'Seguimiento')]").click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//a[contains(text(),'Captación') or contains(text(),'Captacion')]").click()
        time.sleep(2)

        # ── 3. NUEVO REGISTRO ─────────────────────────────────────────────────
        wait_for(driver, By.ID, "ctl00_ctl00_cphContentMain_cphFiltro_lnkNuevo")
        driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphFiltro_lnkNuevo").click()
        time.sleep(2)

        # ── 4. LLENAR FORMULARIO ──────────────────────────────────────────────
        Select(wait_for(driver, By.ID, "ctl00_ctl00_cphContentMain_cphContenido_ddlFamExist")).select_by_value("0")

        campo = wait_for(driver, By.ID, "ctl00_ctl00_cphContentMain_cphContenido_txtNombre")
        campo.clear()
        campo.send_keys(nombre)

        campo = driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphContenido_txtApellidoP")
        campo.clear()
        campo.send_keys(apellido)

        campo = driver.find_element(By.ID, "txtFechaNac")
        campo.clear()
        campo.send_keys("01/01/2000")

        campo = driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphContenido_txtEmail")
        campo.clear()
        campo.send_keys(correo)

        campo = driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphContenido_txtCel")
        campo.clear()
        campo.send_keys(telefono)

        # Oferta educativa = 43 (DOCTORADO EN EDUCACIÓN)
        Select(driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphContenido_ddlOferta")).select_by_value("43")
        time.sleep(2)

        # Periodo = 47 (Abr 26-Jul 26)
        driver.execute_script("SeleccionarPeriodo('Abr 26-Jul 26','47')")
        time.sleep(2)

        # Tipo horario = 1 (MIXTO)
        Select(driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphContenido_ddlTipoHorarioInsc")).select_by_value("1")

        # Departamento = 8 (COMERCIAL Posición Global)
        Select(driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphContenido_ddlDepartamento")).select_by_value("8")

        # Estatus = 1 (PROSPECTO NUEVO)
        Select(driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphContenido_ddlEstatusSeguimiento")).select_by_value("1")

        # ── 5. GUARDAR ────────────────────────────────────────────────────────
        driver.find_element(By.ID, "ctl00_ctl00_cphContentMain_cphContenido_lnkGuardar").click()
        time.sleep(3)

        # ── 6. LEER RESULTADO ─────────────────────────────────────────────────
        page_text = driver.page_source.upper()

        if "YA CUENTA CON UN REGISTRO" in page_text or "COINCIDENCIA FUERTE" in page_text:
            resultado = "FUERTE"
            detalle   = "Registro ya existe en la base de datos"
        elif "COINCIDENCIA" in page_text and ("DÉBIL" in page_text or "DEBIL" in page_text):
            resultado = "DEBIL"
            detalle   = "Coincidencia débil detectada"
        else:
            resultado = "AGREGADO"
            detalle   = "Registro creado exitosamente"

        return {
            "ok": True,
            "estado": "FINALIZADO",
            "resultado": resultado,
            "detalle": detalle,
            "fecha_proceso": datetime.utcnow().isoformat()
        }

    except TimeoutException as e:
        return {
            "ok": False,
            "estado": "ERROR",
            "resultado": "",
            "detalle": f"TIMEOUT: {str(e)[:120]}",
            "fecha_proceso": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "ok": False,
            "estado": "ERROR",
            "resultado": "",
            "detalle": f"ERROR: {str(e)[:120]}",
            "fecha_proceso": datetime.utcnow().isoformat()
        }
    finally:
        driver.quit()


@app.get("/")
def root():
    return {"ok": True, "message": "Servicio activo"}


@app.post("/process-row")
def process_row(payload: ProcessRowRequest):
    if payload.token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token inválido")

    nombre   = payload.nombre.strip().upper()
    apellido = payload.apellido.strip().upper()
    correo   = payload.correo.strip()
    telefono = payload.telefono.strip()

    if not nombre or not apellido or not correo or not telefono:
        return {
            "ok": False,
            "estado": "ERROR",
            "resultado": "",
            "detalle": "DATOS INCOMPLETOS",
            "fecha_proceso": datetime.utcnow().isoformat()
        }

    return registrar_en_crm(nombre, apellido, correo, telefono)
