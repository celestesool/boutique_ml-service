# 🔗 Guía de Integración - ERP (NestJS) ↔ ML Service

Esta guía explica cómo integrar el **Microservicio ML** con tu **ERP Core** (NestJS + GraphQL + PostgreSQL).

---

## 📋 Tabla de Contenidos

1. [Arquitectura de Integración](#arquitectura-de-integración)
2. [Setup en NestJS](#setup-en-nestjs)
3. [Consumir Endpoints ML](#consumir-endpoints-ml)
4. [Ejemplos de Uso](#ejemplos-de-uso)
5. [Manejo de Errores](#manejo-de-errores)
6. [Best Practices](#best-practices)

---

## 🏗️ Arquitectura de Integración

```
┌─────────────────┐
│   Frontend      │
│  (React/Vue)    │
└────────┬────────┘
         │ GraphQL
         ▼
┌─────────────────────────────┐
│      ERP Core (NestJS)      │
│  ┌───────────────────────┐  │
│  │  GraphQL Resolvers    │  │
│  └──────────┬────────────┘  │
│  ┌──────────▼────────────┐  │
│  │   ML Service Client   │◄─┼─── HttpModule (Axios)
│  └──────────┬────────────┘  │
│  ┌──────────▼────────────┐  │
│  │  Business Logic       │  │
│  └───────────────────────┘  │
│  PostgreSQL Database        │
└──────────────┬──────────────┘
               │ REST API
               ▼
┌─────────────────────────────┐
│    ML Service (FastAPI)     │
│  ┌───────────────────────┐  │
│  │  /api/ml/classify     │  │
│  │  /api/ml/embeddings   │  │
│  │  /api/ml/recommend    │  │
│  │  /api/ml/metrics      │  │
│  └───────────────────────┘  │
│  MongoDB Database           │
└─────────────────────────────┘
```

### Flujo de Datos

1. **Frontend** hace query GraphQL al ERP
2. **ERP Resolver** procesa la request
3. **ML Service Client** (en ERP) llama al microservicio ML vía REST
4. **ML Service** procesa (clasificación, embeddings, recomendaciones)
5. **ERP** recibe respuesta y la procesa/enriquece
6. **ERP** retorna datos vía GraphQL al Frontend

---

## 🛠️ Setup en NestJS

### 1. Instalar Dependencias

```bash
npm install @nestjs/axios axios
npm install --save-dev @types/node
```

### 2. Configurar Variables de Entorno

**`.env` (desarrollo):**

```env
# ML Service
ML_SERVICE_URL=http://localhost:8000
ML_SERVICE_API_KEY=ml_secret_key_boutique_2025
ML_SERVICE_TIMEOUT=30000
```

**`.env.production`:**

```env
ML_SERVICE_URL=https://ml-service-abc123-uc.a.run.app
ML_SERVICE_API_KEY=your_production_api_key
ML_SERVICE_TIMEOUT=60000
```

### 3. Crear ML Service Client

**`src/ml-service/ml-service.module.ts`:**

```typescript
import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { ConfigModule } from '@nestjs/config';
import { MlServiceClient } from './ml-service.client';

@Module({
  imports: [
    HttpModule.register({
      timeout: 30000,
      maxRedirects: 5,
    }),
    ConfigModule,
  ],
  providers: [MlServiceClient],
  exports: [MlServiceClient],
})
export class MlServiceModule {}
```

**`src/ml-service/ml-service.client.ts`:**

```typescript
import { Injectable, Logger, HttpException } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { firstValueFrom, timeout, catchError } from 'rxjs';
import { AxiosError } from 'axios';

@Injectable()
export class MlServiceClient {
  private readonly logger = new Logger(MlServiceClient.name);
  private readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly timeout: number;

  constructor(
    private readonly httpService: HttpService,
    private readonly configService: ConfigService,
  ) {
    this.baseUrl = this.configService.get<string>('ML_SERVICE_URL');
    this.apiKey = this.configService.get<string>('ML_SERVICE_API_KEY');
    this.timeout = this.configService.get<number>('ML_SERVICE_TIMEOUT', 30000);
  }

  /**
   * Headers comunes para todas las requests
   */
  private getHeaders() {
    return {
      'x-api-key': this.apiKey,
      'Content-Type': 'application/json',
    };
  }

  /**
   * Manejo centralizado de errores
   */
  private handleError(error: AxiosError) {
    this.logger.error(`ML Service Error: ${error.message}`, error.stack);
    
    if (error.response) {
      // Error de respuesta del servidor ML
      throw new HttpException(
        error.response.data || 'ML Service error',
        error.response.status,
      );
    } else if (error.request) {
      // No hubo respuesta (timeout, network error)
      throw new HttpException(
        'ML Service unavailable',
        503,
      );
    } else {
      // Error en configuración de request
      throw new HttpException(
        'Internal error calling ML Service',
        500,
      );
    }
  }

  /**
   * Clasificar imagen de producto
   */
  async classifyProduct(imageUrl: string): Promise<ClassificationResult> {
    try {
      this.logger.log(`Classifying product image: ${imageUrl}`);

      const response = await firstValueFrom(
        this.httpService
          .post(
            `${this.baseUrl}/api/ml/classify`,
            { image_url: imageUrl },
            { headers: this.getHeaders() },
          )
          .pipe(
            timeout(this.timeout),
            catchError((error: AxiosError) => {
              throw this.handleError(error);
            }),
          ),
      );

      return response.data;
    } catch (error) {
      this.logger.error('Classification failed', error);
      throw error;
    }
  }

  /**
   * Extraer embedding de imagen
   */
  async extractEmbedding(
    productId: string,
    imageUrl: string,
  ): Promise<EmbeddingResult> {
    try {
      this.logger.log(`Extracting embedding for product: ${productId}`);

      const response = await firstValueFrom(
        this.httpService
          .post(
            `${this.baseUrl}/api/ml/embeddings/extract`,
            {
              product_id: productId,
              image_url: imageUrl,
            },
            { headers: this.getHeaders() },
          )
          .pipe(
            timeout(this.timeout),
            catchError((error: AxiosError) => {
              throw this.handleError(error);
            }),
          ),
      );

      return response.data;
    } catch (error) {
      this.logger.error('Embedding extraction failed', error);
      throw error;
    }
  }

  /**
   * Buscar productos similares
   */
  async findSimilarProducts(
    productId: string,
    limit: number = 10,
  ): Promise<SimilarProduct[]> {
    try {
      this.logger.log(`Finding similar products for: ${productId}`);

      const response = await firstValueFrom(
        this.httpService
          .post(
            `${this.baseUrl}/api/ml/embeddings/find-similar`,
            {
              product_id: productId,
              top_k: limit,
            },
            { headers: this.getHeaders() },
          )
          .pipe(
            timeout(this.timeout),
            catchError((error: AxiosError) => {
              throw this.handleError(error);
            }),
          ),
      );

      return response.data.similar_products || [];
    } catch (error) {
      this.logger.error('Similar products search failed', error);
      throw error;
    }
  }

  /**
   * Obtener recomendaciones para usuario
   */
  async getRecommendations(
    userId: string,
    strategy: 'visual' | 'collaborative' | 'hybrid' = 'hybrid',
    limit: number = 10,
  ): Promise<RecommendedProduct[]> {
    try {
      this.logger.log(`Getting recommendations for user: ${userId}`);

      const response = await firstValueFrom(
        this.httpService
          .post(
            `${this.baseUrl}/api/ml/recommendations/get`,
            {
              user_id: userId,
              strategy,
              limit,
            },
            { headers: this.getHeaders() },
          )
          .pipe(
            timeout(this.timeout),
            catchError((error: AxiosError) => {
              throw this.handleError(error);
            }),
          ),
      );

      return response.data.recommendations || [];
    } catch (error) {
      this.logger.error('Recommendations failed', error);
      throw error;
    }
  }

  /**
   * Registrar interacción usuario-producto
   */
  async registerInteraction(
    userId: string,
    productId: string,
    interactionType: 'view' | 'like' | 'cart' | 'purchase',
  ): Promise<void> {
    try {
      this.logger.log(`Registering ${interactionType} interaction: ${userId} -> ${productId}`);

      await firstValueFrom(
        this.httpService
          .post(
            `${this.baseUrl}/api/ml/recommendations/interaction`,
            {
              user_id: userId,
              product_id: productId,
              interaction_type: interactionType,
            },
            { headers: this.getHeaders() },
          )
          .pipe(
            timeout(5000), // Timeout corto para interacciones
            catchError((error: AxiosError) => {
              // Log pero no fallar - las interacciones no son críticas
              this.logger.warn(`Interaction registration failed: ${error.message}`);
              return Promise.resolve(null);
            }),
          ),
      );
    } catch (error) {
      this.logger.warn('Interaction registration failed (non-critical)', error);
      // No throw - las interacciones son best-effort
    }
  }

  /**
   * Obtener métricas del modelo
   */
  async getModelMetrics(): Promise<ModelMetrics> {
    try {
      const response = await firstValueFrom(
        this.httpService
          .get(`${this.baseUrl}/api/ml/metrics/overall`, {
            headers: this.getHeaders(),
          })
          .pipe(
            timeout(10000),
            catchError((error: AxiosError) => {
              throw this.handleError(error);
            }),
          ),
      );

      return response.data;
    } catch (error) {
      this.logger.error('Metrics retrieval failed', error);
      throw error;
    }
  }

  /**
   * Health check del ML Service
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await firstValueFrom(
        this.httpService
          .get(`${this.baseUrl}/health`)
          .pipe(timeout(5000)),
      );

      return response.status === 200;
    } catch (error) {
      this.logger.warn('ML Service health check failed');
      return false;
    }
  }
}

// ===== Interfaces =====

export interface ClassificationResult {
  success: boolean;
  predicted_class: string;
  confidence: number;
  top_3_predictions: Array<{
    class: string;
    confidence: number;
  }>;
}

export interface EmbeddingResult {
  success: boolean;
  product_id: string;
  embedding_id: string;
  dimension: number;
}

export interface SimilarProduct {
  product_id: string;
  similarity_score: number;
  distance: number;
}

export interface RecommendedProduct {
  product_id: string;
  score: number;
  reason: string;
}

export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  total_predictions: number;
  average_inference_time: number;
}
```

---

## 🎯 Consumir Endpoints ML

### 4. Integrar en Product Service

**`src/products/products.service.ts`:**

```typescript
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Product } from './entities/product.entity';
import { MlServiceClient } from '../ml-service/ml-service.client';

@Injectable()
export class ProductsService {
  constructor(
    @InjectRepository(Product)
    private productsRepository: Repository<Product>,
    private mlServiceClient: MlServiceClient,
  ) {}

  /**
   * Crear producto y extraer features ML
   */
  async createProduct(createProductDto: CreateProductDto): Promise<Product> {
    // 1. Guardar producto en PostgreSQL
    const product = this.productsRepository.create(createProductDto);
    await this.productsRepository.save(product);

    // 2. Extraer embedding en background (async, no bloqueante)
    this.extractProductFeatures(product.id, product.imageUrl)
      .catch(err => console.error('ML feature extraction failed:', err));

    return product;
  }

  /**
   * Extracción de features ML (async)
   */
  private async extractProductFeatures(
    productId: string,
    imageUrl: string,
  ): Promise<void> {
    try {
      // Clasificar imagen
      const classification = await this.mlServiceClient.classifyProduct(imageUrl);
      
      // Extraer embedding para similarity search
      await this.mlServiceClient.extractEmbedding(productId, imageUrl);

      // Actualizar producto con clasificación ML
      await this.productsRepository.update(productId, {
        mlCategory: classification.predicted_class,
        mlConfidence: classification.confidence,
      });
    } catch (error) {
      console.error(`ML processing failed for product ${productId}:`, error);
    }
  }

  /**
   * Buscar productos similares
   */
  async getSimilarProducts(productId: string, limit: number = 10): Promise<Product[]> {
    // Obtener IDs de productos similares del ML Service
    const similarProducts = await this.mlServiceClient.findSimilarProducts(
      productId,
      limit,
    );

    // Fetch detalles de productos desde PostgreSQL
    const productIds = similarProducts.map(p => p.product_id);
    const products = await this.productsRepository.findByIds(productIds);

    // Agregar similarity score
    return products.map(product => ({
      ...product,
      similarityScore: similarProducts.find(p => p.product_id === product.id)?.similarity_score,
    }));
  }
}
```

### 5. Crear GraphQL Resolvers

**`src/products/products.resolver.ts`:**

```typescript
import { Resolver, Query, Mutation, Args } from '@nestjs/graphql';
import { ProductsService } from './products.service';
import { Product } from './entities/product.entity';

@Resolver(() => Product)
export class ProductsResolver {
  constructor(private productsService: ProductsService) {}

  @Query(() => [Product])
  async similarProducts(
    @Args('productId') productId: string,
    @Args('limit', { defaultValue: 10 }) limit: number,
  ): Promise<Product[]> {
    return this.productsService.getSimilarProducts(productId, limit);
  }

  @Mutation(() => Product)
  async createProduct(
    @Args('input') input: CreateProductInput,
  ): Promise<Product> {
    return this.productsService.createProduct(input);
  }
}
```

### 6. Integrar Recomendaciones

**`src/recommendations/recommendations.service.ts`:**

```typescript
import { Injectable } from '@nestjs/common';
import { MlServiceClient } from '../ml-service/ml-service.client';
import { ProductsService } from '../products/products.service';

@Injectable()
export class RecommendationsService {
  constructor(
    private mlServiceClient: MlServiceClient,
    private productsService: ProductsService,
  ) {}

  /**
   * Obtener recomendaciones personalizadas
   */
  async getPersonalizedRecommendations(
    userId: string,
    limit: number = 10,
  ) {
    // Obtener recomendaciones del ML Service
    const mlRecommendations = await this.mlServiceClient.getRecommendations(
      userId,
      'hybrid', // visual + collaborative filtering
      limit,
    );

    // Enriquecer con datos de PostgreSQL
    const productIds = mlRecommendations.map(r => r.product_id);
    const products = await this.productsService.findByIds(productIds);

    return products.map(product => ({
      ...product,
      mlScore: mlRecommendations.find(r => r.product_id === product.id)?.score,
      mlReason: mlRecommendations.find(r => r.product_id === product.id)?.reason,
    }));
  }

  /**
   * Registrar interacción (llamar desde eventos)
   */
  async trackInteraction(
    userId: string,
    productId: string,
    action: 'view' | 'like' | 'cart' | 'purchase',
  ): Promise<void> {
    // Fire-and-forget (no await)
    this.mlServiceClient
      .registerInteraction(userId, productId, action)
      .catch(err => console.warn('ML interaction tracking failed:', err));
  }
}
```

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Clasificar Producto al Subirlo

```typescript
// En tu ProductsController o Service

async uploadProductImage(file: Express.Multer.File, productId: string) {
  // 1. Subir imagen a storage (S3, GCS, etc.)
  const imageUrl = await this.storageService.upload(file);

  // 2. Clasificar con ML
  const classification = await this.mlServiceClient.classifyProduct(imageUrl);

  // 3. Actualizar producto
  await this.productsRepository.update(productId, {
    imageUrl,
    category: classification.predicted_class,
    mlConfidence: classification.confidence,
  });

  return {
    imageUrl,
    category: classification.predicted_class,
    confidence: classification.confidence,
  };
}
```

### Ejemplo 2: Página de Producto con "Similares"

```typescript
// GraphQL Query desde Frontend
query GetProductWithSimilar($id: ID!) {
  product(id: $id) {
    id
    name
    price
    imageUrl
    
    # Productos similares vía ML
    similarProducts(limit: 6) {
      id
      name
      price
      imageUrl
      similarityScore
    }
  }
}
```

```typescript
// Resolver en NestJS
@ResolveField(() => [Product])
async similarProducts(
  @Parent() product: Product,
  @Args('limit', { defaultValue: 6 }) limit: number,
) {
  return this.productsService.getSimilarProducts(product.id, limit);
}
```

### Ejemplo 3: Recomendaciones en Homepage

```typescript
// GraphQL Query
query GetRecommendations($userId: ID!) {
  recommendations(userId: $userId, limit: 12) {
    id
    name
    price
    imageUrl
    mlScore
    mlReason  # "Based on visual similarity" o "Often viewed together"
  }
}
```

```typescript
// Resolver
@Query(() => [Product])
async recommendations(
  @Args('userId') userId: string,
  @Args('limit', { defaultValue: 12 }) limit: number,
) {
  return this.recommendationsService.getPersonalizedRecommendations(userId, limit);
}
```

### Ejemplo 4: Track User Interactions

```typescript
// En ProductsController (evento de vista de producto)
@Get(':id')
async getProduct(@Param('id') id: string, @Req() req) {
  const product = await this.productsService.findOne(id);
  
  // Track view (async, no bloquea response)
  if (req.user) {
    this.recommendationsService.trackInteraction(
      req.user.id,
      id,
      'view'
    );
  }
  
  return product;
}

// En CartService (agregar al carrito)
async addToCart(userId: string, productId: string) {
  // ... lógica de carrito ...
  
  // Track cart interaction
  this.recommendationsService.trackInteraction(userId, productId, 'cart');
}

// En OrdersService (compra)
async createOrder(userId: string, items: OrderItem[]) {
  // ... crear orden ...
  
  // Track purchases
  for (const item of items) {
    this.recommendationsService.trackInteraction(userId, item.productId, 'purchase');
  }
}
```

---

## ⚠️ Manejo de Errores

### Strategy 1: Graceful Degradation

```typescript
async getSimilarProducts(productId: string): Promise<Product[]> {
  try {
    // Intentar obtener similares con ML
    return await this.mlServiceClient.findSimilarProducts(productId);
  } catch (error) {
    this.logger.warn('ML Service unavailable, falling back to category matching');
    
    // Fallback: productos de la misma categoría
    const product = await this.productsRepository.findOne(productId);
    return this.productsRepository.find({
      where: { category: product.category },
      take: 10,
    });
  }
}
```

### Strategy 2: Circuit Breaker

```typescript
// Instalar: npm install opossum
import * as CircuitBreaker from 'opossum';

constructor(private mlServiceClient: MlServiceClient) {
  this.classifyBreaker = new CircuitBreaker(
    (imageUrl: string) => this.mlServiceClient.classifyProduct(imageUrl),
    {
      timeout: 30000,
      errorThresholdPercentage: 50,
      resetTimeout: 60000,
    }
  );
  
  this.classifyBreaker.on('open', () => {
    this.logger.warn('Circuit breaker opened for ML classification');
  });
}

async classifyWithCircuitBreaker(imageUrl: string) {
  return this.classifyBreaker.fire(imageUrl);
}
```

---

## ✅ Best Practices

### 1. Async Processing (No Bloqueante)

```typescript
// ❌ MAL: Bloquea la respuesta
async createProduct(dto: CreateProductDto) {
  const product = await this.save(dto);
  await this.mlServiceClient.extractEmbedding(product.id, product.imageUrl); // Espera ML
  return product;
}

// ✅ BIEN: Fire-and-forget
async createProduct(dto: CreateProductDto) {
  const product = await this.save(dto);
  
  // Proceso ML en background
  this.mlServiceClient
    .extractEmbedding(product.id, product.imageUrl)
    .catch(err => this.logger.error('ML processing failed', err));
  
  return product; // Responde inmediatamente
}
```

### 2. Caching de Recomendaciones

```typescript
// Usar Redis para cachear recomendaciones
import { CACHE_MANAGER, Inject } from '@nestjs/common';
import { Cache } from 'cache-manager';

@Injectable()
export class RecommendationsService {
  constructor(
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private mlServiceClient: MlServiceClient,
  ) {}

  async getRecommendations(userId: string) {
    const cacheKey = `recommendations:${userId}`;
    
    // Check cache primero
    let recommendations = await this.cacheManager.get(cacheKey);
    
    if (!recommendations) {
      // Cache miss: fetch de ML Service
      recommendations = await this.mlServiceClient.getRecommendations(userId);
      
      // Cache por 1 hora
      await this.cacheManager.set(cacheKey, recommendations, { ttl: 3600 });
    }
    
    return recommendations;
  }
}
```

### 3. Retry Logic

```typescript
import { retry } from 'rxjs/operators';

async classifyWithRetry(imageUrl: string) {
  return firstValueFrom(
    this.httpService
      .post(`${this.baseUrl}/api/ml/classify`, { image_url: imageUrl })
      .pipe(
        retry(3), // Reintentar 3 veces
        timeout(30000),
      ),
  );
}
```

### 4. Health Monitoring

```typescript
// Health check endpoint en ERP
@Controller('health')
export class HealthController {
  constructor(private mlServiceClient: MlServiceClient) {}

  @Get('ml-service')
  async checkMlService() {
    const isHealthy = await this.mlServiceClient.healthCheck();
    
    return {
      service: 'ml-service',
      status: isHealthy ? 'healthy' : 'unhealthy',
      timestamp: new Date().toISOString(),
    };
  }
}
```

---

## 🚀 Próximos Pasos

1. ✅ Implementar ML Service Client en NestJS
2. ✅ Integrar clasificación en upload de productos
3. ✅ Agregar "Productos Similares" en página de producto
4. ⏭️ Implementar recomendaciones personalizadas en homepage
5. ⏭️ Track user interactions para mejorar recomendaciones
6. ⏭️ Configurar caching con Redis
7. ⏭️ Implementar circuit breaker para resiliencia
8. ⏭️ Monitorear métricas de ML en dashboard admin

---

**¿Preguntas?** Esta integración permite que tu ERP consuma el ML Service de forma limpia y escalable, manteniendo la separación de responsabilidades entre microservicios.
