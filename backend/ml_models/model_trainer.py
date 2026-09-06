import os
import json
import numpy as np
import pickle
import logging
from pathlib import Path
from backend.ml_models.random_forest_model import (
    train_random_forest_with_gridsearch,
    predict_with_rf,
)
from backend.ml_models.isolation_forest_model import (
    tune_isolation_forest,
    predict_anomalies,
)
from backend.ml_models.model_evaluator import (
    evaluate_model,
    generate_evaluation_report,
)
from backend.ml_models.shap_explainer import create_shap_explainer
from backend.ml_models.hybrid_pipeline import hybrid_predict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PROCESSED_DIR = Path("data/processed")
MODELS_DIR = Path("backend/models")
PREDICTIONS_DIR = Path("backend/predictions")


def load_processed_data() -> tuple:
    """Load Part 1 outputs"""
    logger.info(f"Loading datasets from {PROCESSED_DIR}...")
    X_train = np.load(PROCESSED_DIR / "X_train.npy", allow_pickle=True).astype(
        np.float32
    )
    y_train = np.load(PROCESSED_DIR / "y_train.npy", allow_pickle=True).astype(
        int
    )
    X_val = np.load(PROCESSED_DIR / "X_val.npy", allow_pickle=True).astype(
        np.float32
    )
    y_val = np.load(PROCESSED_DIR / "y_val.npy", allow_pickle=True).astype(int)
    X_test = np.load(PROCESSED_DIR / "X_test.npy", allow_pickle=True).astype(
        np.float32
    )
    y_test = np.load(PROCESSED_DIR / "y_test.npy", allow_pickle=True).astype(
        int
    )
    X_train_normal = np.load(
        PROCESSED_DIR / "X_train_normal.npy", allow_pickle=True
    ).astype(np.float32)
    X_test_if = np.load(
        PROCESSED_DIR / "X_test_if.npy", allow_pickle=True
    ).astype(np.float32)
    y_test_if = np.load(
        PROCESSED_DIR / "y_test_if.npy", allow_pickle=True
    ).astype(int)

    with open(PROCESSED_DIR / "feature_names.json", "r") as f:
        feature_names = json.load(f)

    logger.info(f"Loaded X_test_if: {X_test_if.shape}")
    return (
        X_train,
        y_train,
        X_val,
        y_val,
        X_test,
        y_test,
        X_train_normal,
        X_test_if,
        y_test_if,
        feature_names,
    )


def save_models(rf_model, if_model, feature_names, top_indices, if_threshold=0.0):
    """Save trained models as .pkl files"""
    os.makedirs(MODELS_DIR, exist_ok=True)

    with open(MODELS_DIR / "random_forest_model.pkl", "wb") as f:
        pickle.dump(rf_model, f)

    with open(MODELS_DIR / "isolation_forest_model.pkl", "wb") as f:
        pickle.dump(if_model, f)

    with open(MODELS_DIR / "feature_names.json", "w") as f:
        json.dump(
            {
                "features": feature_names,
                "num_features": len(feature_names),
                "if_top_indices": top_indices.tolist() if top_indices is not None else [],
                "if_threshold": float(if_threshold),
                "model_version": "1.0",
            },
            f,
            indent=4,
        )

    # Scaler is now correctly created in Part 1 and saved to PROCESSED_DIR
    if os.path.exists(PROCESSED_DIR / "scaler.pkl"):
        import shutil
        shutil.copy2(PROCESSED_DIR / "scaler.pkl", MODELS_DIR / "scaler.pkl")

    logger.info(f"Saved models to {MODELS_DIR}")


def train_and_evaluate():
    """Main training orchestrator"""
    # 1. Load Data
    (
        X_train,
        y_train,
        X_val,
        y_val,
        X_test,
        y_test,
        X_train_normal,
        X_test_if,
        y_test_if,
        feature_names,
    ) = load_processed_data()

    # 2. Train Models using GridSearchCV and Custom Tuning
    logger.info("Initiating Hyperparameter Tuning Phase...")
    rf = train_random_forest_with_gridsearch(X_train, y_train)

    # Feature Selection for IF: Solve the curse of dimensionality
    importances = rf.feature_importances_
    # Get top 15 most important features
    top_indices = np.argsort(importances)[::-1][:15]
    logger.info(f"Selected Top 15 features for IF: {[feature_names[i] for i in top_indices]}")
    
    # Subset the datasets for IF
    X_train_normal_if = X_train_normal[:, top_indices]
    X_val_if = X_val[:, top_indices]
    X_test_if_sub = X_test_if[:, top_indices]

    if_model, best_thresh = tune_isolation_forest(X_train_normal_if, X_val_if, y_val)

    # 3. Save Models
    save_models(rf, if_model, feature_names, top_indices, best_thresh)

    # 4. Evaluate Models
    logger.info("Evaluating models on test data...")
    rf_preds, rf_probs = predict_with_rf(rf, X_test)
    rf_metrics = evaluate_model(y_test, rf_preds, rf_probs)

    # Use decision_function and best_thresh instead of predict()
    if_scores = if_model.decision_function(X_test_if_sub)
    if_preds_binary = (if_scores < best_thresh).astype(int)
    if_metrics = evaluate_model(y_test_if, if_preds_binary)

    # Evaluate Hybrid Model on Full Test Set
    if_scores_full = if_model.decision_function(X_test[:, top_indices])
    if_preds_full = (if_scores_full < best_thresh).astype(int)
    
    hybrid_preds = np.zeros_like(rf_preds)
    for i in range(len(y_test)):
        rf_conf = rf_probs[i]
        if rf_conf >= 0.70 or rf_conf <= 0.50:
            hybrid_preds[i] = rf_preds[i]
        else:
            hybrid_preds[i] = if_preds_full[i]
            
    hybrid_metrics = evaluate_model(y_test, hybrid_preds)
    
    # Store confusion matrices
    from backend.ml_models.model_evaluator import get_confusion_matrix
    rf_metrics['confusion_matrix'] = get_confusion_matrix(y_test, rf_preds)
    if_metrics['confusion_matrix'] = get_confusion_matrix(y_test_if, if_preds_binary)
    hybrid_metrics['confusion_matrix'] = get_confusion_matrix(y_test, hybrid_preds)

    os.makedirs(PREDICTIONS_DIR, exist_ok=True)
    report_path = PREDICTIONS_DIR / "evaluation_report.json"
    generate_evaluation_report(rf_metrics, if_metrics, hybrid_metrics, report_path)

    # 5. SHAP and Sample Predictions
    logger.info("Generating SHAP explainer and sample predictions...")
    explainer = create_shap_explainer(rf, X_train)

    sample_predictions = {"predictions": []}

    # Generate 5 sample predictions for testing
    for i in range(5):
        sample = X_test[i].reshape(1, -1)
        # Use hybrid pipeline
        pred_result = hybrid_predict(
            rf, if_model, explainer, sample, feature_names, top_indices, best_thresh
        )

        pred_result["sample_id"] = i
        # Numpy arrays aren't JSON serializable easily, so we omit features dict
        sample_predictions["predictions"].append(pred_result)

    with open(PREDICTIONS_DIR / "predictions.json", "w") as f:
        json.dump(sample_predictions, f, indent=4)

    logger.info("Sample predictions saved successfully.")
    logger.info("Part 2 Training Pipeline Completed!")
