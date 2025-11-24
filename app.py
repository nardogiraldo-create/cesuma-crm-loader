# app.py (dentro de la función automatizar_crm)

# ... (Las configuraciones de CRM_URL, CRM_USER, etc., se mantienen) ...

def automatizar_crm(data):
    """Automatiza la carga de un prospecto en el CRM."""
    
    # 1. Configuración de opciones Headless para Render
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 2. Configuración específica para Render usando CHROME_BIN
    # Esto es crucial para que el navegador funcione en el entorno Linux de Render
    # y para evitar el error 'chromedriver executable needs to be in PATH'
    if 'CHROME_BIN' in os.environ:
        chrome_options.binary_location = os.environ['CHROME_BIN']
        
    # Inicializar el driver (ahora usa las opciones binarias)
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 20)
    
    try:
        # ... (El resto de tu lógica de login y automatización sigue aquí) ...
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
