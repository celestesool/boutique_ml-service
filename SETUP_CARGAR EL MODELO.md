
##  Pasos de Instalación

### 1️ Clonar el repositorio
```bash
git clone https://github.com/celestesool/boutique_ml-service.git
cd boutique_ml-service
```

### 2️ Descargar el modelo entrenado (OBLIGATORIO)

 **Descargar desde Google Drive**: [https://drive.google.com/file/d/1x4bJrZBlmhk_2HjVhZrpjkorup6mE8-U/view?usp=drive_link]

 **Colocar en**: `ml-service/models/fashion_classifier.h5`

```
boutique_ml-service/
└── ml-service/
    └── models/
        └── fashion_classifier.h5  ← Aquí va el archivo
```
No necesitas hacer nada, ya tiene:
```
MONGODB_URL=mongodb://admin:admin123@localhost:27017
MONGODB_DB_NAME=ml_boutique_db
API_KEY=ml_secret_key_boutique_2025
```

### 4️ Crear entorno virtual e instalar dependencias
```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activar (Windows CMD)
.\venv\Scripts\activate.bat

# Instalar todos los paquetes
pip install -r requirements.txt
```

⏱️ **Tiempo estimado**: 5-10 minutos

### 5️ Iniciar MongoDB con Docker
```bash
docker run -d \
  --name ml_mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin123 \
  mongo:7.0
```

**Verificar que MongoDB está corriendo**:
```bash
docker ps
```

Deberías ver el contenedor `ml_mongodb` en la lista.

### 6️ Iniciar el servicio ML
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verás algo como:
```
INFO:     Started server process
✅ Connected to MongoDB database: ml_boutique_db
✅ ML Service started successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7️ Verificar que todo funciona
Abre en el navegador: **http://localhost:8000/docs**

####  Test rápido:
1. **Health Check**:
   - Ve a `GET /health` → Execute
   - Deberías ver: `{"status": "healthy", "mongodb": "connected"}`

2. **Clasificar imagen**:
   - Ve a `POST /api/ml/classify-image`
   - Click "Try it out"
   - Pega una imagen en base64
   - Execute
   - ¡Verás las predicciones con 85% accuracy! 

---

## 📦 Estructura de archivos final

```
boutique_ml-service/
├── ml-service/
│   ├── app/                      ← Código fuente (del repo)
│   ├── models/
│   │   └── fashion_classifier.h5 ← DESCARGAR de Drive (500 MB)
│   ├── data/                     ← OPCIONAL (solo para reentrenar)
│   ├── venv/                     ← Crear con python -m venv venv
│   ├── .env                      ← Copiar de .env.example
│   ├── .env.example              ← Del repo (plantilla)
│   ├── requirements.txt          ← Del repo
│   └── docker-compose.yml        ← Del repo
```

---

## ❓ Problemas Comunes

### 🔴 "Model file not found"
```
❌ Error: Could not load model from models/fashion_classifier.h5
```
**Solución**: Descarga `fashion_classifier.h5` desde Google Drive y colócalo en `ml-service/models/`

---

### 🔴 "MongoDB connection failed"
```
❌ Error: Could not connect to MongoDB
```
**Solución**:
1. Verifica que Docker esté corriendo: `docker ps`
2. Si no ves `ml_mongodb`, inicia el contenedor:
   ```bash
   docker start ml_mongodb
   ```
3. Si no existe, créalo con el comando del paso 5️

---

### 🔴 "Module not found: tensorflow"
```
❌ ModuleNotFoundError: No module named 'tensorflow'
```
**Solución**:
1. Verifica que el entorno virtual esté activado:
   ```bash
   .\venv\Scripts\Activate.ps1
   ```
   Deberías ver `(venv)` al inicio de la línea de comandos
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

---

### 🔴 "Port 8000 already in use"
```
❌ ERROR: [Errno 10048] Address already in use
```
**Solución**:
1. Detener el proceso en el puerto 8000:
   ```powershell
   # Windows PowerShell
   Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
   ```
2. O usar otro puerto:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8001
   ```

---

### 🔴 ".env file not found"
```
❌ Warning: .env file not found
```
**Solución**:
```bash
copy .env.example .env
```

---

##  Información del Modelo

- **Arquitectura**: EfficientNetB0 (Transfer Learning de ImageNet)
- **Accuracy**: 85.41% training, 83.73% validation
- **Dataset**: Fashion-MNIST (70,000 imágenes)
- **Clases**: 10 categorías de ropa
- **Tiempo de entrenamiento**: ~2 horas (10 épocas)
- **Tamaño del modelo**: ~500 MB

---

##  Endpoints Principales

### **Clasificación (Deep Learning)**
- `POST /api/ml/classify-image` - Clasificar imagen de producto
- `POST /api/ml/classify/batch` - Clasificar múltiples imágenes

### **Similitud (Unsupervised Learning)**
- `POST /api/ml/similar/image` - Productos similares por imagen
- `GET /api/ml/similar/product/{id}` - Productos similares por ID

### **Recomendaciones (Collaborative Filtering)**
- `GET /api/ml/recommendations/user/{id}` - Recomendaciones personalizadas
- `POST /api/ml/recommendations/interaction` - Registrar interacción

### **Métricas y Supervisión**
- `GET /api/ml/metrics/overall` - Métricas generales del modelo
- `GET /api/ml/metrics/report` - Reporte completo
- `GET /api/ml/metrics/training-history` - Historial de entrenamiento

### **Embeddings**
- `POST /api/ml/embeddings/extract` - Extraer vector de características (1280-dim)

---

## Características Implementadas

✅ **3 Tipos de ML**:
1. Deep Learning - CNN EfficientNetB0 (clasificación)
2. Supervised Learning - Sistema de validación humana
3. Unsupervised Learning - FAISS similarity + recomendaciones

✅ **Sistema de Métricas/KPIs**:
- Accuracy, Precision, Recall, F1-Score
- Confusion Matrix
- Per-class metrics
- Inference statistics

✅ **Producción Ready**:
- Docker & Docker Compose
- MongoDB con índices optimizados
- API key authentication
- CORS configurado
- Logging estructurado
- Health checks

---

## 🔗 Links Importantes

- **Repositorio**: https://github.com/celestesool/boutique_ml-service

---

##  Ayuda

Si tienes problemas, verifica:
1. ✅ Python 3.11 instalado
2. ✅ Docker Desktop corriendo
3. ✅ Modelo descargado en `models/fashion_classifier.h5`
4. ✅ `.env` existe (copiado de `.env.example`)
5. ✅ Virtual environment activado `(venv)`
6. ✅ Dependencias instaladas `pip install -r requirements.txt`
7. ✅ MongoDB corriendo `docker ps`

---

¡Listo para usar! 
