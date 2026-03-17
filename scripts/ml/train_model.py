"""
Intelligent Air Quality Model Training
Features: Confidence scoring, quality metrics, ensemble learning
Auto-combines CSV data with real-time ESP32 data from database
"""

import pandas as pd
import numpy as np
import joblib
import json
import subprocess
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.svm import SVR
from sklearn.linear_model import Ridge
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
MODELS_DIR = PROJECT_ROOT / 'models'
RESULTS_DIR = PROJECT_ROOT / 'results'

RESULTS_DIR.mkdir(exist_ok=True)


def run_data_pipeline():
    """Run data preparation pipeline or skip if processed data exists"""
    print("\n" + "="*70)
    print("CHECKING DATA")
    print("="*70)
    
    # Check if processed data already exists
    train_file = PROJECT_ROOT / 'data' / 'train_processed.csv'
    test_file = PROJECT_ROOT / 'data' / 'test_processed.csv'
    
    if train_file.exists() and test_file.exists():
        print(f"   ✓ Found existing processed data:")
        print(f"     - {train_file.name}")
        print(f"     - {test_file.name}")
        print("   ✓ Skipping data preparation pipeline")
        return True
    
    # Run pipeline if data doesn't exist
    print("   ⚠️  Processed data not found. Running preparation pipeline...")
    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / 'scripts' / 'prepare_data.py')],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print("   ✓ Data pipeline completed successfully")
            return True
        else:
            print(f"   ❌ Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error running pipeline: {e}")
        return False


def load_esp32_data_from_database():
    """Load real-time ESP32 data from SQLite database (if exists)"""
    db_path = PROJECT_ROOT / 'data' / 'database' / 'iot_data.db'
    
    if not db_path.exists():
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Query to get readings with required features
        query = """
        SELECT 
            temperature,
            humidity,
            mq135,
            predicted_aqi as target,
            timestamp
        FROM readings
        WHERE predicted_aqi IS NOT NULL
          AND temperature IS NOT NULL
          AND humidity IS NOT NULL
          AND mq135 IS NOT NULL
        ORDER BY timestamp DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) > 0:
            print(f"   ✓ Found {len(df):,} ESP32 readings in database")
            return df
        else:
            print("   ⚠️  Database exists but no readings found")
            return None
            
    except Exception as e:
        print(f"   ⚠️  Error loading database: {e}")
        return None


def engineer_features_for_esp32(df):
    """Engineer 23 features from raw ESP32 data (temperature, humidity, mq135)"""
    print("   ⚙️  Engineering features for ESP32 data...")
    
    # Base features are already present: temperature, humidity, mq135
    features_df = df[['temperature', 'humidity', 'mq135']].copy()
    
    # Feature engineering (same as preprocessing):
    # Interactions (6)
    features_df['temp_humidity'] = df['temperature'] * df['humidity']
    features_df['temp_mq135'] = df['temperature'] * df['mq135']
    features_df['humidity_mq135'] = df['humidity'] * df['mq135']
    features_df['temp_humidity_mq135'] = df['temperature'] * df['humidity'] * df['mq135']
    features_df['temp_per_humidity'] = df['temperature'] / (df['humidity'] + 1)
    features_df['mq135_per_temp'] = df['mq135'] / (df['temperature'] + 1)
    
    # Polynomials (6)
    features_df['temp_squared'] = df['temperature'] ** 2
    features_df['humidity_squared'] = df['humidity'] ** 2
    features_df['mq135_squared'] = df['mq135'] ** 2
    features_df['temp_cubed'] = df['temperature'] ** 3
    features_df['humidity_cubed'] = df['humidity'] ** 3
    features_df['mq135_cubed'] = df['mq135'] ** 3
    
    # Ratios (3)
    features_df['temp_humidity_ratio'] = df['temperature'] / (df['humidity'] + 1)
    features_df['mq135_temp_ratio'] = df['mq135'] / (df['temperature'] + 1)
    features_df['mq135_humidity_ratio'] = df['mq135'] / (df['humidity'] + 1)
    
    # Z-scores (3)
    for col in ['temperature', 'humidity', 'mq135']:
        mean = df[col].mean()
        std = df[col].std()
        features_df[f'{col}_zscore'] = (df[col] - mean) / (std + 1e-6)
    
    # Rolling averages (2)
    features_df['temp_rolling_mean'] = df['temperature'].rolling(window=10, min_periods=1).mean()
    features_df['humidity_rolling_mean'] = df['humidity'].rolling(window=10, min_periods=1).mean()
    
    # Add target
    features_df['target'] = df['target']
    
    print(f"   ✓ Created {len(features_df.columns)-1} features")
    return features_df


def combine_datasets(csv_train, csv_test, esp32_df):
    """Combine CSV training data with ESP32 real-time data"""
    print("\n" + "="*70)
    print("COMBINING DATASETS")
    print("="*70)
    
    # Combine CSV files
    csv_combined = pd.concat([csv_train, csv_test], ignore_index=True)
    print(f"\n   CSV Data: {len(csv_combined):,} samples")
    
    if esp32_df is None or len(esp32_df) == 0:
        print("   ESP32 Data: 0 samples (no database)")
        print(f"\n   ✓ Using CSV data only: {len(csv_combined):,} samples")
        return csv_combined
    
    # Engineer features for ESP32 data
    esp32_processed = engineer_features_for_esp32(esp32_df)
    print(f"   ESP32 Data: {len(esp32_processed):,} samples")
    
    # Ensure columns match
    csv_columns = set(csv_combined.columns)
    esp32_columns = set(esp32_processed.columns)
    
    # Use only common columns
    common_columns = csv_columns.intersection(esp32_columns)
    
    csv_filtered = csv_combined[list(common_columns)]
    esp32_filtered = esp32_processed[list(common_columns)]
    
    # Combine datasets
    combined = pd.concat([csv_filtered, esp32_filtered], ignore_index=True)
    combined = combined.drop_duplicates()
    
    print(f"\n   ✓ Combined dataset: {len(combined):,} samples")
    print(f"     - CSV:  {len(csv_combined):,} ({len(csv_combined)/len(combined)*100:.1f}%)")
    print(f"     - ESP32: {len(esp32_processed):,} ({len(esp32_processed)/len(combined)*100:.1f}%)")
    
    return combined


def calculate_confidence_factors(model, X, y_true, y_pred):
    """Calculate confidence factors for prediction quality"""
    
    # Factor 1: Model R² score (0-1)
    r2 = r2_score(y_true, y_pred)
    
    # Factor 2: Prediction consistency (inverse of std deviation)
    residuals = np.abs(y_true - y_pred)
    consistency = 1 / (1 + np.std(residuals))
    
    # Factor 3: Feature stability (if tree-based model)
    if hasattr(model, 'feature_importances_'):
        feature_importance = model.feature_importances_
        # High concentration = more stable
        stability = np.max(feature_importance) / np.mean(feature_importance)
        stability = min(stability / 10, 1.0)  # Normalize
    else:
        stability = 0.8  # Default for linear models
    
    # Combined confidence score
    confidence = (r2 * 0.5 + consistency * 0.3 + stability * 0.2)
    
    return {
        'overall': float(confidence),
        'r2_factor': float(r2),
        'consistency': float(consistency),
        'stability': float(stability)
    }


def main():
    """Main training pipeline with quality metrics"""
    print("\n" + "="*70)
    print("🚀 INTELLIGENT AIR QUALITY MODEL TRAINING")
    print("="*70)
    
    # Step 1: Run data pipeline
    if not run_data_pipeline():
        print("\n   ❌ Data pipeline failed!")
        return
    
    # Step 2: Load CSV processed data
    print("\n" + "="*70)
    print("LOADING DATA")
    print("="*70)
    
    train_file = DATA_DIR / 'train_processed.csv'
    test_file = DATA_DIR / 'test_processed.csv'
    
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)
    
    # Step 3: Check for ESP32 real-time data
    print("\n   🔍 Checking for ESP32 real-time data...")
    esp32_df = load_esp32_data_from_database()
    
    # Step 4: Combine datasets if ESP32 data exists
    if esp32_df is not None and len(esp32_df) > 0:
        combined_df = combine_datasets(train_df, test_df, esp32_df)
        print("\n   ✅ Training with COMBINED data (CSV + ESP32)")
    else:
        combined_df = pd.concat([train_df, test_df], ignore_index=True)
        print("\n   ✅ Training with CSV data only")
    
    # Split combined data for training
    from sklearn.model_selection import train_test_split
    
    X = combined_df.drop('target', axis=1)
    y = combined_df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )
    
    print(f"\n   📊 Final Dataset:")
    print(f"      Total samples: {len(combined_df):,}")
    print(f"      Training samples: {len(X_train):,}")
    print(f"      Test samples: {len(X_test):,}")
    print(f"      Features: {X_train.shape[1]}")
    
    # Step 3: Train ensemble model
    print("\n" + "="*70)
    print("TRAINING INTELLIGENT ENSEMBLE")
    print("="*70)
    
    print("\nCreating Voting Ensemble with quality optimization...")
    
    ensemble = VotingRegressor(
        estimators=[
            ('rf', RandomForestRegressor(n_estimators=200, max_depth=20, random_state=42, n_jobs=-1)),
            ('gb', GradientBoostingRegressor(n_estimators=150, learning_rate=0.1, max_depth=5, random_state=42)),
            ('ridge', Ridge(alpha=1.0, random_state=42)),
            ('svr', SVR(kernel='rbf', C=100, gamma='scale'))
        ],
        n_jobs=-1
    )
    
    print("   Training ensemble model...")
    ensemble.fit(X_train, y_train)
    
    # Predictions
    y_train_pred = ensemble.predict(X_train)
    y_test_pred = ensemble.predict(X_test)
    
    # Calculate metrics
    train_r2 = r2_score(y_train, y_train_pred)
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
    
    print(f"\n   Train R²: {train_r2:.6f} | MAE: {train_mae:.4f}")
    print(f"   Test R²:  {test_r2:.6f} | MAE: {test_mae:.4f}")
    
    # Step 4: Calculate confidence factors
    print("\n" + "="*70)
    print("CALCULATING QUALITY METRICS")
    print("="*70)
    
    confidence_factors = calculate_confidence_factors(
        ensemble.estimators_[0],  # Use Random Forest for feature importance
        X_test,
        y_test,
        y_test_pred
    )
    
    print(f"\n   Overall Confidence: {confidence_factors['overall']*100:.2f}%")
    print(f"   R² Factor: {confidence_factors['r2_factor']:.4f}")
    print(f"   Consistency: {confidence_factors['consistency']:.4f}")
    print(f"   Stability: {confidence_factors['stability']:.4f}")
    
    # Step 5: Save model
    print("\n" + "="*70)
    print("SAVING MODEL & METADATA")
    print("="*70)
    
    model_path = MODELS_DIR / 'air_quality_model_advanced.joblib'
    joblib.dump(ensemble, model_path)
    print(f"\n   Model saved: {model_path}")
    
    # Save feature names
    feature_names_path = MODELS_DIR / 'feature_names.joblib'
    joblib.dump(list(X_train.columns), feature_names_path)
    print(f"   Feature names saved: {feature_names_path}")
    
    # Save comprehensive metadata
    esp32_count = len(esp32_df) if esp32_df is not None else 0
    csv_count = len(combined_df) - esp32_count
    
    metadata = {
        'model_type': 'Intelligent Voting Ensemble',
        'algorithms': ['Random Forest', 'Gradient Boosting', 'Ridge', 'SVR'],
        'num_estimators': 4,
        'test_r2_score': float(test_r2),
        'test_mae': float(test_mae),
        'test_rmse': float(test_rmse),
        'training_date': datetime.now().isoformat(),
        'feature_names': list(X_train.columns),
        'data_sources': {
            'csv_samples': csv_count,
            'esp32_samples': esp32_count,
            'total_samples': len(combined_df),
            'has_esp32_data': esp32_count > 0
        },
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'confidence_factors': confidence_factors,
        'quality_thresholds': {
            'high': 0.90,
            'medium': 0.75,
            'low': 0.60
        },
        'alert_config': {
            'unhealthy_threshold': 100,
            'very_unhealthy_threshold': 150,
            'hazardous_threshold': 200,
            'cooldown_minutes': 15
        },
        'training_note': 'Auto-combines CSV + ESP32 data. Retrain after collecting ESP32 data for improved accuracy.'
    }
    
    metadata_path = MODELS_DIR / 'model_metadata_advanced.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"   Metadata saved: {metadata_path}")
    
    # Step 6: Summary
    print("\n" + "="*70)
    print("✅ TRAINING COMPLETED SUCCESSFULLY!")
    print("="*70)
    
    print("\n   📊 Model Performance:")
    print(f"      Test R²: {test_r2*100:.2f}%")
    print(f"      Test MAE: {test_mae:.3f}")
    print(f"      Overall Confidence: {confidence_factors['overall']*100:.2f}%")
    
    print("\n   📁 Data Sources:")
    if esp32_count > 0:
        print(f"      CSV Data: {csv_count:,} samples")
        print(f"      ESP32 Real-time: {esp32_count:,} samples")
        print(f"      ✅ Model includes real-world ESP32 data!")
    else:
        print(f"      CSV Data: {csv_count:,} samples")
        print(f"      ⚠️  No ESP32 data yet - collect and retrain for higher accuracy")
    print(f"      Total: {len(combined_df):,} samples")
    
    print("\n   🎯 Intelligent Features Enabled:")
    print("      ✓ Sliding Window Buffer (30 readings)")
    print("      ✓ Real-time Trend Analysis")
    print("      ✓ Anomaly Detection (Edge + Server)")
    print("      ✓ Adaptive Alert System")
    print("      ✓ Confidence Scoring")
    print("      ✓ Quality Assessment")
    print("      ✓ Auto ESP32 Data Integration")
    
    if esp32_count == 0:
        print("\n   💡 Next Steps:")
        print("      1. Run app_server.py to start web application")
        print("      2. Upload ESP32 firmware and collect data")
        print("      3. Retrain model to include ESP32 data:")
        print("         python advanced_model/scripts/train_model.py")
        print("      4. Model will automatically combine CSV + ESP32 data!")
    else:
        print("\n   💡 To improve further:")
        print(f"      Current ESP32 data: {esp32_count:,} samples")
        print("      Collect more data and retrain for even better accuracy!")
    
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
