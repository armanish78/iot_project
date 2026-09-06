import logging
from backend.ml_models.shap_explainer import get_feature_importance

logger = logging.getLogger(__name__)


def ensemble_voting(rf_pred: int, if_pred: int, rf_confidence: float) -> tuple:
    """
    Decision logic with RF Uncertainty Override.
    RF: 0 (normal), 1 (attack)
    IF: 1 (normal), -1 (anomaly)

    Returns: (final_prediction, confidence, threat_type)
    """
    if rf_confidence >= 0.70 or rf_confidence <= 0.50:
        # Trust RF
        final_prediction = (rf_pred == 1)
        threat_type = "known_attack" if final_prediction else "normal"
        confidence = float(max(0.70, rf_confidence))
        return final_prediction, confidence, threat_type
    else:
        # RF is uncertain, IF overrides
        final_prediction = (if_pred == -1)
        threat_type = "zero_day" if final_prediction else "normal"
        confidence = 0.85
        return final_prediction, confidence, threat_type


def hybrid_predict(
    rf_model, if_model, shap_explainer, X_sample, feature_names, if_top_indices=None, if_threshold=0.0
) -> dict:
    """
    Make prediction using both models
    """
    # 1. Get RF prediction
    rf_pred = int(rf_model.predict(X_sample)[0])
    rf_conf = float(rf_model.predict_proba(X_sample)[0, 1])

    # 2. Get IF prediction
    if if_top_indices is not None:
        X_sample_if = X_sample[:, if_top_indices]
    else:
        X_sample_if = X_sample

    score = if_model.decision_function(X_sample_if)[0]
    if_pred = -1 if score < if_threshold else 1

    # 3. Decision logic
    is_threat, confidence, threat_type = ensemble_voting(
        rf_pred, if_pred, rf_conf
    )

    # 4. Explainability
    explanation_dict = get_feature_importance(
        shap_explainer, X_sample, feature_names, rf_pred, rf_conf
    )

    return {
        "threat": is_threat,
        "confidence": confidence,
        "threat_type": threat_type,
        "rf_prediction": rf_pred,
        "if_prediction": if_pred,
        "explanation": explanation_dict["explanation"],
        "top_features": explanation_dict["top_contributing_features"]
    }
