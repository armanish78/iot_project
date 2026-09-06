import json
import logging
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

logger = logging.getLogger(__name__)


def evaluate_model(y_true, y_pred, y_prob=None) -> dict:
    """
    Calculate metrics for the model
    """
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
    }

    if y_prob is not None:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        except ValueError:
            pass  # Only one class present in y_true, ROC AUC not defined

    return metrics


def get_confusion_matrix(y_true, y_pred):
    """Get confusion matrix for visualization"""
    return confusion_matrix(y_true, y_pred).tolist()


def generate_evaluation_report(
    rf_metrics: dict, if_metrics: dict, hybrid_metrics: dict, output_path: str
):
    """Save evaluation report as JSON"""
    report = {"random_forest": rf_metrics, "isolation_forest": if_metrics, "hybrid_model": hybrid_metrics}

    with open(output_path, "w") as f:
        json.dump(report, f, indent=4)
    logger.info(f"Evaluation report saved to {output_path}")
