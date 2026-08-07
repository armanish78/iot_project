import logging

logger = logging.getLogger(__name__)


def ensemble_voting(rf_pred: int, if_pred: int, rf_confidence: float) -> tuple:
    """
    Decision logic
    RF: 0 (normal), 1 (attack)
    IF: 1 (normal), -1 (anomaly)

    Returns: (final_prediction, confidence, threat_type)
    final_prediction: True (threat) / False (normal)
    """

    if rf_pred == 1 and if_pred == -1:
        # Both models detect an issue
        return True, float(max(0.95, rf_confidence)), "known_attack"

    elif rf_pred == 0 and if_pred == 1:
        # Both models say normal
        return False, float(max(0.95, 1 - rf_confidence)), "normal"

    elif rf_pred == 1 and if_pred == 1:
        # RF detects known attack, IF doesn't see anomaly (could be a standard attack)
        return True, float(rf_confidence), "known_attack"

    elif rf_pred == 0 and if_pred == -1:
        # RF says normal, IF detects anomaly -> Zero-Day!
        return True, 0.85, "zero_day"

    return False, 0.5, "unknown"


def hybrid_predict(
    rf_model, if_model, shap_explainer, X_sample, feature_names
) -> dict:
    """
    Make prediction using both models
    """
    from backend.ml_models.shap_explainer import get_feature_importance

    # 1. Get RF prediction
    rf_pred = int(rf_model.predict(X_sample)[0])
    rf_conf = float(rf_model.predict_proba(X_sample)[0, 1])

    # 2. Get IF prediction
    if_pred = int(if_model.predict(X_sample)[0])

    # 3. Decision logic
    is_threat, confidence, threat_type = ensemble_voting(
        rf_pred, if_pred, rf_conf
    )

    # 4. Explainability
    # For zero-days, SHAP might not be as reliable since RF didn't detect it, but we still generate it
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
    }
