"""
IDS Model Training using NSL-KDD Dataset
Trains a Random Forest classifier for network intrusion detection
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
from pathlib import Path
import sys

# Constants
CATEGORICAL_COLUMNS = ['protocol_type', 'service', 'flag']
RANDOM_STATE = 42
N_ESTIMATORS = 100
MAX_DEPTH = 20

# Column names for NSL-KDD dataset
columns = [
    'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
    'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
    'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
    'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
    'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
    'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
    'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
    'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
    'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
    'dst_host_rerror_rate', 'dst_host_srv_rerror_rate', 'attack_type', 'difficulty'
]

def load_and_preprocess_data(train_file, test_file):
    """Load and preprocess NSL-KDD dataset - optimized"""
    print("Loading datasets...")
    
    # Convert to Path objects
    train_path = Path(train_file)
    test_path = Path(test_file)
    
    if not train_path.exists():
        raise FileNotFoundError(f"Training file not found: {train_file}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test file not found: {test_file}")
    
    # Load training and test data with optimized dtypes
    print("Reading CSV files...")
    train_df = pd.read_csv(train_path, names=columns, header=None, low_memory=False)
    test_df = pd.read_csv(test_path, names=columns, header=None, low_memory=False)
    
    # Remove difficulty column
    train_df = train_df.drop(['difficulty'], axis=1)
    test_df = test_df.drop(['difficulty'], axis=1)
    
    # Binary classification: normal vs attack - vectorized for performance
    train_df['label'] = (train_df['attack_type'] != 'normal').astype(int)
    test_df['label'] = (test_df['attack_type'] != 'normal').astype(int)
    
    # Store attack types for reference
    train_df['attack_category'] = train_df['attack_type']
    test_df['attack_category'] = test_df['attack_type']
    
    # Drop attack_type column
    train_df = train_df.drop(['attack_type'], axis=1)
    test_df = test_df.drop(['attack_type'], axis=1)
    
    print(f"Training samples: {len(train_df):,}, Test samples: {len(test_df):,}")
    print(f"Normal: {len(train_df[train_df['label']==0]):,}, Attacks: {len(train_df[train_df['label']==1]):,}")
    
    return train_df, test_df

def encode_features(train_df, test_df):
    """Encode categorical features - optimized"""
    print("Encoding categorical features...")
    
    label_encoders = {}
    
    for col in CATEGORICAL_COLUMNS:
        le = LabelEncoder()
        # Fit on training data
        train_df[col] = le.fit_transform(train_df[col].astype(str))
        
        # Transform test data, handle unseen labels more efficiently
        test_series = test_df[col].astype(str)
        # Use map for better performance than apply
        test_df[col] = test_series.map(
            lambda x: le.transform([x])[0] if x in le.classes_ else -1
        )
        label_encoders[col] = le
        print(f"  {col}: {len(le.classes_)} unique values")
    
    return train_df, test_df, label_encoders

def train_model(train_df, test_df):
    """Train Random Forest classifier - optimized"""
    print("Training model...")
    
    # Separate features and labels
    feature_cols = [col for col in train_df.columns if col not in ['label', 'attack_category']]
    X_train = train_df[feature_cols]
    y_train = train_df['label']
    
    X_test = test_df[feature_cols]
    y_test = test_df['label']
    
    print(f"Features: {len(feature_cols)}")
    print(f"Training set shape: {X_train.shape}")
    print(f"Test set shape: {X_test.shape}")
    
    # Standardize features
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    print("Training Random Forest classifier...")
    rf_model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=1
    )
    
    rf_model.fit(X_train_scaled, y_train)
    
    # Predictions
    print("Making predictions...")
    y_pred = rf_model.predict(X_test_scaled)
    
    # Evaluation
    print("\n=== Model Evaluation ===")
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Important Features:")
    print(feature_importance.head(10).to_string(index=False))
    
    return rf_model, scaler, feature_cols

def save_model(model, scaler, feature_names, label_encoders, output_dir='../data'):
    """Save trained model and preprocessing objects - optimized"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\nSaving model to {output_path}...")
    
    # Save all files
    joblib.dump(model, output_path / 'ids_model.pkl')
    joblib.dump(scaler, output_path / 'scaler.pkl')
    joblib.dump(feature_names, output_path / 'feature_names.pkl')
    joblib.dump(label_encoders, output_path / 'label_encoders.pkl')
    
    print("✓ Model saved successfully!")
    print(f"  - Model: {output_path / 'ids_model.pkl'}")
    print(f"  - Scaler: {output_path / 'scaler.pkl'}")
    print(f"  - Features: {output_path / 'feature_names.pkl'}")
    print(f"  - Encoders: {output_path / 'label_encoders.pkl'}")

if __name__ == "__main__":
    # File paths - relative to script location
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / 'data'
    train_file = data_dir / 'KDDTrain+.txt'
    test_file = data_dir / 'KDDTest+.txt'
    
    try:
        # Load and preprocess
        train_df, test_df = load_and_preprocess_data(train_file, test_file)
        
        # Encode categorical features
        train_df, test_df, label_encoders = encode_features(train_df, test_df)
        
        # Train model
        model, scaler, feature_names = train_model(train_df, test_df)
        
        # Save model
        save_model(model, scaler, feature_names, label_encoders, output_dir=str(data_dir))
        
        print("\n✓ Training completed successfully!")
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nPlease download NSL-KDD dataset from: https://www.unb.ca/cic/datasets/nsl.html")
        print(f"Place KDDTrain+.txt and KDDTest+.txt in the {data_dir} directory")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)