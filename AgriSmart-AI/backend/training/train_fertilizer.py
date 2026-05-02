"""
Fertilizer Recommendation ML Model Training
============================================
Dataset: Fertilizer Prediction.csv
Features: Temperature, Humidity, Moisture, Soil Type, Crop Type, N, P, K
Target: Fertilizer Name (7 classes)
Model: Random Forest Classifier + Label Encoders
Output: fertilizer_model.pkl, fertilizer_encoders.pkl
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib
import os
import json

print("=" * 60)
print("🌱 FERTILIZER RECOMMENDATION MODEL TRAINING")
print("=" * 60)

# ===== 1. LOAD DATA =====
csv_path = r'c:\Users\r6875\OneDrive\Desktop\project_Agri(Data_set)\Fertilizer Prediction.csv'
df = pd.read_csv(csv_path)

print(f"\n📊 Dataset shape: {df.shape}")
print(f"   Features: {list(df.columns)}")
print(f"   Target classes: {df['Fertilizer Name'].nunique()}")
print(f"\n   Class distribution:")
for name, count in df['Fertilizer Name'].value_counts().items():
    print(f"     {name}: {count}")

# ===== 2. FEATURE ENGINEERING =====
# Encode categorical features
soil_encoder = LabelEncoder()
crop_encoder = LabelEncoder()
target_encoder = LabelEncoder()

df['Soil Type Encoded'] = soil_encoder.fit_transform(df['Soil Type'])
df['Crop Type Encoded'] = crop_encoder.fit_transform(df['Crop Type'])
df['Fertilizer Encoded'] = target_encoder.fit_transform(df['Fertilizer Name'])

# Create feature engineering
df['NPK_Total'] = df['Nitrogen'] + df['Potassium'] + df['Phosphorous']
df['N_Ratio'] = df['Nitrogen'] / (df['NPK_Total'] + 1)
df['P_Ratio'] = df['Phosphorous'] / (df['NPK_Total'] + 1)
df['K_Ratio'] = df['Potassium'] / (df['NPK_Total'] + 1)
df['Temp_Humidity_Ratio'] = df['Temparature'] / (df['Humidity '] + 1)
df['Moisture_Humidity_Ratio'] = df['Moisture'] / (df['Humidity '] + 1)

# Features
feature_cols = [
    'Temparature', 'Humidity ', 'Moisture', 
    'Soil Type Encoded', 'Crop Type Encoded',
    'Nitrogen', 'Potassium', 'Phosphorous',
    'NPK_Total', 'N_Ratio', 'P_Ratio', 'K_Ratio',
    'Temp_Humidity_Ratio', 'Moisture_Humidity_Ratio'
]

X = df[feature_cols].values
y = df['Fertilizer Encoded'].values

print(f"\n   Final features: {len(feature_cols)}")
print(f"   Feature names: {feature_cols}")

# ===== 3. TRAIN-TEST SPLIT =====
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"\n   Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")

# ===== 4. MODEL TRAINING WITH HYPERPARAMETER TUNING =====
print("\n🔧 Training Random Forest with GridSearchCV...")

param_grid = {
    'n_estimators': [100, 200, 300, 500],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 3, 5],
    'min_samples_leaf': [1, 2, 3],
    'max_features': ['sqrt', 'log2', None]
}

rf = RandomForestClassifier(random_state=42, class_weight='balanced')

# Use smaller grid for speed
fast_grid = {
    'n_estimators': [200, 300, 500],
    'max_depth': [None, 15, 25],
    'min_samples_split': [2, 3],
    'min_samples_leaf': [1, 2],
}

grid_search = GridSearchCV(
    rf, fast_grid, cv=5, scoring='accuracy', n_jobs=-1, verbose=0
)
grid_search.fit(X_train, y_train)

best_rf = grid_search.best_estimator_
print(f"   Best params: {grid_search.best_params_}")
print(f"   Best CV accuracy: {grid_search.best_score_:.4f}")

# ===== 5. ALSO TRAIN GRADIENT BOOSTING FOR COMPARISON =====
print("\n🔧 Training Gradient Boosting Classifier...")
gb = GradientBoostingClassifier(
    n_estimators=300, max_depth=5, learning_rate=0.1, 
    min_samples_split=3, random_state=42
)
gb.fit(X_train, y_train)
gb_score = gb.score(X_test, y_test)
print(f"   Gradient Boosting test accuracy: {gb_score:.4f}")

# ===== 6. EVALUATE BEST MODEL =====
rf_score = best_rf.score(X_test, y_test)
print(f"\n   Random Forest test accuracy: {rf_score:.4f}")

# Pick the best
if gb_score > rf_score:
    best_model = gb
    best_score = gb_score
    model_name = "GradientBoosting"
    print(f"   >>> Using Gradient Boosting (better)")
else:
    best_model = best_rf
    best_score = rf_score
    model_name = "RandomForest"
    print(f"   >>> Using Random Forest (better)")

# Cross-validation score
cv_scores = cross_val_score(best_model, X, y, cv=5, scoring='accuracy')
print(f"\n   5-Fold CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

# Detailed report
y_pred = best_model.predict(X_test)
print(f"\n📋 Classification Report:")
print(classification_report(y_test, y_pred, target_names=target_encoder.classes_))

# Feature importance
if hasattr(best_model, 'feature_importances_'):
    importances = best_model.feature_importances_
    print("\n📊 Feature Importances:")
    for feat, imp in sorted(zip(feature_cols, importances), key=lambda x: -x[1]):
        bar = "█" * int(imp * 50)
        print(f"   {feat:30s} {imp:.4f} {bar}")

# ===== 7. SAVE MODEL + ENCODERS =====
models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
os.makedirs(models_dir, exist_ok=True)

model_path = os.path.join(models_dir, 'fertilizer_model.pkl')
encoders_path = os.path.join(models_dir, 'fertilizer_encoders.pkl')

joblib.dump(best_model, model_path)
print(f"\n💾 Model saved: {model_path}")

# Save encoders and metadata
encoders_data = {
    'soil_encoder': soil_encoder,
    'crop_encoder': crop_encoder,
    'target_encoder': target_encoder,
    'feature_cols': feature_cols,
    'soil_classes': list(soil_encoder.classes_),
    'crop_classes': list(crop_encoder.classes_),
    'fertilizer_classes': list(target_encoder.classes_),
    'model_name': model_name,
    'accuracy': float(best_score),
    'cv_accuracy': float(cv_scores.mean()),
}
joblib.dump(encoders_data, encoders_path)
print(f"💾 Encoders saved: {encoders_path}")

# Also save a JSON metadata file for reference
meta_path = os.path.join(models_dir, 'fertilizer_model_meta.json')
with open(meta_path, 'w') as f:
    json.dump({
        'model_type': model_name,
        'accuracy': float(best_score),
        'cv_accuracy': float(cv_scores.mean()),
        'features': feature_cols,
        'soil_types': list(soil_encoder.classes_),
        'crop_types': list(crop_encoder.classes_),
        'fertilizer_types': list(target_encoder.classes_),
        'n_samples': len(df),
        'n_features': len(feature_cols),
    }, f, indent=2)
print(f"📄 Metadata saved: {meta_path}")

print(f"\n✅ Fertilizer Model Training Complete!")
print(f"   Model: {model_name}")
print(f"   Accuracy: {best_score:.2%}")
print(f"   CV Score: {cv_scores.mean():.2%}")
print("=" * 60)
