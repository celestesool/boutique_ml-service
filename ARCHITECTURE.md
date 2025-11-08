# 🏗️ ARQUITECTURA DEL SISTEMA

## 📊 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (React)                        │
│                http://localhost:3000                     │
│  - Interfaz de usuario                                   │
│  - Upload de imágenes                                    │
│  - Visualización de productos                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ GraphQL / HTTP
                     │
┌────────────────────▼────────────────────────────────────┐
│            BACKEND NESTJS (ERP Core)                     │
│              http://localhost:3001                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  GraphQL API (Apollo Server)                     │   │
│  │  - Productos                                      │   │
│  │  - Categorías                                     │   │
│  │  - Órdenes                                        │   │
│  │  - Usuarios                                       │   │
│  │  - Reportes                                       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  PostgreSQL Database                             │   │
│  │  - products                                       │   │
│  │  - categories                                     │   │
│  │  - orders                                         │   │
│  │  - users                                          │   │
│  │  - product_ml_labels (nuevo)                     │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ HTTP REST API
                     │ Header: X-API-Key
                     │
┌────────────────────▼────────────────────────────────────┐
│         MICROSERVICIO ML (FastAPI)                       │
│           http://localhost:8000                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  FastAPI REST Endpoints                          │   │
│  │  ├─ POST /api/ml/classify-image                 │   │
│  │  ├─ POST /api/ml/similar-products               │   │
│  │  ├─ POST /api/ml/search-by-image                │   │
│  │  ├─ POST /api/ml/train                          │   │
│  │  └─ GET  /health                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  ML Models                                        │   │
│  │  ├─ CNN Classifier (EfficientNetB0)             │   │
│  │  ├─ Embedding Extractor (512 dims)              │   │
│  │  └─ FAISS Vector Index                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  MongoDB Database                                 │   │
│  │  ├─ images (metadatos)                          │   │
│  │  ├─ classifications (resultados ML)             │   │
│  │  ├─ embeddings (vectores 512D)                  │   │
│  │  └─ training_jobs (historial)                   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 🔄 Flujo de Datos: Clasificar Producto

```
1. Usuario sube imagen en Frontend
        │
        ▼
2. Frontend → NestJS GraphQL
   mutation clasificarProducto {
     productId: "uuid"
     imageBase64: "..."
   }
        │
        ▼
3. NestJS → ML Service
   POST /api/ml/classify-image
   Headers: { X-API-Key: "..." }
        │
        ▼
4. ML Service:
   ├─ Decodifica base64 → PIL Image
   ├─ Resize 224x224
   ├─ Normaliza [0,1]
   ├─ Ejecuta CNN → Predicciones
   ├─ Extrae embedding (512 dims)
   ├─ Guarda en MongoDB
   └─ Indexa en FAISS
        │
        ▼
5. ML Service → NestJS
   {
     success: true,
     predictions: {
       tipo_prenda: { label: "camisa", confidence: 0.94 },
       color: { label: "azul", confidence: 0.88 }
     }
   }
        │
        ▼
6. NestJS guarda etiquetas en PostgreSQL
   INSERT INTO product_ml_labels
        │
        ▼
7. NestJS → Frontend
   Devuelve etiquetas al usuario
```

## 🔍 Flujo de Datos: Búsqueda por Similitud

```
1. Usuario ve producto en tienda
        │
        ▼
2. Frontend solicita similares
   query {
     productosSimilares(productId: "uuid")
   }
        │
        ▼
3. NestJS → ML Service
   POST /api/ml/similar-products
   { product_id: "uuid", limit: 10 }
        │
        ▼
4. ML Service:
   ├─ Obtiene embedding del producto (MongoDB)
   ├─ Busca en índice FAISS (cosine similarity)
   ├─ Retorna top 10 productos similares
   │
        ▼
5. ML Service → NestJS
   {
     similar_products: [
       { product_id: "...", score: 0.92 },
       { product_id: "...", score: 0.87 }
     ]
   }
        │
        ▼
6. NestJS consulta detalles en PostgreSQL
   SELECT * FROM products WHERE id IN (...)
        │
        ▼
7. NestJS → Frontend
   Devuelve productos completos con imágenes
```

## 📦 Stack Tecnológico por Capa

### Frontend
- React 18
- Apollo Client (GraphQL)
- TailwindCSS / Material-UI

### Backend NestJS
- NestJS 10
- Apollo Server (GraphQL)
- TypeORM / Prisma
- PostgreSQL 15
- JWT Authentication

### Microservicio ML
- **Framework**: FastAPI 0.109
- **Runtime**: Python 3.11
- **ML Libs**: TensorFlow 2.15, scikit-learn
- **Vector Search**: FAISS
- **Database**: MongoDB 7.0
- **Server**: Uvicorn (ASGI)
- **Image Processing**: Pillow, OpenCV

## 🔐 Autenticación y Seguridad

```
Frontend → NestJS:
  Authorization: Bearer <JWT_TOKEN>

NestJS → ML Service:
  X-API-Key: ml_secret_key_boutique_2025

ML Service → MongoDB:
  mongodb://localhost:27017 (interno, sin auth en dev)
```

## 🚀 Deployment Architecture (Producción)

```
┌─────────────────────────────────────────────┐
│         GOOGLE CLOUD PLATFORM                │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │  Cloud Run                          │    │
│  │  - ml-service container             │    │
│  │  - Auto-scaling                     │    │
│  │  - HTTPS automático                 │    │
│  └────────────────────────────────────┘    │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │  Secret Manager                     │    │
│  │  - ML_API_KEY                       │    │
│  │  - MONGODB_URL                      │    │
│  └────────────────────────────────────┘    │
│                                              │
│  ┌────────────────────────────────────┐    │
│  │  Cloud Storage                      │    │
│  │  - Modelos ML (.h5, .pkl)          │    │
│  │  - Datasets                         │    │
│  └────────────────────────────────────┘    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         MONGODB ATLAS                        │
│  - Cluster M0 (Free tier)                   │
│  - 512MB Storage                            │
│  - Global deployment                        │
└─────────────────────────────────────────────┘
```

## 📊 Data Models

### PostgreSQL (NestJS)

```sql
-- Tabla de productos (existente)
products:
  - id: UUID
  - nombre: VARCHAR
  - precio: DECIMAL
  - imagen_url: VARCHAR
  - categoria_id: UUID

-- Nueva tabla para etiquetas ML
product_ml_labels:
  - id: UUID
  - product_id: UUID (FK → products)
  - tipo_prenda: VARCHAR
  - color_principal: VARCHAR
  - estilo: VARCHAR
  - confidence_avg: DECIMAL
  - approved: BOOLEAN
  - created_at: TIMESTAMP
```

### MongoDB (ML Service)

```javascript
// Colección: images
{
  _id: ObjectId,
  product_id: "uuid-nestjs",
  image_url: "https://...",
  image_hash: "sha256",
  status: "processed",
  uploaded_at: ISODate
}

// Colección: classifications
{
  _id: ObjectId,
  product_id: "uuid",
  predictions: {
    tipo_prenda: { label: "camisa", confidence: 0.94 },
    color: { label: "azul", confidence: 0.88 }
  },
  model_version: "v1.0.0",
  classified_at: ISODate,
  approved: false
}

// Colección: embeddings
{
  _id: ObjectId,
  product_id: "uuid",
  embedding_vector: [0.12, 0.45, ..., 0.89], // 512 dims
  faiss_index_position: 1234,
  created_at: ISODate
}

// Colección: training_jobs
{
  _id: ObjectId,
  job_id: "job-abc-123",
  status: "completed",
  metrics: { accuracy: 0.94, loss: 0.12 },
  started_at: ISODate,
  completed_at: ISODate
}
```

## 🎯 Capacidades del Sistema

### Clasificación
- ✅ Tipo de prenda (camisa, pantalón, vestido, etc.)
- ✅ Tipo de cuello (redondo, v, tortuga, etc.)
- ✅ Tipo de manga (corta, larga, sin manga)
- ✅ Patrón (liso, rayas, cuadros, floral)
- ✅ Color principal (8+ colores)
- ✅ Estilo (casual, formal, deportivo, etc.)

### Búsqueda
- ✅ Productos similares por ID
- ✅ Búsqueda visual (upload de imagen)
- ✅ Filtros (categoría, precio, etc.)
- ✅ Ranking por similitud

### Performance
- ⚡ Clasificación: ~200-300ms por imagen
- ⚡ Búsqueda similares: ~100-150ms
- ⚡ Throughput: 100+ req/min
- ⚡ Embeddings: 512 dimensiones

---

**Última actualización**: Noviembre 8, 2025
