# 🚀 CRM Loader - Guía de Deployment y Correcciones

## 📋 Resumen de Mejoras Implementadas

### ✅ Correcciones Críticas
1. **Ruta de Chrome corregida**: Ahora busca `/usr/bin/chromium` en lugar de `/usr/bin/google-chrome`
2. **Context manager para driver**: Garantiza cierre del navegador en todos los escenarios
3. **Validación de datos**: Verifica emails, teléfonos y campos obligatorios
4. **Fecha de nacimiento configurable**: Ya no está hardcodeada
5. **Logging estructurado**: Sistema de logs con niveles y timestamps

### ⚡ Optimizaciones
6. **Reintentos con backoff exponencial**: 3 intentos automáticos con espera incremental
7. **WebDriverWait dinámico**: Reemplaza `time.sleep()` fijos por esperas inteligentes
8. **Validación de variables de entorno**: Falla rápido si falta configuración
9. **Manejo de errores específico**: Distingue entre errores recuperables y permanentes
10. **Rate limiting básico**: 2 segundos de delay entre requests en Google Sheets

---

## 🛠️ Pasos para Actualizar en Render

### 1. Actualizar Archivos

Reemplaza estos archivos en tu repositorio:

```bash
# Archivos a actualizar
app.py                    # ← Versión mejorada
render-build.sh           # ← Corregido
# script.gs va en Google Sheets, no en Render
```

### 2. Variables de Entorno en Render

Verifica que estén configuradas:

```bash
CRM_URL=https://cesuma.academic.lat/...
CRM_USER=tu_usuario
CRM_PASS=tu_contraseña
CHROME_BIN=/usr/bin/chromium              # ← NUEVA
CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

### 3. Configuración del Servicio en Render

#### Build Command:
```bash
bash render-build.sh
```

#### Start Command:
```bash
gunicorn app:app --workers 2 --timeout 120 --bind 0.0.0.0:10000
```

**IMPORTANTE**: Aumenta el timeout a 120 segundos porque el proceso puede tardar.

### 4. Health Check en Render

Configura el health check:
- **Path**: `/health`
- **Interval**: 60 segundos
- **Initial delay**: 30 segundos

---

## 📊 Google Apps Script

### Instalación en Google Sheets

1. Abre tu Google Sheet
2. Ve a **Extensiones → Apps Script**
3. Borra todo el código existente
4. Pega el nuevo código de `script.gs`
5. Guarda con `Ctrl+S`
6. Recarga la hoja de cálculo
7. Verás un nuevo menú **🚀 CRM Loader**

### Estructura de la Hoja

Tu hoja debe tener estos encabezados (pueden estar en cualquier orden):

| Nombre | Apellido_Paterno | Email | Telefono_Celular | CURP_ID | Oferta_Educativa | Estado de Carga |
|--------|------------------|-------|------------------|---------|------------------|-----------------|
| Juan   | Pérez           | juan@example.com | 3001234567 | ABC123 | Licenciatura | Pendiente |

**Nota**: El script normaliza los nombres (quita tildes, espacios extras, etc.)

### Uso del Menú

- **📤 Enviar Prospectos**: Procesa todas las filas con estado "Pendiente"
- **🔄 Resetear Estados**: Pone todas las filas en "Pendiente" nuevamente

---

## 🔍 Monitoreo y Debug

### Logs en Render

Para ver logs en tiempo real:

```bash
# En el dashboard de Render, ve a "Logs"
# O desde CLI:
render logs -s tu-servicio-id --tail
```

### Logs en Google Sheets

```javascript
// En Apps Script, ve a:
// Extensiones → Apps Script → Ejecuciones
// Ahí verás el historial completo
```

### Endpoint de Salud

Prueba que el servicio esté funcionando:

```bash
curl https://tu-app.onrender.com/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "chrome_available": true
}
```

---

## 🐛 Troubleshooting

### Error: "Chromium not found"

**Solución**:
```bash
# En render-build.sh, agrega:
apt-get install -y chromium-browser
```

### Error: "Timeout al cargar CRM"

**Causa**: El servidor del CRM está lento o Render tiene latencia alta.

**Solución**: Aumenta los timeouts:
```python
# En app.py
driver.set_page_load_timeout(120)  # En vez de 90
wait = WebDriverWait(driver, 45)   # En vez de 30
```

### Error: "No se encontró la oferta educativa"

**Causa**: El texto de la oferta no coincide exactamente con el select.

**Solución**: 
1. Entra manualmente al CRM
2. Inspecciona el select de "Oferta Educativa"
3. Copia el texto EXACTO de la opción
4. Úsalo en la hoja de cálculo

### Error: "HTTP 429 - Too Many Requests"

**Causa**: Estás enviando demasiados requests muy rápido.

**Solución**: Aumenta el delay en script.gs:
```javascript
const DELAY_ENTRE_REQUESTS = 5000; // 5 segundos
```

### Error: "Memory limit exceeded"

**Causa**: Render Free Tier tiene 512MB de RAM.

**Solución**:
1. Reduce workers de Gunicorn a 1
2. Procesa en lotes pequeños (10-20 prospectos a la vez)
3. Considera upgrade a plan pagado

---

## 📈 Mejoras Futuras Recomendadas

### Prioridad Alta
- [ ] Sistema de cola con Redis (para procesar grandes volúmenes)
- [ ] Webhook para notificar cuando termina el proceso
- [ ] Dashboard simple para ver estadísticas

### Prioridad Media
- [ ] Tests automatizados
- [ ] Integración con Sentry para error tracking
- [ ] Logs a servicio externo (LogDNA, Papertrail)

### Prioridad Baja
- [ ] Interfaz web para cargar CSVs directamente
- [ ] API para consultar estado de prospectos
- [ ] Exportar reportes de carga

---

## 🔐 Seguridad

### Recomendaciones

1. **Nunca commitees credenciales**: Usa siempre variables de entorno
2. **Rota contraseñas regularmente**: Cambia `CRM_PASS` cada 3 meses
3. **Limita acceso a Google Sheet**: Solo usuarios autorizados
4. **Revisa logs periódicamente**: Busca intentos de acceso no autorizado

### Backup

Haz backup semanal de la hoja de cálculo:
```
Archivo → Descargar → Microsoft Excel (.xlsx)
```

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa los logs en Render
2. Revisa las ejecuciones en Apps Script
3. Verifica que las variables de entorno estén correctas
4. Prueba el endpoint `/health`

---

## 📝 Changelog

### v2.0 (Actual)
- ✅ Corrección de ruta de Chrome
- ✅ Context manager para driver
- ✅ Validación de datos
- ✅ Sistema de reintentos
- ✅ Logging mejorado
- ✅ WebDriverWait dinámico

### v1.0 (Original)
- Versión inicial con problemas conocidos
