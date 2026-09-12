import numpy as np

class DataProcessorService:
    def __init__(self):
        # List of 187 features expected by the offline/reference model
        # Loaded from feature_names.json at prediction time
        pass
        
    def preprocess_input(self, data: dict, scaler) -> np.ndarray:
        """
        Normalize incoming data using saved scaler.
        Extract mathematical features, drop IPs, etc.
        """
        # Load the feature names to map the packet correctly
        import json
        import os
        from backend.flask_api.config import Config
        import logging
        
        logger = logging.getLogger(__name__)
        
        # We know the canonical feature dimension is 187
        feature_array = np.zeros((1, 187))
        
        feature_names_path = os.path.join(os.path.dirname(Config.RANDOM_FOREST_MODEL), "feature_names.json")
        try:
            with open(feature_names_path, 'r') as f:
                feature_names = json.load(f)["features"]
        except Exception as e:
            raise RuntimeError(f"Could not load feature_names.json: {e}")
            
        # Fill the first 162 elements with scaler.mean_ if available as a baseline for missing numeric data
        if scaler and hasattr(scaler, 'mean_') and len(scaler.mean_) == 162:
            feature_array[0, :162] = scaler.mean_
                
        # Map the incoming data to the correct index in the 187 length array
        for k, v in data.items():
            if k in feature_names and isinstance(v, (int, float)):
                idx = feature_names.index(k)
                feature_array[0, idx] = v
                
        # The trained model contract: 162 numeric features + 25 categorical features
        NUMERIC_COUNT = 162
        
        if scaler:
            numeric_features = feature_array[:, :NUMERIC_COUNT]
            categorical_features = feature_array[:, NUMERIC_COUNT:]
            
            # This MUST fail loudly if dimensions are wrong
            if numeric_features.shape[1] != scaler.n_features_in_:
                raise ValueError(f"Scaler expects {scaler.n_features_in_} features but received {numeric_features.shape[1]}. Numeric feature extraction/mapping failed.")
                
            scaled_numeric = scaler.transform(numeric_features)
            
            final_features = np.hstack((scaled_numeric, categorical_features))
            
            log_str = f"[PREPROCESSING] Input features: 187 | Numeric features: {numeric_features.shape[1]} | Categorical features: {categorical_features.shape[1]} | Scaled numeric features: {scaled_numeric.shape[1]} | Final model features: {final_features.shape[1]} | Scaler validation: PASS"
            logger.info(log_str)
            print(log_str)
            
            return final_features
            
        return feature_array

processor_service = DataProcessorService()
