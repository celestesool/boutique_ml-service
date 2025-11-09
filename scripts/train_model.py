"""
Script to train initial classification model
"""

import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import os

# Configuration
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 10
NUM_CLASSES = 10

# Paths (rutas absolutas para ejecutar desde ml-service/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAIN_DIR = os.path.join(BASE_DIR, "data", "train")
VAL_DIR = os.path.join(BASE_DIR, "data", "validation")
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "models", "fashion_classifier.h5")


def create_model():
    """Create CNN model using transfer learning"""
    
    # Load pre-trained EfficientNetB0
    base_model = EfficientNetB0(
        include_top=False,
        weights='imagenet',
        input_shape=(IMG_SIZE, IMG_SIZE, 3)
    )
    
    # Freeze base model
    base_model.trainable = False
    
    # Create new model
    model = models.Sequential([
        # Base model (ya recibe imágenes RGB del ImageDataGenerator)
        base_model,
        
        # Custom top layers
        layers.GlobalAveragePooling2D(),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.5),
        layers.Dense(NUM_CLASSES, activation='softmax')
    ])
    
    return model


def train_model():
    """Train the classification model"""
    
    print("🧠 Creating model...")
    model = create_model()
    
    # Compile model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # Data augmentation con preprocessing correcto para EfficientNet
    train_datagen = ImageDataGenerator(
        preprocessing_function=preprocess_input,  # Normalización de ImageNet
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    
    val_datagen = ImageDataGenerator(preprocessing_function=preprocess_input)
    
    # Load data
    print("\n📂 Loading training data...")
    train_generator = train_datagen.flow_from_directory(
        TRAIN_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        color_mode='rgb'  # Convertir a RGB automáticamente
    )
    
    print("\n📂 Loading validation data...")
    val_generator = val_datagen.flow_from_directory(
        VAL_DIR,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        color_mode='rgb'  # Convertir a RGB automáticamente
    )
    
    # Callbacks
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            MODEL_SAVE_PATH,
            save_best_only=True,
            monitor='val_accuracy',
            verbose=1
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1
        )
    ]
    
    # Train model
    print("\n🚀 Starting training...\n")
    history = model.fit(
        train_generator,
        validation_data=val_generator,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    
    # Save final model
    model.save(MODEL_SAVE_PATH)
    print(f"\n✅ Model saved to: {MODEL_SAVE_PATH}")
    
    # Print final metrics
    final_acc = history.history['accuracy'][-1]
    final_val_acc = history.history['val_accuracy'][-1]
    print(f"\n📊 Final Training Accuracy: {final_acc:.4f}")
    print(f"📊 Final Validation Accuracy: {final_val_acc:.4f}")


if __name__ == "__main__":
    # Check if dataset exists
    if not os.path.exists(TRAIN_DIR):
        print("❌ Error: Training dataset not found!")
        print("   Please run 'python download_dataset.py' first.")
        exit(1)
    
    train_model()
