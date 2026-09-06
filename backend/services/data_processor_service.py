import numpy as np

class DataProcessorService:
    def __init__(self):
        # List of 167 features expected by the model
        # Normally this would be loaded from a config or extracted from training column names
        # For this prototype, we'll assume the incoming data dict has these exact features
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
        
        # If we have a scaler, use its mean as the background "normal" packet fill. Otherwise use 0.
        if scaler and hasattr(scaler, 'mean_'):
            feature_array = np.array([scaler.mean_])
        else:
            feature_array = np.zeros((1, 187))
        
        feature_names_path = os.path.join(os.path.dirname(Config.RANDOM_FOREST_MODEL), "feature_names.json")
        try:
            with open(feature_names_path, 'r') as f:
                feature_names = json.load(f)["features"]
                
            # Map the incoming data to the correct index in the 187 length array
            for k, v in data.items():
                if k in feature_names and isinstance(v, (int, float)):
                    idx = feature_names.index(k)
                    feature_array[0, idx] = v
                    
        except Exception as e:
            # Fallback if json not found
            pass
        
        # Scale
        if scaler:
            try:
                scaled_features = scaler.transform(feature_array)
                return scaled_features
            except Exception:
                # Fallback if scaler fails
                return feature_array
                
        return feature_array

processor_service = DataProcessorService()
