from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import os
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

app = FastAPI(title="Academic CRM Uploader")

API_TOKEN = os.getenv("API_TOKEN", "cambia-esto-por-tu-token")
CRM_URL     = "https://cesuma.academic.lat/Autenticacion.aspx"
CRM_USER    = os.getenv("CRM_USER", "")
CRM_PASS    = os.getenv("CRM_PASSWORD", "")

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

    resultado = asyncio.run(registrar_en_crm(nombre, apellido, correo, telefono))
    return resultado


async def registrar_en_crm(nombre, apellido, correo, telefono):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page    = await context.new_page()

        try:
            # ── 1. LOGIN ──────────────────────────────────────────────────────
            await page.goto(CRM_URL, wait_until="networkidle", timeout=30000)

            await page.fill("#txtUsuario",     CRM_USER)
            await page.fill("#txtContrasenia", CRM_PASS)
            await page.click("#lnkEntrar")
            await page.wait_for_url("**/Principal.aspx", timeout=20000)

            # ── 2. NAVEGAR A CAPTACIÓN ────────────────────────────────────────
            await page.goto(
                "https://cesuma.academic.lat/Admin/Principal.aspx",
                wait_until="networkidle", timeout=20000
            )
            # Menú: Captación y atención → Seguimiento → Captación
            await page.click("text=Captación y atención")
            await page.click("text=Seguimiento")
            await page.click("text=Captación")
            await page.wait_for_load_state("networkidle", timeout=15000)

            # ── 3. NUEVO REGISTRO ─────────────────────────────────────────────
            await page.click("#ctl00_ctl00_cphContentMain_cphFiltro_lnkNuevo")
            await page.wait_for_load_state("networkidle", timeout=15000)

            # ── 4. LLENAR FORMULARIO ──────────────────────────────────────────
            # Familia = No registrar (valor 0)
            await page.select_option(
                "#ctl00_ctl00_cphContentMain_cphContenido_ddlFamExist", "0"
            )

            await page.fill(
                "#ctl00_ctl00_cphContentMain_cphContenido_txtNombre", nombre
            )
            await page.fill(
                "#ctl00_ctl00_cphContentMain_cphContenido_txtApellidoP", apellido
            )
            await page.fill("#txtFechaNac", "01/01/2000")
            await page.fill(
                "#ctl00_ctl00_cphContentMain_cphContenido_txtEmail", correo
            )
            await page.fill(
                "#ctl00_ctl00_cphContentMain_cphContenido_txtCel", telefono
            )

            # Oferta educativa = 43 (DOCTORADO EN EDUCACIÓN)
            await page.select_option(
                "#ctl00_ctl00_cphContentMain_cphContenido_ddlOferta", "43"
            )
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Periodo = 47 (Abr 26-Jul 26)
            await page.evaluate("SeleccionarPeriodo('Abr 26-Jul 26','47')")
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Tipo horario = 1 (MIXTO)
            await page.select_option(
                "#ctl00_ctl00_cphContentMain_cphContenido_ddlTipoHorarioInsc", "1"
            )

            # Departamento = 8 (COMERCIAL Posición Global)
            await page.select_option(
                "#ctl00_ctl00_cphContentMain_cphContenido_ddlDepartamento", "8"
            )

            # Estatus = 1 (PROSPECTO NUEVO)
            await page.select_option(
                "#ctl00_ctl00_cphContentMain_cphContenido_ddlEstatusSeguimiento", "1"
            )

            # ── 5. GUARDAR ────────────────────────────────────────────────────
            await page.click(
                "#ctl00_ctl00_cphContentMain_cphContenido_lnkGuardar"
            )
            await page.wait_for_load_state("networkidle", timeout=20000)

            # ── 6. LEER RESULTADO ─────────────────────────────────────────────
            page_text = (await page.content()).upper()

            if "YA CUENTA CON UN REGISTRO" in page_text or "COINCIDENCIA FUERTE" in page_text:
                resultado  = "FUERTE"
                detalle    = "Registro ya existe en la base de datos"
            elif "COINCIDENCIA DÉBIL" in page_text or "COINCIDENCIA DEBIL" in page_text:
                resultado  = "DEBIL"
                detalle    = "Coincidencia débil detectada"
            else:
                resultado  = "AGREGADO"
                detalle    = "Registro creado exitosamente"

            return {
                "ok": True,
                "estado": "FINALIZADO",
                "resultado": resultado,
                "detalle": detalle,
                "fecha_proceso": datetime.utcnow().isoformat()
            }

        except PlaywrightTimeout as e:
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
            await browser.close()
