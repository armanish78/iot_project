import logging
from sklearn.ensemble import IsolationForest
import numpy as np
from sklearn.metrics import f1_score

logger = logging.getLogger(__name__)


def create_isolation_forest(
    contamination: float = 0.01, random_state: int = 42
) -> IsolationForest:
    """Create Isolation Forest for anomaly detection"""
    logger.info(f"Creating IsolationForest (contamination={contamination})")
    return IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=150,
        n_jobs=-1,
    )


def train_isolation_forest(X_train, model: IsolationForest) -> IsolationForest:
    """Train on data (no labels needed)"""
    logger.info(f"Training Isolation Forest on {len(X_train)} samples...")
    model.fit(X_train)
    logger.info("Isolation Forest training complete.")
    return model


def tune_isolation_forest(X_train_normal, X_val, y_val) -> tuple:
    """Custom Grid Search for Isolation Forest.
    Trains strictly on normal data, but uses the validation set to find the best configuration
    and optimal decision threshold based on a 5% zero-day anomaly prevalence.
    Returns: (best_model, best_threshold)
    """
    best_f1 = -1
    best_model = None
    best_thresh = 0
    best_params = {}

    n_estimators_list = [200]
    max_samples_list = [1.0]
    max_features_list = [0.5]
    
    # Subsample validation set to 5% anomalies to mimic X_test_if test environment
    X_val_normal = X_val[y_val == 0]
    y_val_normal = y_val[y_val == 0]
    X_val_attack = X_val[y_val == 1]
    y_val_attack = y_val[y_val == 1]
    
    attack_target_count = int(len(X_val_normal) * 0.05 / 0.95)
    
    # Randomly select the required number of attacks
    np.random.seed(42)
    attack_indices = np.random.choice(len(X_val_attack), min(attack_target_count, len(X_val_attack)), replace=False)
    X_val_attack_sampled = X_val_attack[attack_indices]
    y_val_attack_sampled = y_val_attack[attack_indices]
    
    X_val_sub = np.vstack([X_val_normal, X_val_attack_sampled])
    y_val_sub = np.concatenate([y_val_normal, y_val_attack_sampled])

    logger.info("Starting custom Grid Search for Isolation Forest with Threshold Tuning...")

    for n in n_estimators_list:
        for ms in max_samples_list:
            for mf in max_features_list:
                # We use a dummy contamination for fitting because we rely on decision_function
                model = IsolationForest(
                    contamination=0.05, 
                    n_estimators=n, 
                    max_samples=ms,
                    max_features=mf,
                    random_state=42, 
                    n_jobs=-1
                )
                model.fit(X_train_normal)

                # Evaluate on 5% anomaly validation set
                scores = model.decision_function(X_val_sub)
                
                # Tune threshold
                thresholds = np.linspace(np.min(scores), np.max(scores), 100)
                for t in thresholds:
                    # IF outputs negative scores for anomalies. We predict 1 (attack) if score < threshold
                    preds_binary = (scores < t).astype(int)
                    score = f1_score(y_val_sub, preds_binary, zero_division=0)
                    
                    if score > best_f1:
                        best_f1 = score
                        best_model = model
                        best_thresh = float(t)
                        best_params = {"n_estimators": n, "max_samples": ms, "max_features": mf, "threshold": best_thresh}
                
                logger.info(f"Tested params: n_estimators={n}, max_samples={ms}, max_features={mf}. Best F1 so far: {best_f1:.4f}")

    logger.info(
        f"Isolation Forest Final Best Params: {best_params} (Val F1: {best_f1:.4f})"
    )
    return best_model, best_thresh


def predict_anomalies(model: IsolationForest, X_test):
    """
    Detect anomalies
    Returns: (predictions, anomaly_scores)
    predictions: -1 (anomaly), 1 (normal)
    anomaly_scores: lower score = more anomalous (negative values are anomalies)
    """
    preds = model.predict(X_test)
    scores = model.decision_function(X_test)
    return preds, scores
