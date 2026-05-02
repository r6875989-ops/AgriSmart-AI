"""
backend/training/train_disease.py
───────────────────────────────────
Train MobileNetV2 CNN on PlantVillage dataset.

FIXES applied vs original:
  1. DATASET_DIR reads from env variable PLANTVILLAGE_PATH (portable — works on any machine)
  2. disease_info stores BOTH int and str keys → fixes runtime key-type mismatch
  3. Exits with clear message if dataset folder not found
  4. Saves model metadata JSON with corrected class names (double underscores cleaned)
"""

import os
import sys
import json
import joblib
import numpy as np

# ─── Suppress TF verbose logs ─────────────────────────────────────────────────
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import (
    Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
)
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
)

print("=" * 65)
print("🌿  CROP DISEASE DETECTION — MODEL TRAINING")
print("=" * 65)
print(f"    TensorFlow: {tf.__version__}")

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

# FIX 1: Use environment variable so the script works on any machine.
# Usage: set PLANTVILLAGE_PATH=C:\your\path\PlantVillage   (Windows)
#         export PLANTVILLAGE_PATH=/your/path/PlantVillage  (Linux/Mac)
# Falls back to the original hardcoded path if the env var is not set.
DATASET_DIR = os.environ.get(
    'PLANTVILLAGE_PATH',
    r'C:\Users\r6875\OneDrive\Desktop\project_Agri(Data_set)\PlantVillage'
)

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

IMG_SIZE      = 224    # MobileNetV2 expected input
BATCH_SIZE    = 32
EPOCHS        = 15
LEARNING_RATE = 0.001

# ─── Verify dataset path ───────────────────────────────────────────────────────
if not os.path.exists(DATASET_DIR):
    print(f"\n❌  Dataset not found at: {DATASET_DIR}")
    print("    Please set the env variable:")
    print("      Windows: set PLANTVILLAGE_PATH=C:\\path\\to\\PlantVillage")
    print("      Linux:   export PLANTVILLAGE_PATH=/path/to/PlantVillage")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# 1. DATASET EXPLORATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n📊  Dataset Analysis:")

classes = sorted([
    d for d in os.listdir(DATASET_DIR)
    if os.path.isdir(os.path.join(DATASET_DIR, d)) and d != 'PlantVillage'
])

total_images = 0
for cls in classes:
    count = len(os.listdir(os.path.join(DATASET_DIR, cls)))
    total_images += count
    print(f"    {cls}: {count} images")

print(f"\n    Total: {total_images:,} images across {len(classes)} classes")

# ══════════════════════════════════════════════════════════════════════════════
# 2. DATA GENERATORS WITH AUGMENTATION
# ══════════════════════════════════════════════════════════════════════════════
print("\n🔧  Setting up data generators with augmentation...")

train_datagen = ImageDataGenerator(
    rescale=1. / 255,
    rotation_range=30,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest',
    validation_split=0.2,
)

train_generator = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='training',
    shuffle=True,
    seed=42,
    classes=classes,
)

val_generator = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='categorical',
    subset='validation',
    shuffle=False,
    seed=42,
    classes=classes,
)

NUM_CLASSES = len(train_generator.class_indices)
print(f"    Training samples:   {train_generator.samples:,}")
print(f"    Validation samples: {val_generator.samples:,}")
print(f"    Number of classes:  {NUM_CLASSES}")

# ══════════════════════════════════════════════════════════════════════════════
# 3. BUILD MODEL — MobileNetV2 TRANSFER LEARNING
# ══════════════════════════════════════════════════════════════════════════════
print("\n🏗️   Building MobileNetV2 transfer learning model...")

base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
)
base_model.trainable = False

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = BatchNormalization()(x)
x = Dense(256, activation='relu')(x)
x = Dropout(0.5)(x)
x = BatchNormalization()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.3)(x)
predictions = Dense(NUM_CLASSES, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=predictions)

trainable   = sum(tf.keras.backend.count_params(w) for w in model.trainable_weights)
nontrainable = sum(tf.keras.backend.count_params(w) for w in model.non_trainable_weights)
print(f"    Trainable params:     {trainable:,}")
print(f"    Non-trainable params: {nontrainable:,}")

# ══════════════════════════════════════════════════════════════════════════════
# 4. COMPILE & CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════
model_path = os.path.join(MODELS_DIR, 'disease_model.h5')

model.compile(
    optimizer=Adam(learning_rate=LEARNING_RATE),
    loss='categorical_crossentropy',
    metrics=['accuracy'],
)

callbacks = [
    EarlyStopping(monitor='val_accuracy', patience=5,
                  restore_best_weights=True, verbose=1),
    ReduceLROnPlateau(monitor='val_loss', factor=0.5,
                      patience=3, min_lr=1e-7, verbose=1),
    ModelCheckpoint(model_path, monitor='val_accuracy',
                    save_best_only=True, verbose=1),
]

steps_per_epoch  = train_generator.samples // BATCH_SIZE
validation_steps = val_generator.samples   // BATCH_SIZE

# ══════════════════════════════════════════════════════════════════════════════
# 5. PHASE 1 — Train classification head (base frozen)
# ══════════════════════════════════════════════════════════════════════════════
print("\n🚀  Phase 1: Training classification head (base frozen)...")

model.fit(
    train_generator,
    epochs=8,
    validation_data=val_generator,
    steps_per_epoch=steps_per_epoch,
    validation_steps=validation_steps,
    callbacks=callbacks,
    verbose=1,
)

# ══════════════════════════════════════════════════════════════════════════════
# 6. PHASE 2 — Fine-tune last 30 layers
# ══════════════════════════════════════════════════════════════════════════════
print("\n🔧  Phase 2: Fine-tuning last 30 layers of MobileNetV2...")

base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

model.compile(
    optimizer=Adam(learning_rate=LEARNING_RATE / 10),
    loss='categorical_crossentropy',
    metrics=['accuracy'],
)

model.fit(
    train_generator,
    epochs=EPOCHS,
    validation_data=val_generator,
    steps_per_epoch=steps_per_epoch,
    validation_steps=validation_steps,
    callbacks=callbacks,
    verbose=1,
)

# ══════════════════════════════════════════════════════════════════════════════
# 7. EVALUATE
# ══════════════════════════════════════════════════════════════════════════════
print("\n📈  Final Evaluation:")
val_loss, val_acc = model.evaluate(val_generator, steps=validation_steps, verbose=0)
print(f"    Validation Loss:     {val_loss:.4f}")
print(f"    Validation Accuracy: {val_acc:.4f}  ({val_acc * 100:.1f}%)")

# ══════════════════════════════════════════════════════════════════════════════
# 8. SAVE MODEL + CLASS MAPPING
# ══════════════════════════════════════════════════════════════════════════════
model.save(model_path)
print(f"\n💾  Model saved: {model_path}")

# ── Build class mapping ────────────────────────────────────────────────────────
class_indices = train_generator.class_indices           # {"Tomato_healthy": 14, ...}
idx_to_class  = {v: k for k, v in class_indices.items()}  # {14: "Tomato_healthy", ...}

import re

def clean_class_name(cls_name: str) -> tuple:
    """Parse 'Tomato__Tomato_YellowLeaf__Curl_Virus' → crop, disease, is_healthy."""
    # Normalise double underscores
    normalised = re.sub(r'_+', '_', cls_name).strip('_')
    parts = normalised.split('_')
    crop  = parts[0]
    rest  = parts[1:] if len(parts) > 1 else []
    is_healthy = 'healthy' in cls_name.lower()
    disease = 'Healthy' if is_healthy else ' '.join(rest).strip()
    return crop, disease, is_healthy


# FIX 2: Store BOTH int and str keys in disease_info dict.
# This prevents key-type mismatch bugs at runtime (Bug 3 in the analysis).
disease_info = {}
for idx, cls_name in idx_to_class.items():
    crop, disease, is_healthy = clean_class_name(cls_name)
    entry = {
        'class_name': cls_name,
        'crop':       crop,
        'disease':    disease,
        'is_healthy': is_healthy,
    }
    disease_info[idx]        = entry   # int key  (for Python dict access)
    disease_info[str(idx)]   = entry   # str key  (for JSON-round-tripped dicts)

classes_data = {
    'class_indices': class_indices,
    'idx_to_class':  idx_to_class,
    'disease_info':  disease_info,   # has both int and str keys
    'num_classes':   NUM_CLASSES,
    'img_size':      IMG_SIZE,
    'accuracy':      float(val_acc),
}

classes_path = os.path.join(MODELS_DIR, 'disease_classes.pkl')
joblib.dump(classes_data, classes_path)
print(f"💾  Class mapping saved: {classes_path}")

# ── Save JSON metadata (human-readable) ───────────────────────────────────────
meta_path = os.path.join(MODELS_DIR, 'disease_model_meta.json')
with open(meta_path, 'w', encoding='utf-8') as f:
    # JSON can only have str keys — convert int keys to str
    json_disease_info = {
        str(k): v for k, v in disease_info.items() if isinstance(k, int)
    }
    json.dump({
        'model_type': 'MobileNetV2_TransferLearning',
        'img_size':   IMG_SIZE,
        'num_classes': NUM_CLASSES,
        'accuracy':   float(val_acc),
        'loss':       float(val_loss),
        'classes':    json_disease_info,
    }, f, indent=2, ensure_ascii=False)

print(f"📄  Metadata saved: {meta_path}")

print(f"\n✅  Training complete!")
print(f"    Model:    MobileNetV2 Transfer Learning")
print(f"    Accuracy: {val_acc * 100:.1f}%")
print(f"    Classes:  {NUM_CLASSES}")
print("=" * 65)