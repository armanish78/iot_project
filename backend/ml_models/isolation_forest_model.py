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


def tune_isolation_forest(X_train_normal, X_val, y_val) -> IsolationForest:
    """Custom Grid Search for Isolation Forest.
    Trains strictly on normal data, but uses the validation set to find the best contamination rate.
    """
    best_f1 = -1
    best_model = None
    best_params = {}

    # Significantly expanded grid to target >85% precision/recall
    contaminations = [0.01, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4]
    n_estimators_list = [100, 200]
    max_samples_list = ['auto', 256, 512, 1024]
    max_features_list = [1.0, 0.8, 0.5]

    logger.info("Starting custom Grid Search for Isolation Forest...")

    for c in contaminations:
        for n in n_estimators_list:
            for ms in max_samples_list:
                for mf in max_features_list:
                    # Skip some combinations to save time if needed, but we want the best score
                    model = IsolationForest(
                        contamination=c, 
                        n_estimators=n, 
                        max_samples=ms,
                        max_features=mf,
                        random_state=42, 
                        n_jobs=-1
                    )
                    model.fit(X_train_normal)  # Train purely on normal traffic

                    # Evaluate on validation set
                    preds = model.predict(X_val)
                    # IF output: -1 (anomaly/attack), 1 (normal). Convert to 1 (attack), 0 (normal)
                    preds_binary = np.where(preds == -1, 1, 0)

                    score = f1_score(y_val, preds_binary, zero_division=0)

                    if score > best_f1:
                        best_f1 = score
                        best_model = model
                        best_params = {"contamination": c, "n_estimators": n, "max_samples": ms, "max_features": mf}
                        logger.info(f"New Best IF Params found: {best_params} (Val F1: {best_f1:.4f})")

    logger.info(
        f"Isolation Forest Final Best Params: {best_params} (Val F1: {best_f1:.4f})"
    )
    return best_model


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
