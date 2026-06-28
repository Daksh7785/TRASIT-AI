import numpy as np
import pandas as pd
from tqdm import tqdm
from transit_ai.data_loader import generate_synthetic_lightcurve
from transit_ai.preprocessing import preprocess_pipeline
from transit_ai.detector import run_bls_search
from transit_ai.classifier import TransitClassifier
import os

def generate_and_train(model_path="transit_ai/model.joblib", samples_per_class=50):
    print(f"Generating synthetic training dataset ({samples_per_class} samples per class)...")
    
    classes = ['transit', 'eclipse', 'blend', 'noise']
    features_list = []
    labels_list = []
    
    # Random seed for reproducibility
    np.random.seed(42)
    
    for cls in classes:
        print(f"Processing class: {cls}")
        for i in tqdm(range(samples_per_class)):
            # Randomize parameters slightly to make classifier robust
            period = np.random.uniform(1.5, 6.0)
            depth = np.random.uniform(0.005, 0.02)
            duration = np.random.uniform(0.08, 0.25)
            noise_level = np.random.uniform(0.0008, 0.002)
            
            # Generate
            lc = generate_synthetic_lightcurve(
                label=cls,
                length=1500,
                noise_level=noise_level,
                period=period,
                depth=depth,
                duration=duration
            )
            
            # Preprocess
            prep = preprocess_pipeline(lc)
            
            # Detect using BLS
            try:
                _, best_params = run_bls_search(
                    prep['clean_time'], 
                    prep['clean_flux'], 
                    prep['clean_err'],
                    min_period=1.0,
                    max_period=8.0
                )
                
                # Extract features
                classifier_temp = TransitClassifier()
                features = classifier_temp.extract_features(
                    prep['clean_time'], 
                    prep['clean_flux'], 
                    best_params
                )
                
                features_list.append(features)
                labels_list.append(cls)
            except Exception as e:
                # If BLS fails (e.g. all points clipped), skip
                continue
                
    # Train
    print("Training Random Forest Classifier...")
    df_features = pd.DataFrame(features_list)
    
    # Fill any NaNs just in case
    df_features.fillna(0, inplace=True)
    
    # Save the feature names to check ordering later
    joblib_dir = os.path.dirname(model_path)
    if joblib_dir and not os.path.exists(joblib_dir):
        os.makedirs(joblib_dir, exist_ok=True)
        
    classifier = TransitClassifier(model_path=model_path)
    classifier.train(df_features, labels_list)
    
    # Compute accuracy on training set as quick check
    predictions = classifier.model.predict(df_features)
    accuracy = np.mean(predictions == np.array(labels_list))
    print(f"Training accuracy: {accuracy * 100:.2f}%")
    print(f"Model successfully saved to {model_path}")
    
    # Save feature names list
    feature_cols_path = model_path.replace(".joblib", "_features.txt")
    with open(feature_cols_path, "w") as f:
        f.write("\n".join(df_features.columns.tolist()))

if __name__ == "__main__":
    generate_and_train()
