FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver

RUN which chromium && chromium --version && \
    which chromedriver && chromedriver --version

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "app:app", "--workers", "1", "--timeout", "120", "--bind", "0.0.0.0:10000"]
```

5. Click en **"Commit new file"** (botón verde)

---

## **PASO 2: Configurar Render**

1. Ve a tu servicio en Render Dashboard
2. Click en **"Settings"** (menú lateral)
3. En la sección **"Build & Deploy"**:
   - **Build Command**: BORRA TODO (deja el campo VACÍO)
   - **Start Command**: BORRA TODO (deja el campo VACÍO)
4. Scroll hasta el final y click en **"Save Changes"** (botón rojo)

---

## **PASO 3: Deploy**

1. Ve a la pestaña **"Manual Deploy"** (arriba)
2. Click en **"Clear build cache & deploy"**
3. **Espera 5-10 minutos** (el primer build con Docker tarda más)

---

## **PASO 4: Verificar que funcione**

Deberías ver en los logs:
```
==> Building with Dockerfile
Step 1/10 : FROM python:3.11-slim
Step 2/10 : ENV PYTHONUNBUFFERED=1
...
✅ Chromium version 1xx.x.xxxx.xx
✅ ChromeDriver 1xx.x.xxxx.xx
...
==> Build successful
==> Deploying...
```

---

## ⏱️ Mientras esperas el deploy:

Compárteme una captura o texto de los logs cuando empiece el build. Deberían decir algo como:
```
==> Building with Dockerfile
