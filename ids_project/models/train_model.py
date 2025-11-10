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
import os

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
    """Load and preprocess NSL-KDD dataset"""
    print("Loading datasets...")
    
    # Load training and test data
    train_df = pd.read_csv(train_file, names=columns, header=None)
    test_df = pd.read_csv(test_file, names=columns, header=None)
    
    # Remove difficulty column
    train_df = train_df.drop(['difficulty'], axis=1)
    test_df = test_df.drop(['difficulty'], axis=1)
    
    # Binary classification: normal vs attack
    train_df['label'] = train_df['attack_type'].apply(lambda x: 0 if x == 'normal' else 1)
    test_df['label'] = test_df['attack_type'].apply(lambda x: 0 if x == 'normal' else 1)
    
    # Store attack types for reference
    train_df['attack_category'] = train_df['attack_type']
    test_df['attack_category'] = test_df['attack_type']
    
    # Drop attack_type column
    train_df = train_df.drop(['attack_type'], axis=1)
    test_df = test_df.drop(['attack_type'], axis=1)
    
    print(f"Training samples: {len(train_df)}, Test samples: {len(test_df)}")
    print(f"Normal: {len(train_df[train_df['label']==0])}, Attacks: {len(train_df[train_df['label']==1])}")
    
    return train_df, test_df

def encode_features(train_df, test_df):
    """Encode categorical features"""
    print("Encoding categorical features...")
    
    categorical_columns = ['protocol_type', 'service', 'flag']
    label_encoders = {}
    
    for col in categorical_columns:
        le = LabelEncoder()
        # Fit on training data
        train_df[col] = le.fit_transform(train_df[col].astype(str))
        
        # Transform test data, handle unseen labels
        test_df[col] = test_df[col].astype(str).apply(
            lambda x: le.transform([x])[0] if x in le.classes_ else -1
        )
        label_encoders[col] = le
    
    return train_df, test_df, label_encoders

def train_model(train_df, test_df):
    """Train Random Forest classifier"""
    print("Training model...")
    
    # Separate features and labels
    X_train = train_df.drop(['label', 'attack_category'], axis=1)
    y_train = train_df['label']
    
    X_test = test_df.drop(['label', 'attack_category'], axis=1)
    y_test = test_df['label']
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        random_state=42,
        n_jobs=-1,
        verbose=1
    )
    
    rf_model.fit(X_train_scaled, y_train)
    
    # Predictions
    y_pred = rf_model.predict(X_test_scaled)
    
    # Evaluation
    print("\n=== Model Evaluation ===")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Attack']))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Important Features:")
    print(feature_importance.head(10))
    
    return rf_model, scaler, X_train.columns.tolist()

def save_model(model, scaler, feature_names, label_encoders, output_dir='../data'):
    """Save trained model and preprocessing objects"""
    print(f"\nSaving model to {output_dir}...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    joblib.dump(model, f'{output_dir}/ids_model.pkl')
    joblib.dump(scaler, f'{output_dir}/scaler.pkl')
    joblib.dump(feature_names, f'{output_dir}/feature_names.pkl')
    joblib.dump(label_encoders, f'{output_dir}/label_encoders.pkl')
    
    print("Model saved successfully!")

if __name__ == "__main__":
    # File paths - Update these to your NSL-KDD dataset paths
    train_file = "../data/KDDTrain+.txt"
    test_file = "../data/KDDTest+.txt"
    
    # Check if files exist
    if not os.path.exists(train_file):
        print(f"Training file not found: {train_file}")
        print("Please download NSL-KDD dataset from: https://www.unb.ca/cic/datasets/nsl.html")
        print("Place KDDTrain+.txt and KDDTest+.txt in the data/ directory")
        exit(1)
    
    # Load and preprocess
    train_df, test_df = load_and_preprocess_data(train_file, test_file)
    
    # Encode categorical features
    train_df, test_df, label_encoders = encode_features(train_df, test_df)
    
    # Train model
    model, scaler, feature_names = train_model(train_df, test_df)
    
    # Save model
    save_model(model, scaler, feature_names, label_encoders)
    
    print("\n✓ Training completed successfully!")