import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV

logger = logging.getLogger(__name__)


def create_random_forest(
    n_estimators: int = 150, max_depth: int = 30, random_state: int = 42
) -> RandomForestClassifier:
    """Create Random Forest model"""
    logger.info(
        f"Creating RandomForestClassifier (n_estimators={n_estimators}, max_depth={max_depth})"
    )
    return RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=-1,
    )


def train_random_forest(
    X_train, y_train, model: RandomForestClassifier
) -> RandomForestClassifier:
    """Train Random Forest on labeled data"""
    logger.info(f"Training Random Forest on {len(X_train)} samples...")
    model.fit(X_train, y_train)
    logger.info("Random Forest training complete.")
    return model


def train_random_forest_with_gridsearch(
    X_train, y_train
) -> RandomForestClassifier:
    """Hyperparameter tuning using GridSearchCV"""
    rf = RandomForestClassifier(random_state=42, n_jobs=-1)

    # We define a grid of parameters to test (Restricted to force Regularization)
    param_grid = {"n_estimators": [50, 100, 150], "max_depth": [3, 5, 7]}

    logger.info(
        f"Starting GridSearchCV for Random Forest on {len(X_train)} samples..."
    )
    # cv=3 for 3-fold cross validation. n_jobs=1 on gridsearch since n_jobs=-1 is on the estimator (RAM safety)
    grid_search = GridSearchCV(
        estimator=rf,
        param_grid=param_grid,
        cv=3,
        scoring="f1",
        n_jobs=1,
        verbose=1,
    )
    grid_search.fit(X_train, y_train)

    logger.info(f"Random Forest Best Params found: {grid_search.best_params_}")
    return grid_search.best_estimator_


def predict_with_rf(model: RandomForestClassifier, X_test):
    """
    Make predictions with confidence scores
    Returns: (predictions, confidence_scores)
    """
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[
        :, 1
    ]  # Probability of class 1 (attack)
    return preds, probs


def get_feature_importance(
    model: RandomForestClassifier, feature_names: list
) -> dict:
    """Get which features are most important for decisions"""
    importances = model.feature_importances_
    # Sort features by importance
    indices = importances.argsort()[::-1]

    important_features = {}
    for i in range(len(feature_names)):
        important_features[feature_names[indices[i]]] = float(
            importances[indices[i]]
        )

    return important_features
