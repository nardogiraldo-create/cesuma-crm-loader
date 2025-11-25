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

5. Commit

---

## 🎯 Después de subir el archivo:

### Si subiste `render-build.sh`:
1. Ve a Render Dashboard
2. **Manual Deploy** → **"Clear build cache & deploy"**
3. Espera 5 minutos
4. Revisa los logs

### Si subiste `Dockerfile`:
1. Render lo detectará automáticamente
2. En Settings, borra el Build Command (déjalo vacío)
3. Borra el Start Command también
4. Guarda cambios
5. **Manual Deploy** → **"Clear build cache & deploy"**

---

## ✅ Checklist de tu repositorio en GitHub:

Después de subir los archivos, tu repo debe tener:
```
tu-repositorio/
├── app.py                      ✅
├── requirements.txt            ✅
├── render-build.sh            ✅ NUEVO (Opción 1)
└── Dockerfile                 ✅ NUEVO (Opción 2 - mejor)
