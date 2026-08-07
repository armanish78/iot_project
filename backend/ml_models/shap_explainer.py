import shap
import logging

logger = logging.getLogger(__name__)


def create_shap_explainer(model, X_train):
    """Create SHAP explainer for Random Forest model"""
    logger.info("Creating SHAP TreeExplainer...")
    # Use a small background dataset if X_train is too large
    if len(X_train) > 1000:
        shap.sample(X_train, 100)

    explainer = shap.TreeExplainer(model)
    return explainer


def get_feature_importance(
    explainer,
    X_sample,
    feature_names: list,
    prediction: int,
    confidence: float,
) -> dict:
    """Get SHAP values for a specific sample"""
    # X_sample should be 2D
    if len(X_sample.shape) == 1:
        X_sample = X_sample.reshape(1, -1)

    shap_values = explainer.shap_values(X_sample)

    # Random Forest shap_values is a list of arrays (one for each class)
    # We want the explanation for class 1 (attack)
    if isinstance(shap_values, list):
        attack_shap_values = shap_values[1][0]
    else:
        # In newer shap versions, it might be a single array or Explanation object
        if len(shap_values.shape) == 3:
            attack_shap_values = shap_values[0, :, 1]
        else:
            attack_shap_values = shap_values[0]

    # Combine feature names with their absolute SHAP values to find top contributors
    feature_contributions = []
    for i, name in enumerate(feature_names):
        feature_contributions.append(
            {"feature": name, "contribution": float(attack_shap_values[i])}
        )

    # Sort by absolute contribution (highest impact first)
    feature_contributions.sort(
        key=lambda x: abs(x["contribution"]), reverse=True
    )
    top_features = feature_contributions[:3]

    predicted_class = "attack" if prediction == 1 else "normal"

    # Generate human readable explanation
    explanation = f"Connection flagged as {predicted_class.upper()} with {confidence*100:.1f}% confidence because: "
    reasons = []
    for f in top_features:
        impact = "increased" if f["contribution"] > 0 else "decreased"
        reasons.append(f"{f['feature']} ({impact} threat score)")

    explanation += ", ".join(reasons)

    return {
        "predicted_class": predicted_class,
        "confidence": float(confidence),
        "top_contributing_features": top_features,
        "explanation": explanation,
    }


def generate_explanation(shap_values, feature_names: list, instance) -> str:
    """Generate human-readable explanation (simplified)"""
    pass  # logic is embedded in get_feature_importance for simplicity
