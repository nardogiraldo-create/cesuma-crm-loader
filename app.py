# app.py - Script de Automatización CRM (Selenium Headless)
# ... (imports y configuraciones se mantienen) ...

SELECTORS = {
    # Login
    "USER_INPUT": "input[type='email']", 
    "PASS_INPUT": "input[type='password']",
    "LOGIN_BTN": "button[type='submit']", 
    
    # Flujo Familiar (Paso 1) - Revisado el botón Continuar
    "FAMILIA_DROPDOWN": "select[id*='ddlFamilia']", 
    "CONTINUAR_BTN": "button:contains('Continuar')", # <--- AJUSTADO
    
    # Formulario Prospecto (Paso 2)
    "NOMBRE": "input[id*='txtNombre']", 
    "APELLIDO_PATERNO": "input[id*='txtApellidoPaterno']",
    "SEXO": "select[id*='ddlSexo']",
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
    "GUARDAR_BTN": "button:contains('Guardar')" # <--- AJUSTADO
}

# --- FUNCIÓN PRINCIPAL DE AUTOMATIZACIÓN ---
def automatizar_crm(data):
    # ... (Se mantiene la configuración de Chrome Options) ...
    # driver = webdriver.Chrome(options=chrome_options) 
    # ... (Se mantiene la función de login) ...
    
    try:
        # ... (Pasos 1 y 2 de Login y Navegación) ...

        # 3. PASO 1: INFORMACIÓN FAMILIAR (Familia: No registrar, Clic en Continuar)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["FAMILIA_DROPDOWN"])))
        
        # Seleccionar "No registrar" 
        Select(driver.find_element(By.CSS_SELECTOR, SELECTORS["FAMILIA_DROPDOWN"])).select_by_visible_text("No registrar")
        
        # Usar XPath o CSS Selector para el botón de Continuar
        # Intentamos con XPath, que es más seguro para buscar texto en botones
        driver.find_element(By.XPATH, "//button[contains(., 'Continuar')]").click()
        time.sleep(1.5)

        # 4. PASO 2: INFORMACIÓN DEL PROSPECTO 
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS["NOMBRE"])))
        
        # ... (Llenado de datos se mantiene) ...
        # ...

        # 5. PASO 3: DATOS DE PROGRAMA
        
        # ... (Selecciones de Oferta, Periodo, Horario, etc. se mantienen) ...
        
        # 6. GUARDAR
        # Usar XPath para el botón de Guardar
        driver.find_element(By.XPATH, "//button[contains(., 'Guardar')]").click()
        
        # Esperar confirmación
        wait.until(EC.url_changes(driver.current_url)) 
        
        return {"status": "success", "message": "Prospecto cargado exitosamente."}
        
    # ... (Manejo de excepciones se mantiene) ...
    finally:
        driver.quit()
# ... (Rutas de Flask se mantienen) ...
