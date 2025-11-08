# 🚀 Guía de Deployment - ML Service

Esta guía cubre el deployment del microservicio ML tanto en **desarrollo local** como en **Google Cloud Platform (GCP)**.

---

## 📋 Tabla de Contenidos

1. [Desarrollo Local con Docker](#desarrollo-local-con-docker)
2. [Deployment a Google Cloud Run](#deployment-a-google-cloud-run)
3. [Variables de Entorno](#variables-de-entorno)
4. [Monitoreo y Logs](#monitoreo-y-logs)
5. [Troubleshooting](#troubleshooting)

---

## 🐳 Desarrollo Local con Docker

### Prerrequisitos

- Docker Desktop instalado y corriendo
- Docker Compose v2+

### Opción 1: Docker Compose (Recomendado)

**Iniciar todos los servicios:**

```bash
# Desde la carpeta ml-service
docker-compose up -d
```

Esto levantará:
- **MongoDB** en puerto `27017`
- **ML Service API** en puerto `8000`

**Ver logs:**

```bash
docker-compose logs -f ml-service
```

**Detener servicios:**

```bash
docker-compose down
```

**Reconstruir después de cambios:**

```bash
docker-compose up -d --build
```

### Opción 2: Docker Manual

**Build de la imagen:**

```bash
docker build -t ml-service:latest .
```

**Run del contenedor:**

```bash
docker run -d \
  --name ml-service \
  -p 8000:8000 \
  -e MONGODB_URL=mongodb://host.docker.internal:27017 \
  -e API_KEY=ml_secret_key_boutique_2025 \
  ml-service:latest
```

### Verificar que funciona

```bash
# Health check
curl http://localhost:8000/health

# Ver documentación
# Abrir en navegador: http://localhost:8000/docs
```

---

## ☁️ Deployment a Google Cloud Run

### Prerrequisitos

1. **Cuenta de Google Cloud** con facturación habilitada
2. **Google Cloud SDK** instalado
3. **Proyecto de GCP** creado

### Paso 1: Configurar Google Cloud

```bash
# Login
gcloud auth login

# Configurar proyecto (reemplaza YOUR_PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID

# Habilitar APIs necesarias
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com
```

### Paso 2: Configurar MongoDB (Atlas o Compute Engine)

#### Opción A: MongoDB Atlas (Recomendado para producción)

1. Ir a https://www.mongodb.com/cloud/atlas
2. Crear cluster gratuito (M0)
3. Configurar usuario y contraseña
4. Whitelist IPs: `0.0.0.0/0` (para Cloud Run)
5. Obtener Connection String: `mongodb+srv://user:pass@cluster.mongodb.net/ml_boutique_db`

#### Opción B: MongoDB en Compute Engine

```bash
# Crear VM con MongoDB
gcloud compute instances create mongodb-vm \
  --zone=us-central1-a \
  --machine-type=e2-medium \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB

# SSH y instalar MongoDB (seguir guía oficial)
```

### Paso 3: Deploy Manual a Cloud Run

```bash
# Build y push de imagen
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/ml-service

# Deploy a Cloud Run
gcloud run deploy ml-service \
  --image gcr.io/YOUR_PROJECT_ID/ml-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10 \
  --min-instances 1 \
  --timeout 300s \
  --set-env-vars MONGODB_URL="mongodb+srv://user:pass@cluster.mongodb.net/ml_boutique_db" \
  --set-env-vars API_KEY="ml_secret_key_boutique_2025" \
  --set-env-vars CORS_ORIGINS="https://your-frontend.com,https://your-erp.com"
```

### Paso 4: Deploy Automático con Cloud Build

**Conectar repositorio GitHub:**

1. Ir a Cloud Build > Triggers
2. Conectar repositorio
3. Crear trigger:
   - **Evento**: Push to branch
   - **Branch**: `^main$`
   - **Configuration**: Cloud Build (cloudbuild.yaml)

**Variables de entorno secretas:**

```bash
# Crear secrets
echo -n "mongodb+srv://user:pass@cluster.mongodb.net/ml_boutique_db" | \
  gcloud secrets create MONGODB_URL --data-file=-

echo -n "ml_secret_key_boutique_2025" | \
  gcloud secrets create API_KEY --data-file=-

# Dar acceso a Cloud Build
gcloud secrets add-iam-policy-binding MONGODB_URL \
  --member="serviceAccount:YOUR_PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

**Push a GitHub → Deploy automático:**

```bash
git add .
git commit -m "Deploy to production"
git push origin main
```

### Paso 5: Obtener URL del servicio

```bash
gcloud run services describe ml-service \
  --platform managed \
  --region us-central1 \
  --format 'value(status.url)'
```

**Ejemplo de URL:** `https://ml-service-abc123-uc.a.run.app`

---

## 🔐 Variables de Entorno

### Desarrollo Local (.env)

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=ml_boutique_db
API_KEY=ml_secret_key_boutique_2025
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
LOG_LEVEL=DEBUG
```

### Producción (Cloud Run)

Se configuran al hacer deploy:

```bash
--set-env-vars MONGODB_URL="..." \
--set-env-vars API_KEY="..." \
--set-env-vars CORS_ORIGINS="https://production-url.com"
```

**Variables requeridas:**

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `MONGODB_URL` | Connection string de MongoDB | `mongodb+srv://...` |
| `MONGODB_DB_NAME` | Nombre de la base de datos | `ml_boutique_db` |
| `API_KEY` | API Key para autenticación | `your-secret-key` |
| `CORS_ORIGINS` | Orígenes permitidos (separados por coma) | `https://app.com,https://erp.com` |
| `LOG_LEVEL` | Nivel de logs | `INFO` o `DEBUG` |

---

## 📊 Monitoreo y Logs

### Cloud Run Logs

```bash
# Ver logs en tiempo real
gcloud run services logs tail ml-service \
  --region us-central1

# Ver logs de las últimas 24 horas
gcloud run services logs read ml-service \
  --region us-central1 \
  --limit 100
```

### Cloud Monitoring

1. Ir a **Cloud Console > Monitoring > Dashboards**
2. Métricas importantes:
   - Request Count
   - Request Latency (p50, p95, p99)
   - Error Rate
   - Memory Utilization
   - CPU Utilization
   - Container Instance Count

### Configurar Alertas

```bash
# Crear alerta de error rate alto
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="ML Service High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

---

## 🔧 Troubleshooting

### Problema: Container no inicia

**Síntomas:** Service unavailable, container crashes

**Soluciones:**

1. Verificar logs:
   ```bash
   gcloud run services logs read ml-service --limit 50
   ```

2. Verificar variables de entorno:
   ```bash
   gcloud run services describe ml-service
   ```

3. Aumentar memoria/CPU si es necesario

### Problema: No conecta a MongoDB

**Síntomas:** `MongoNetworkError`, `Connection timeout`

**Soluciones:**

1. Verificar que MongoDB Atlas permite conexión desde `0.0.0.0/0`
2. Verificar connection string (URL encode password si tiene caracteres especiales)
3. Test de conexión:
   ```bash
   # Desde Cloud Shell
   mongosh "mongodb+srv://user:pass@cluster.mongodb.net/ml_boutique_db"
   ```

### Problema: CORS errors

**Síntomas:** Browser bloquea requests

**Soluciones:**

1. Verificar CORS_ORIGINS incluye tu dominio frontend
2. Actualizar variable:
   ```bash
   gcloud run services update ml-service \
     --set-env-vars CORS_ORIGINS="https://new-domain.com,https://old-domain.com"
   ```

### Problema: Cold starts lentos

**Síntomas:** Primera request tarda >10 segundos

**Soluciones:**

1. Configurar `--min-instances=1` (costo adicional pero sin cold start)
2. Optimizar Dockerfile (multi-stage build)
3. Reducir tamaño de imagen

### Problema: Out of Memory

**Síntomas:** Container killed, Error 137

**Soluciones:**

1. Aumentar memoria:
   ```bash
   gcloud run services update ml-service --memory 4Gi
   ```

2. Optimizar carga de modelos (lazy loading)

---

## 📦 Costos Estimados (GCP)

### Cloud Run

- **Tier gratuito:** 2M requests/mes
- **Después:** $0.40 por millón de requests
- **Compute:** $0.00002400 por vCPU-second
- **Memory:** $0.00000250 per GiB-second

**Ejemplo mensual (tráfico moderado):**
- 5M requests
- 100ms promedio por request
- 2 vCPU, 2GB RAM
- **~$15-30/mes**

### MongoDB Atlas

- **M0 (Free):** 512MB storage, shared cluster
- **M10 (Producción):** ~$57/mes, 10GB storage, replicación
- **M30 (Alta demanda):** ~$240/mes, 40GB storage

---

## 🎯 Próximos Pasos

1. ✅ Deploy local con Docker Compose
2. ✅ Deploy manual a Cloud Run
3. ⏭️ Configurar CI/CD con GitHub Actions
4. ⏭️ Implementar autenticación JWT
5. ⏭️ Configurar CDN para assets estáticos
6. ⏭️ Implementar rate limiting
7. ⏭️ Setup de staging environment

---

## 📚 Recursos Adicionales

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

**¿Problemas?** Revisa logs con `docker-compose logs -f` o `gcloud run logs read ml-service`
