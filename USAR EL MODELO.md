#  Setup para Compañeros

## 1️ Clonar el repositorio
```bash
git clone [URL_DE_TU_REPO]
cd ml-service
```

## 2️ Descargar archivos pesados desde Google Drive

### **OBLIGATORIO: Modelo entrenado**
📥 **Descargar**: [LINK_GOOGLE_DRIVE_MODELO]
📂 **Colocar en**: `ml-service/models/fashion_classifier.h5`

### **OPCIONAL: Dataset (solo si quieres reentrenar)**
📥 **Descargar**: [LINK_GOOGLE_DRIVE_DATA]
📂 **Extraer en**: `ml-service/data/`

Estructura esperada:
```
ml-service/
├── models/
│   └── fashion_classifier.h5  ← DESCARGAR AQUÍ
├── data/
│   ├── train/          ← OPCIONAL (si quieres reentrenar)
│   ├── validation/     ← OPCIONAL
│   └── test/           ← OPCIONAL
```

## 3️ Instalar dependencias
```bash
# Crear entorno virtual
python -m venv venv

# Activar (Windows)
.\venv\Scripts\Activate.ps1

# Instalar paquetes
pip install -r requirements.txt
```

## 4️ Iniciar MongoDB (Docker)
```bash
docker run -d \
  --name ml_mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=admin123 \
  mongo:7.0
```

## 5️ Iniciar el servicio
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 6️ Probar que funciona
Abre en el navegador: **http://localhost:8000/docs**

### Test rápido:
1. Ve a **GET /health** → Execute → Deberías ver `"status": "healthy"`
2. Ve a **POST /api/ml/classify-image** → Prueba clasificar una imagen

---

## ❓ Problemas comunes

### "Model file not found"
→ Descarga `fashion_classifier.h5` desde Drive y colócalo en `models/`

### "MongoDB connection failed"
→ Verifica que Docker esté corriendo: `docker ps`

### "Module not found"
→ Activa el venv: `.\venv\Scripts\Activate.ps1`
→ Instala dependencias: `pip install -r requirements.txt`

---

##  Características del modelo
- **Arquitectura**: EfficientNetB0 (Transfer Learning)
- **Accuracy**: 85.41% training, 83.73% validation
- **Dataset**: Fashion-MNIST (70,000 imágenes)
- **Clases**: 10 categorías de ropa

## Endpoints principales
- `POST /api/ml/classify-image` - Clasificar imágenes
- `POST /api/ml/similar/image` - Buscar productos similares
- `GET /api/ml/recommendations/user/{id}` - Recomendaciones
- `GET /api/ml/metrics/report` - Métricas del modelo

¡Listo! 
