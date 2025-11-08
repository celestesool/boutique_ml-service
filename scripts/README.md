# Scripts de ML

Scripts utilitarios para entrenar y gestionar modelos de Machine Learning.

## 1. Descargar Dataset

```powershell
cd scripts
python download_dataset.py
```

Este script:
- Descarga Fashion-MNIST (70,000 imágenes)
- Organiza en carpetas train/validation/test
- Guarda imágenes en formato PNG

##  2. Entrenar Modelo

```powershell
cd scripts
python train_model.py
```

Este script:
- Crea modelo CNN con Transfer Learning (EfficientNetB0)
- Entrena con data augmentation
- Guarda el mejor modelo en `models/classifier_v1.h5`

**Tiempo estimado**: 20-30 minutos (con GPU), 1-2 horas (sin GPU)

##  Requisitos

Asegúrate de tener activado el entorno virtual:

```powershell
cd ..
.\venv\Scripts\activate
cd scripts
```

##  Resultados Esperados

- **Training Accuracy**: ~85-90%
- **Validation Accuracy**: ~80-85%

## 🚀 Próximos Scripts

- `create_embeddings.py` - Generar embeddings para productos
- `build_faiss_index.py` - Crear índice FAISS
- `test_model.py` - Probar modelo con imágenes nuevas
