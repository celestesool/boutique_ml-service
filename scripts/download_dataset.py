"""
Script to download Fashion-MNIST dataset
"""

import tensorflow as tf
from tensorflow.keras.datasets import fashion_mnist
import numpy as np
from PIL import Image
import os
from pathlib import Path

# Dataset labels mapping
FASHION_MNIST_LABELS = {
    0: "camiseta",
    1: "pantalon",
    2: "sueter",
    3: "vestido",
    4: "abrigo",
    5: "sandalia",
    6: "camisa",
    7: "zapatilla",
    8: "bolso",
    9: "bota"
}


def download_and_prepare_dataset():
    """Download Fashion-MNIST and save as images"""
    
    print("📥 Downloading Fashion-MNIST dataset...")
    (x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
    
    print(f"✅ Downloaded: {len(x_train)} training images, {len(x_test)} test images")
    
    # Create directories
    base_path = Path("../data")
    train_path = base_path / "train"
    val_path = base_path / "validation"
    test_path = base_path / "test"
    
    # Create subdirectories for each class
    for label_id, label_name in FASHION_MNIST_LABELS.items():
        (train_path / label_name).mkdir(parents=True, exist_ok=True)
        (val_path / label_name).mkdir(parents=True, exist_ok=True)
        (test_path / label_name).mkdir(parents=True, exist_ok=True)
    
    print("\n📁 Saving training images...")
    # Save training images (first 48000 for training, last 12000 for validation)
    for i in range(48000):
        label_id = y_train[i]
        label_name = FASHION_MNIST_LABELS[label_id]
        img = Image.fromarray(x_train[i])
        img.save(train_path / label_name / f"train_{i}.png")
        
        if i % 5000 == 0:
            print(f"  Saved {i}/48000 images...")
    
    print("\n📁 Saving validation images...")
    for i in range(48000, 60000):
        label_id = y_train[i]
        label_name = FASHION_MNIST_LABELS[label_id]
        img = Image.fromarray(x_train[i])
        img.save(val_path / label_name / f"val_{i}.png")
    
    print("\n📁 Saving test images...")
    for i in range(len(x_test)):
        label_id = y_test[i]
        label_name = FASHION_MNIST_LABELS[label_id]
        img = Image.fromarray(x_test[i])
        img.save(test_path / label_name / f"test_{i}.png")
        
        if i % 1000 == 0:
            print(f"  Saved {i}/{len(x_test)} images...")
    
    print("\n✅ Dataset prepared successfully!")
    print(f"   Training: {train_path}")
    print(f"   Validation: {val_path}")
    print(f"   Test: {test_path}")


if __name__ == "__main__":
    download_and_prepare_dataset()
