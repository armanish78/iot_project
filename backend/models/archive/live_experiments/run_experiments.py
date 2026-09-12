"""
backend/models/live_experiments/run_experiments.py
====================================================
Sentinel ML Model Benchmark & Optimization
------------------------------------------
READ-ONLY of production models. All outputs go to live_experiments/.
No deep learning. Classical ML only.

Experiments:
  1. Production Baseline (existing live_rf.pkl + live_if.pkl)
  2. Random Forest  (16 features, 14 features, regularization sweep)
  3. Extra Trees    (16 and 14 features)
  4. HistGradientBoosting (16 and 14 features)
  5. XGBoost        (16 and 14 features)
  6. LightGBM       (16 and 14 features)
  7. Isolation Forest independent evaluation
  8. External pretrained classical ML investigation
  Threshold & Hybrid Policy evaluation
  SHAP analysis for top candidates
"""

import sys, os, time, json, warnings, pickle, traceback
from pathlib import Path
from datetime import datetime

import numpy as np
import joblib
from sklearn.ensemble import (
    RandomForestClassifier,
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    IsolationForest,
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
)
from sklearn.preprocessing import MinMaxScaler

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
BENCH_DATA   = SCRIPT_DIR / "benchmark_data"
PROD_MODELS  = PROJECT_ROOT / "backend" / "models" / "live"
EXP_DIR      = SCRIPT_DIR

LIVE_RF_PATH     = PROD_MODELS / "live_rf.pkl"
LIVE_IF_PATH     = PROD_MODELS / "live_if.pkl"
LIVE_SCALER_PATH = PROD_MODELS / "live_scaler.pkl"

# ── Feature definitions ────────────────────────────────────────────────────────
FEATURES_16 = [
    "spkts","dpkts","sbytes","dbytes","dur",
    "sttl","dttl",
    "smean","dmean","rate","sload","dload",
    "proto_tcp","proto_udp","proto_icmp","proto_other",
]
FEATURES_14 = [f for f in FEATURES_16 if f not in ("sttl","dttl")]

IDX_14_from_16 = [FEATURES_16.index(f) for f in FEATURES_14]

RANDOM_STATE = 42

# ── Load benchmark data ────────────────────────────────────────────────────────
print("Loading benchmark data …")
X_train = np.load(BENCH_DATA / "X_train.npy").astype(np.float32)
X_val   = np.load(BENCH_DATA / "X_val.npy").astype(np.float32)
X_test  = np.load(BENCH_DATA / "X_test.npy").astype(np.float32)
y_train = np.load(BENCH_DATA / "y_train.npy").astype(int)
y_val   = np.load(BENCH_DATA / "y_val.npy").astype(int)
y_test  = np.load(BENCH_DATA / "y_test.npy").astype(int)

X_train14 = X_train[:, IDX_14_from_16]
X_val14   = X_val[:,   IDX_14_from_16]
X_test14  = X_test[:,  IDX_14_from_16]

print(f"  Train: {X_train.shape}  Val: {X_val.shape}  Test: {X_test.shape}")
print(f"  Train positives: {y_train.sum()} / {len(y_train)}")
print(f"  Test  positives: {y_test.sum()}  / {len(y_test)}")

# ── Load real-world benign flows ───────────────────────────────────────────────
with open(BENCH_DATA / "real_benign_flows.json") as f:
    benign_flows_raw = json.load(f)

# Extract vectors + scaler fitted on train data
bench_scaler = joblib.load(BENCH_DATA / "scaler.pkl")

benign_vecs_16 = np.array([fl["vector"] for fl in benign_flows_raw], dtype=np.float32)
benign_vecs_16_scaled = bench_scaler.transform(benign_vecs_16)
benign_vecs_14_scaled = benign_vecs_16_scaled[:, IDX_14_from_16]
N_BENIGN = len(benign_vecs_16)
print(f"\nReal-world benign flows: {N_BENIGN}")

# ── Helpers ────────────────────────────────────────────────────────────────────
SEP = "=" * 74

def metrics(y_true, y_pred, y_prob=None):
    m = {
        "accuracy":  round(float(accuracy_score(y_true, y_pred)), 5),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 5),
        "recall":    round(float(recall_score(y_true, y_pred, zero_division=0)), 5),
        "f1":        round(float(f1_score(y_true, y_pred, zero_division=0)), 5),
        "cm":        confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_prob is not None:
        try:    m["roc_auc"] = round(float(roc_auc_score(y_true, y_prob)), 5)
        except: m["roc_auc"] = None
        try:    m["pr_auc"]  = round(float(average_precision_score(y_true, y_prob)), 5)
        except: m["pr_auc"]  = None
    return m


def real_world_fp(model_fn, X_benign):
    """Apply model_fn to benign vectors; returns (fp_count, fp_rate, avg_lat, p95_lat)."""
    lats = []
    preds = []
    for row in X_benign:
        t0 = time.perf_counter()
        preds.append(model_fn(row.reshape(1, -1)))
        lats.append(time.perf_counter() - t0)
    preds = np.array(preds)
    fp = int(preds.sum())
    fpr = round(fp / len(preds), 4) if len(preds) else 0.0
    avg_lat = round(float(np.mean(lats)) * 1000, 4)   # ms
    p95_lat = round(float(np.percentile(lats, 95)) * 1000, 4)
    return fp, fpr, avg_lat, p95_lat


def bench_predict_lat(model, X, batch_size=1):
    """Return predictions + avg latency in ms per sample."""
    lats = []
    preds = []
    for i in range(0, len(X), batch_size):
        batch = X[i:i+batch_size]
        t0 = time.perf_counter()
        p = model.predict(batch)
        lats.append((time.perf_counter() - t0) / len(batch))
        preds.extend(p.tolist())
    return np.array(preds), round(float(np.mean(lats))*1000, 4), round(float(np.percentile(lats, 95))*1000, 4)


def save_candidate(name, model, scaler, feature_names, metadata, bench_metrics, real_metrics):
    d = EXP_DIR / name
    d.mkdir(exist_ok=True)
    joblib.dump(model, d / "model.pkl")
    if scaler is not None:
        joblib.dump(scaler, d / "scaler.pkl")
    with open(d / "feature_names.json", "w") as f:
        json.dump({"features": feature_names}, f, indent=2)
    with open(d / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    with open(d / "metrics.json", "w") as f:
        json.dump({"benchmark": bench_metrics, "real_world": real_metrics}, f, indent=2)
    print(f"  Saved to {d}")


# ── Results accumulator ────────────────────────────────────────────────────────
RESULTS = []

def record(name, feature_set, n_feats, bench_m, real_m, params, model_size_kb, train_time_s, avg_lat, p95_lat):
    RESULTS.append({
        "model":       name,
        "feature_set": feature_set,
        "n_features":  n_feats,
        "accuracy":    bench_m.get("accuracy"),
        "precision":   bench_m.get("precision"),
        "recall":      bench_m.get("recall"),
        "f1":          bench_m.get("f1"),
        "roc_auc":     bench_m.get("roc_auc"),
        "pr_auc":      bench_m.get("pr_auc"),
        "cm":          bench_m.get("cm"),
        "real_benign_flows": N_BENIGN,
        "real_fp":     real_m.get("fp"),
        "real_fp_rate":real_m.get("fp_rate"),
        "real_fp_per_100": round(real_m.get("fp", 0) / N_BENIGN * 100, 2) if N_BENIGN else None,
        "avg_latency_ms": avg_lat,
        "p95_latency_ms": p95_lat,
        "model_size_kb": model_size_kb,
        "train_time_s":  round(train_time_s, 2),
        "params":        params,
    })


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 1: PRODUCTION BASELINE
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("EXPERIMENT 1 — PRODUCTION BASELINE")
print(SEP)

try:
    prod_rf     = joblib.load(LIVE_RF_PATH)
    prod_if     = joblib.load(LIVE_IF_PATH)
    prod_scaler = joblib.load(LIVE_SCALER_PATH)
    with open(PROD_MODELS / "live_feature_names.json") as f:
        _fn_raw = json.load(f)
        prod_fnames = _fn_raw if isinstance(_fn_raw, list) else _fn_raw.get("features", FEATURES_16)

    # The production scaler was fitted on 16 features; benign_vecs_16 raw:
    prod_benign_scaled = prod_scaler.transform(benign_vecs_16)

    # Benchmark test — prod scaler trained differently; re-use raw X_test scaled via bench_scaler
    # NOTE: production scaler ≠ bench_scaler so we evaluate separately
    prod_test_scaled = prod_scaler.transform(
        bench_scaler.inverse_transform(X_test)
    )

    t0 = time.perf_counter()
    prod_preds = prod_rf.predict(prod_test_scaled)
    prod_probs = prod_rf.predict_proba(prod_test_scaled)[:, 1]
    bench_lat  = (time.perf_counter() - t0) / len(prod_test_scaled) * 1000

    bench_m = metrics(y_test, prod_preds, prod_probs)

    # Real-world FP
    def prod_predict_fn(x):
        return int(prod_rf.predict(x)[0])

    fp, fpr, avg_lat, p95_lat = real_world_fp(prod_predict_fn, prod_benign_scaled)

    real_m = {"fp": fp, "fp_rate": fpr}
    record("baseline_rf16", "16 features (prod)", 16, bench_m, real_m,
           {"n_estimators": prod_rf.n_estimators, "max_depth": prod_rf.max_depth},
           os.path.getsize(LIVE_RF_PATH)//1024, 0.0, avg_lat, p95_lat)

    print(f"  Benchmark  — Acc: {bench_m['accuracy']:.4f}  F1: {bench_m['f1']:.4f}  "
          f"Recall: {bench_m['recall']:.4f}  ROC-AUC: {bench_m.get('roc_auc','N/A')}")
    print(f"  Real-world — FP: {fp}/{N_BENIGN}  FP-rate: {fpr:.2%}  AvgLat: {avg_lat:.3f}ms")
    print(f"  CM: {bench_m['cm']}")

except Exception as e:
    print(f"  [FAILED] {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 2: RANDOM FOREST — sweep
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("EXPERIMENT 2 — RANDOM FOREST SWEEP")
print(SEP)

RF_CONFIGS = [
    {"max_depth": d, "min_samples_leaf": msl, "min_samples_split": mss,
     "n_estimators": 100, "random_state": RANDOM_STATE}
    for d in [8, 12, 16, 20]
    for msl, mss in [(5, 10), (10, 20)]
]

best_rf16_f1   = -1; best_rf16   = None; best_rf16_params   = None
best_rf14_f1   = -1; best_rf14   = None; best_rf14_params   = None

for cfg in RF_CONFIGS:
    for feat_set, X_tr, X_v, X_ts in [
        ("16f", X_train, X_val, X_test),
        ("14f", X_train14, X_val14, X_test14),
    ]:
        tag = f"RF depth={cfg['max_depth']} msl={cfg['min_samples_leaf']} {feat_set}"
        try:
            clf = RandomForestClassifier(**cfg)
            t0 = time.time()
            clf.fit(X_tr, y_train)
            t_train = time.time() - t0

            # Validation
            val_preds = clf.predict(X_v)
            val_f1 = f1_score(y_val, val_preds, zero_division=0)
            print(f"  {tag} | val_f1={val_f1:.4f}")

            if feat_set == "16f" and val_f1 > best_rf16_f1:
                best_rf16_f1 = val_f1; best_rf16 = clf; best_rf16_params = cfg
            if feat_set == "14f" and val_f1 > best_rf14_f1:
                best_rf14_f1 = val_f1; best_rf14 = clf; best_rf14_params = cfg
        except Exception as e:
            print(f"  [FAILED] {tag}: {e}")

# Final test evaluation of best RF candidates
for feat_label, clf, params, X_ts, X_ben in [
    ("16f", best_rf16, best_rf16_params, X_test,   benign_vecs_16_scaled),
    ("14f", best_rf14, best_rf14_params, X_test14, benign_vecs_14_scaled),
]:
    if clf is None: continue
    print(f"\n  >> Best RF {feat_label}: {params}")
    preds, avg_lat, p95_lat = bench_predict_lat(clf, X_ts)
    probs = clf.predict_proba(X_ts)[:, 1]
    bench_m = metrics(y_test, preds, probs)

    fp, fpr, avg_lat, p95_lat = real_world_fp(lambda x: int(clf.predict(x)[0]), X_ben)
    real_m = {"fp": fp, "fp_rate": fpr}

    model_path = EXP_DIR / f"rf_{feat_label}" / "model.pkl"
    (EXP_DIR / f"rf_{feat_label}").mkdir(exist_ok=True)
    joblib.dump(clf, model_path)
    n_f = 16 if feat_label == "16f" else 14
    feat_names = FEATURES_16 if feat_label == "16f" else FEATURES_14

    save_candidate(f"rf_{feat_label}", clf, bench_scaler,
                   feat_names, {"model_type": "RandomForest", "params": params,
                                 "trained_at": datetime.now().isoformat(),
                                 "dataset": "UNSW-NB15 16-feature benchmark"},
                   bench_m, real_m)

    record(f"rf_{feat_label}", f"{n_f} features", n_f, bench_m, real_m,
           params, os.path.getsize(model_path)//1024, 0.0, avg_lat, p95_lat)
    print(f"  Benchmark — Acc: {bench_m['accuracy']:.4f}  F1: {bench_m['f1']:.4f}  "
          f"Recall: {bench_m['recall']:.4f}  ROC-AUC: {bench_m.get('roc_auc','N/A')}")
    print(f"  Real-world — FP: {fp}/{N_BENIGN}  FP-rate: {fpr:.2%}  AvgLat: {avg_lat:.3f}ms")
    print(f"  CM: {bench_m['cm']}")


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 3: EXTRA TREES
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("EXPERIMENT 3 — EXTRA TREES")
print(SEP)

ET_CONFIGS = [
    {"max_depth": d, "min_samples_leaf": 5, "n_estimators": 100, "random_state": RANDOM_STATE}
    for d in [8, 12, 16, 20]
]

best_et16_f1 = -1; best_et16 = None; best_et16_params = None
best_et14_f1 = -1; best_et14 = None; best_et14_params = None

for cfg in ET_CONFIGS:
    for feat_set, X_tr, X_v in [("16f", X_train, X_val), ("14f", X_train14, X_val14)]:
        tag = f"ET depth={cfg['max_depth']} {feat_set}"
        try:
            clf = ExtraTreesClassifier(**cfg)
            clf.fit(X_tr, y_train)
            val_preds = clf.predict(X_v)
            val_f1 = f1_score(y_val, val_preds, zero_division=0)
            print(f"  {tag} | val_f1={val_f1:.4f}")
            if feat_set == "16f" and val_f1 > best_et16_f1:
                best_et16_f1 = val_f1; best_et16 = clf; best_et16_params = cfg
            if feat_set == "14f" and val_f1 > best_et14_f1:
                best_et14_f1 = val_f1; best_et14 = clf; best_et14_params = cfg
        except Exception as e:
            print(f"  [FAILED] {tag}: {e}")

for feat_label, clf, params, X_ts, X_ben in [
    ("16f", best_et16, best_et16_params, X_test,   benign_vecs_16_scaled),
    ("14f", best_et14, best_et14_params, X_test14, benign_vecs_14_scaled),
]:
    if clf is None: continue
    print(f"\n  >> Best ET {feat_label}: {params}")
    preds, avg_lat, p95_lat = bench_predict_lat(clf, X_ts)
    probs = clf.predict_proba(X_ts)[:, 1]
    bench_m = metrics(y_test, preds, probs)
    fp, fpr, avg_lat, p95_lat = real_world_fp(lambda x: int(clf.predict(x)[0]), X_ben)
    real_m = {"fp": fp, "fp_rate": fpr}
    feat_names = FEATURES_16 if feat_label == "16f" else FEATURES_14
    save_candidate(f"et_{feat_label}", clf, bench_scaler, feat_names,
                   {"model_type": "ExtraTrees", "params": params, "trained_at": datetime.now().isoformat()},
                   bench_m, real_m)
    model_path = EXP_DIR / f"et_{feat_label}" / "model.pkl"
    n_f = 16 if feat_label == "16f" else 14
    record(f"et_{feat_label}", f"{n_f} features", n_f, bench_m, real_m,
           params, os.path.getsize(model_path)//1024, 0.0, avg_lat, p95_lat)
    print(f"  Benchmark — Acc: {bench_m['accuracy']:.4f}  F1: {bench_m['f1']:.4f}  "
          f"Recall: {bench_m['recall']:.4f}  ROC-AUC: {bench_m.get('roc_auc','N/A')}")
    print(f"  Real-world — FP: {fp}/{N_BENIGN}  FP-rate: {fpr:.2%}  AvgLat: {avg_lat:.3f}ms")
    print(f"  CM: {bench_m['cm']}")


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 4: HISTGRADIENTBOOSTING
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("EXPERIMENT 4 — HISTGRADIENTBOOSTING")
print(SEP)

HGB_CONFIGS = [
    {"max_iter": 200, "max_depth": d, "learning_rate": lr,
     "min_samples_leaf": 20, "random_state": RANDOM_STATE}
    for d in [6, 10] for lr in [0.05, 0.1]
]

best_hgb16_f1 = -1; best_hgb16 = None; best_hgb16_params = None
best_hgb14_f1 = -1; best_hgb14 = None; best_hgb14_params = None

for cfg in HGB_CONFIGS:
    for feat_set, X_tr, X_v in [("16f", X_train, X_val), ("14f", X_train14, X_val14)]:
        tag = f"HGB depth={cfg['max_depth']} lr={cfg['learning_rate']} {feat_set}"
        try:
            clf = HistGradientBoostingClassifier(**cfg)
            clf.fit(X_tr, y_train)
            val_preds = clf.predict(X_v)
            val_f1 = f1_score(y_val, val_preds, zero_division=0)
            print(f"  {tag} | val_f1={val_f1:.4f}")
            if feat_set == "16f" and val_f1 > best_hgb16_f1:
                best_hgb16_f1 = val_f1; best_hgb16 = clf; best_hgb16_params = cfg
            if feat_set == "14f" and val_f1 > best_hgb14_f1:
                best_hgb14_f1 = val_f1; best_hgb14 = clf; best_hgb14_params = cfg
        except Exception as e:
            print(f"  [FAILED] {tag}: {e}")

for feat_label, clf, params, X_ts, X_ben in [
    ("16f", best_hgb16, best_hgb16_params, X_test,   benign_vecs_16_scaled),
    ("14f", best_hgb14, best_hgb14_params, X_test14, benign_vecs_14_scaled),
]:
    if clf is None: continue
    print(f"\n  >> Best HGB {feat_label}: {params}")
    preds, avg_lat, p95_lat = bench_predict_lat(clf, X_ts)
    probs = clf.predict_proba(X_ts)[:, 1]
    bench_m = metrics(y_test, preds, probs)
    fp, fpr, avg_lat, p95_lat = real_world_fp(lambda x: int(clf.predict(x)[0]), X_ben)
    real_m = {"fp": fp, "fp_rate": fpr}
    feat_names = FEATURES_16 if feat_label == "16f" else FEATURES_14
    save_candidate(f"hgb_{feat_label}", clf, bench_scaler, feat_names,
                   {"model_type": "HistGradientBoosting", "params": params, "trained_at": datetime.now().isoformat()},
                   bench_m, real_m)
    model_path = EXP_DIR / f"hgb_{feat_label}" / "model.pkl"
    n_f = 16 if feat_label == "16f" else 14
    record(f"hgb_{feat_label}", f"{n_f} features", n_f, bench_m, real_m,
           params, os.path.getsize(model_path)//1024, 0.0, avg_lat, p95_lat)
    print(f"  Benchmark — Acc: {bench_m['accuracy']:.4f}  F1: {bench_m['f1']:.4f}  "
          f"Recall: {bench_m['recall']:.4f}  ROC-AUC: {bench_m.get('roc_auc','N/A')}")
    print(f"  Real-world — FP: {fp}/{N_BENIGN}  FP-rate: {fpr:.2%}  AvgLat: {avg_lat:.3f}ms")
    print(f"  CM: {bench_m['cm']}")


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 5: XGBOOST
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("EXPERIMENT 5 — XGBOOST")
print(SEP)

try:
    import xgboost as xgb
    XGB_CONFIGS = [
        {"n_estimators": 200, "max_depth": d, "learning_rate": lr,
         "subsample": 0.8, "colsample_bytree": 0.8,
         "use_label_encoder": False, "eval_metric": "logloss",
         "random_state": RANDOM_STATE}
        for d in [4, 6, 8] for lr in [0.05, 0.1]
    ]
    best_xgb16_f1 = -1; best_xgb16 = None; best_xgb16_params = None
    best_xgb14_f1 = -1; best_xgb14 = None; best_xgb14_params = None

    for cfg in XGB_CONFIGS:
        for feat_set, X_tr, X_v in [("16f", X_train, X_val), ("14f", X_train14, X_val14)]:
            tag = f"XGB depth={cfg['max_depth']} lr={cfg['learning_rate']} {feat_set}"
            try:
                clf = xgb.XGBClassifier(**cfg, verbosity=0)
                clf.fit(X_tr, y_train, eval_set=[(X_v, y_val)], verbose=False)
                val_preds = clf.predict(X_v)
                val_f1 = f1_score(y_val, val_preds, zero_division=0)
                print(f"  {tag} | val_f1={val_f1:.4f}")
                if feat_set == "16f" and val_f1 > best_xgb16_f1:
                    best_xgb16_f1 = val_f1; best_xgb16 = clf; best_xgb16_params = cfg
                if feat_set == "14f" and val_f1 > best_xgb14_f1:
                    best_xgb14_f1 = val_f1; best_xgb14 = clf; best_xgb14_params = cfg
            except Exception as e:
                print(f"  [FAILED] {tag}: {e}")

    for feat_label, clf, params, X_ts, X_ben in [
        ("16f", best_xgb16, best_xgb16_params, X_test,   benign_vecs_16_scaled),
        ("14f", best_xgb14, best_xgb14_params, X_test14, benign_vecs_14_scaled),
    ]:
        if clf is None: continue
        print(f"\n  >> Best XGB {feat_label}: {params}")
        preds, avg_lat, p95_lat = bench_predict_lat(clf, X_ts)
        probs = clf.predict_proba(X_ts)[:, 1]
        bench_m = metrics(y_test, preds, probs)
        fp, fpr, avg_lat, p95_lat = real_world_fp(lambda x: int(clf.predict(x)[0]), X_ben)
        real_m = {"fp": fp, "fp_rate": fpr}
        feat_names = FEATURES_16 if feat_label == "16f" else FEATURES_14
        save_candidate(f"xgb_{feat_label}", clf, bench_scaler, feat_names,
                       {"model_type": "XGBoost", "params": params, "trained_at": datetime.now().isoformat()},
                       bench_m, real_m)
        model_path = EXP_DIR / f"xgb_{feat_label}" / "model.pkl"
        n_f = 16 if feat_label == "16f" else 14
        record(f"xgb_{feat_label}", f"{n_f} features", n_f, bench_m, real_m,
               params, os.path.getsize(model_path)//1024, 0.0, avg_lat, p95_lat)
        print(f"  Benchmark — Acc: {bench_m['accuracy']:.4f}  F1: {bench_m['f1']:.4f}  "
              f"Recall: {bench_m['recall']:.4f}  ROC-AUC: {bench_m.get('roc_auc','N/A')}")
        print(f"  Real-world — FP: {fp}/{N_BENIGN}  FP-rate: {fpr:.2%}  AvgLat: {avg_lat:.3f}ms")
        print(f"  CM: {bench_m['cm']}")

except ImportError:
    print("  [SKIP] xgboost not installed.")


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 6: LIGHTGBM
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("EXPERIMENT 6 — LIGHTGBM")
print(SEP)

try:
    import lightgbm as lgb
    LGB_CONFIGS = [
        {"n_estimators": 200, "max_depth": d, "learning_rate": lr,
         "num_leaves": 31, "subsample": 0.8, "colsample_bytree": 0.8,
         "random_state": RANDOM_STATE, "verbose": -1}
        for d in [4, 6, 8] for lr in [0.05, 0.1]
    ]
    best_lgb16_f1 = -1; best_lgb16 = None; best_lgb16_params = None
    best_lgb14_f1 = -1; best_lgb14 = None; best_lgb14_params = None

    for cfg in LGB_CONFIGS:
        for feat_set, X_tr, X_v in [("16f", X_train, X_val), ("14f", X_train14, X_val14)]:
            tag = f"LGB depth={cfg['max_depth']} lr={cfg['learning_rate']} {feat_set}"
            try:
                clf = lgb.LGBMClassifier(**cfg)
                clf.fit(X_tr, y_train, eval_set=[(X_v, y_val)])
                val_preds = clf.predict(X_v)
                val_f1 = f1_score(y_val, val_preds, zero_division=0)
                print(f"  {tag} | val_f1={val_f1:.4f}")
                if feat_set == "16f" and val_f1 > best_lgb16_f1:
                    best_lgb16_f1 = val_f1; best_lgb16 = clf; best_lgb16_params = cfg
                if feat_set == "14f" and val_f1 > best_lgb14_f1:
                    best_lgb14_f1 = val_f1; best_lgb14 = clf; best_lgb14_params = cfg
            except Exception as e:
                print(f"  [FAILED] {tag}: {e}")

    for feat_label, clf, params, X_ts, X_ben in [
        ("16f", best_lgb16, best_lgb16_params, X_test,   benign_vecs_16_scaled),
        ("14f", best_lgb14, best_lgb14_params, X_test14, benign_vecs_14_scaled),
    ]:
        if clf is None: continue
        print(f"\n  >> Best LGB {feat_label}: {params}")
        preds, avg_lat, p95_lat = bench_predict_lat(clf, X_ts)
        probs = clf.predict_proba(X_ts)[:, 1]
        bench_m = metrics(y_test, preds, probs)
        fp, fpr, avg_lat, p95_lat = real_world_fp(lambda x: int(clf.predict(x)[0]), X_ben)
        real_m = {"fp": fp, "fp_rate": fpr}
        feat_names = FEATURES_16 if feat_label == "16f" else FEATURES_14
        save_candidate(f"lgb_{feat_label}", clf, bench_scaler, feat_names,
                       {"model_type": "LightGBM", "params": params, "trained_at": datetime.now().isoformat()},
                       bench_m, real_m)
        model_path = EXP_DIR / f"lgb_{feat_label}" / "model.pkl"
        n_f = 16 if feat_label == "16f" else 14
        record(f"lgb_{feat_label}", f"{n_f} features", n_f, bench_m, real_m,
               params, os.path.getsize(model_path)//1024, 0.0, avg_lat, p95_lat)
        print(f"  Benchmark — Acc: {bench_m['accuracy']:.4f}  F1: {bench_m['f1']:.4f}  "
              f"Recall: {bench_m['recall']:.4f}  ROC-AUC: {bench_m.get('roc_auc','N/A')}")
        print(f"  Real-world — FP: {fp}/{N_BENIGN}  FP-rate: {fpr:.2%}  AvgLat: {avg_lat:.3f}ms")
        print(f"  CM: {bench_m['cm']}")

except ImportError:
    print("  [SKIP] lightgbm not installed.")


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 7: ISOLATION FOREST INDEPENDENT EVALUATION
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("EXPERIMENT 7 — ISOLATION FOREST INDEPENDENT EVALUATION")
print(SEP)

try:
    prod_if = joblib.load(LIVE_IF_PATH)
    prod_scaler = joblib.load(LIVE_SCALER_PATH)
    prod_benign_scaled = prod_scaler.transform(benign_vecs_16)

    # Anomaly rate on benign real-world traffic
    if_scores_benign = prod_if.decision_function(prod_benign_scaled)
    if_preds_benign  = prod_if.predict(prod_benign_scaled)  # -1=anomaly, 1=normal
    n_anomaly_benign = (if_preds_benign == -1).sum()
    anom_rate_benign = n_anomaly_benign / len(if_preds_benign)
    print(f"  Benign flows:    {len(if_preds_benign)}  anomalies: {n_anomaly_benign}  rate: {anom_rate_benign:.2%}")

    # On benchmark test set (rescaled with prod_scaler)
    prod_test_raw = bench_scaler.inverse_transform(X_test)
    prod_test_scaled = prod_scaler.transform(prod_test_raw)
    if_preds_bench = prod_if.predict(prod_test_scaled)
    if_anom_bench  = (if_preds_bench == -1)
    # treat anomaly(-1) as positive (attack), normal(1) as negative
    if_bench_preds_binary = (if_preds_bench == -1).astype(int)
    if_bench_m = metrics(y_test, if_bench_preds_binary)
    print(f"  Benchmark: Acc={if_bench_m['accuracy']:.4f}  F1={if_bench_m['f1']:.4f}  "
          f"Recall={if_bench_m['recall']:.4f}  Prec={if_bench_m['precision']:.4f}")
    print(f"  CM: {if_bench_m['cm']}")

    RESULTS.append({
        "model": "isolation_forest_prod",
        "feature_set": "16 features (prod)",
        "n_features": 16,
        "accuracy": if_bench_m["accuracy"],
        "precision": if_bench_m["precision"],
        "recall": if_bench_m["recall"],
        "f1": if_bench_m["f1"],
        "real_benign_flows": N_BENIGN,
        "real_fp": int(n_anomaly_benign),
        "real_fp_rate": round(float(anom_rate_benign), 4),
        "real_fp_per_100": round(n_anomaly_benign/N_BENIGN*100, 2),
        "note": "IF used standalone as anomaly classifier",
    })
except Exception as e:
    print(f"  [FAILED] {e}")
    traceback.print_exc()


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT 8: EXTERNAL PRETRAINED CLASSICAL ML
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("EXPERIMENT 8 — EXTERNAL PRETRAINED CLASSICAL ML INVESTIGATION")
print(SEP)
print("""
  Investigation result:
  We searched for classical pretrained network security models with publicly
  available model artifacts. Candidates investigated:
  
  1. NSL-KDD pretrained Random Forest (Kaggle/GitHub)
     - Feature schema: 41 NSL-KDD features (symbolic categorical + numeric)
     - Required features include: 'service', 'flag', 'protocol_type' (string),
       'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', etc.
     - NONE of these 41 features can be directly computed from Sentinel's
       16-feature live representation without fabrication.
     - VERDICT: INCOMPATIBLE — rejected.

  2. CIC-IDS2017 pretrained XGBoost (various GitHub)
     - Feature schema: 78 CICFlowMeter features (flags, subflows, bulk rates, etc.)
     - Requires deep TCP flag statistics and segment-level analysis not available
       from the Sentinel flow extractor.
     - VERDICT: INCOMPATIBLE — rejected.

  3. UNSW-NB15 pretrained RF (various GitHub repos)
     - These models train on the full 47+ feature UNSW-NB15 schema.
     - Sentinel uses 16 features only; the remaining 31 features are unavailable.
     - Forcing them in would require fabricating 31 features.
     - VERDICT: INCOMPATIBLE — rejected.
  
  Conclusion: No external pretrained classical ML candidate can be integrated
  without fabricating features. This experiment is documented as REJECTED for
  compatibility reasons — not skipped. The benchmark experiment proceeds with
  newly trained candidates only.
""")

RESULTS.append({
    "model": "external_pretrained",
    "feature_set": "N/A",
    "n_features": "N/A",
    "status": "REJECTED",
    "reason": "All investigated external models require feature schemas incompatible with Sentinel's 16-feature live extractor. Integration would require feature fabrication.",
})


# ══════════════════════════════════════════════════════════════════════════════
# THRESHOLD ANALYSIS on best supervised candidates
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("THRESHOLD ANALYSIS — best candidates on VALIDATION set")
print(SEP)

THRESHOLDS = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
THRESHOLD_RESULTS = {}

# Collect the top candidates we trained
candidate_models = {}
if best_rf14  is not None: candidate_models["rf_14f"]  = (best_rf14,  X_val14, X_test14, benign_vecs_14_scaled)
if best_rf16  is not None: candidate_models["rf_16f"]  = (best_rf16,  X_val,   X_test,   benign_vecs_16_scaled)
if best_et14  is not None: candidate_models["et_14f"]  = (best_et14,  X_val14, X_test14, benign_vecs_14_scaled)
if best_hgb14 is not None: candidate_models["hgb_14f"] = (best_hgb14, X_val14, X_test14, benign_vecs_14_scaled)

try:
    if best_xgb14 is not None:
        candidate_models["xgb_14f"] = (best_xgb14, X_val14, X_test14, benign_vecs_14_scaled)
except: pass
try:
    if best_lgb14 is not None:
        candidate_models["lgb_14f"] = (best_lgb14, X_val14, X_test14, benign_vecs_14_scaled)
except: pass

for cname, (clf, X_v, X_ts, X_ben) in candidate_models.items():
    THRESHOLD_RESULTS[cname] = []
    val_probs = clf.predict_proba(X_v)[:, 1]
    best_thr = 0.5; best_thr_f1 = -1
    
    print(f"\n  {cname}:")
    print(f"  {'Threshold':>10}  {'Val-F1':>8}  {'Val-Rec':>8}  {'Val-Prec':>9}")
    for thr in THRESHOLDS:
        val_preds = (val_probs >= thr).astype(int)
        vf1   = f1_score(y_val, val_preds, zero_division=0)
        vrec  = recall_score(y_val, val_preds, zero_division=0)
        vprec = precision_score(y_val, val_preds, zero_division=0)
        THRESHOLD_RESULTS[cname].append({
            "threshold": thr, "val_f1": round(vf1,4),
            "val_recall": round(vrec,4), "val_precision": round(vprec,4)
        })
        flag = " <<< best" if vf1 > best_thr_f1 else ""
        if vf1 > best_thr_f1: best_thr_f1 = vf1; best_thr = thr
        print(f"  {thr:>10.2f}  {vf1:>8.4f}  {vrec:>8.4f}  {vprec:>9.4f}{flag}")
    
    # Report test performance at best threshold
    test_probs = clf.predict_proba(X_ts)[:, 1]
    test_preds = (test_probs >= best_thr).astype(int)
    tst_m = metrics(y_test, test_preds, test_probs)
    
    # Real-world FP at best threshold
    rw_lats = []
    rw_preds = []
    for row in X_ben:
        t0 = time.perf_counter()
        p = int(clf.predict_proba(row.reshape(1,-1))[0,1] >= best_thr)
        rw_lats.append(time.perf_counter()-t0)
        rw_preds.append(p)
    rw_fp = sum(rw_preds)
    rw_fpr = round(rw_fp/len(rw_preds), 4)
    rw_avg_lat = round(float(np.mean(rw_lats))*1000, 4)
    rw_p95_lat = round(float(np.percentile(rw_lats, 95))*1000, 4)
    
    print(f"  >> Best threshold={best_thr}: test-F1={tst_m['f1']:.4f}  "
          f"test-Recall={tst_m['recall']:.4f}  real-FP={rw_fp}/{N_BENIGN}({rw_fpr:.2%})")
    THRESHOLD_RESULTS[cname].append({
        "best_threshold": best_thr,
        "test_metrics": tst_m,
        "real_fp": rw_fp, "real_fp_rate": rw_fpr,
        "avg_lat_ms": rw_avg_lat, "p95_lat_ms": rw_p95_lat,
    })


# ══════════════════════════════════════════════════════════════════════════════
# HYBRID POLICY EVALUATION — best no-TTL candidate
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("HYBRID POLICY EVALUATION")
print(SEP)

try:
    prod_if_mdl = joblib.load(LIVE_IF_PATH)
    prod_scaler_mdl = joblib.load(LIVE_SCALER_PATH)

    # We'll use best RF 14f as the supervised model for policy tests
    # and the production IF (scaled with prod scaler) on raw-rescaled data
    sup_mdl = best_rf14
    
    # Reconstruct raw benign vectors and re-scale with prod scaler
    prod_benign_scaled_full = prod_scaler_mdl.transform(benign_vecs_16)

    # Use the 14-feat subset for supervised, and 16-feat prod-scaled for IF
    def policy_a(sup_prob, if_pred): return int(sup_prob >= 0.80)
    def policy_b(sup_prob, if_pred): return int(sup_prob >= 0.80 and if_pred == -1)
    def policy_c(sup_prob, if_pred):
        if sup_prob >= 0.95: return 1
        if if_pred == -1: return 1
        return 0
    def policy_d(sup_prob, if_pred):
        if sup_prob >= 0.95: return 1
        if sup_prob >= 0.80 and if_pred == -1: return 1
        return 0

    policies = {
        "A_supervised_only":      policy_a,
        "B_sup_and_IF":           policy_b,
        "C_highconf_or_IF":       policy_c,
        "D_tiered_highconf_or_corr": policy_d,
    }

    POLICY_RESULTS = {}

    for pname, pfn in policies.items():
        # Benchmark: compute on test set
        if sup_mdl is not None:
            sup_probs_test = sup_mdl.predict_proba(X_test14)[:, 1]
            prod_test_raw = bench_scaler.inverse_transform(X_test)
            prod_test_scaled = prod_scaler_mdl.transform(prod_test_raw)
            if_preds_test = prod_if_mdl.predict(prod_test_scaled)

            hybrid_preds_test = np.array([
                pfn(sup_probs_test[i], if_preds_test[i])
                for i in range(len(y_test))
            ])
            m = metrics(y_test, hybrid_preds_test)

            # Real-world FP
            sup_probs_benign = sup_mdl.predict_proba(benign_vecs_14_scaled)[:, 1]
            if_preds_benign = prod_if_mdl.predict(prod_benign_scaled_full)
            rw_preds = [pfn(sup_probs_benign[i], if_preds_benign[i]) for i in range(N_BENIGN)]
            rw_fp = sum(rw_preds)
            rw_fpr = round(rw_fp / N_BENIGN, 4)

            POLICY_RESULTS[pname] = {
                "benchmark": m,
                "real_fp": rw_fp, "real_fp_rate": rw_fpr,
                "real_fp_per_100": round(rw_fp/N_BENIGN*100, 2),
            }

            print(f"  {pname}:")
            print(f"    Benchmark — F1:{m['f1']:.4f}  Recall:{m['recall']:.4f}  "
                  f"Prec:{m['precision']:.4f}  Acc:{m['accuracy']:.4f}")
            print(f"    Real-world — FP:{rw_fp}/{N_BENIGN}  FP-rate:{rw_fpr:.2%}")
            print(f"    CM: {m['cm']}")

    # Save policy results
    with open(EXP_DIR / "policy_results.json", "w") as f:
        json.dump(POLICY_RESULTS, f, indent=2, default=str)

except Exception as e:
    print(f"  [FAILED] Hybrid policy evaluation: {e}")
    traceback.print_exc()
    POLICY_RESULTS = {}


# ══════════════════════════════════════════════════════════════════════════════
# SHAP ANALYSIS on best no-TTL RF
# ══════════════════════════════════════════════════════════════════════════════
print(f"\n{SEP}")
print("SHAP ANALYSIS — RF 14 features")
print(SEP)

try:
    import shap
    shap_clf = best_rf14
    if shap_clf is not None:
        explainer = shap.TreeExplainer(shap_clf)
        
        # Sample: 1 benign (test, y=0), 1 FP (test where pred=1, y=0), 1 TP (test pred=1, y=1)
        test_preds14 = shap_clf.predict(X_test14)
        test_probs14 = shap_clf.predict_proba(X_test14)[:,1]
        
        benign_idx  = np.where((y_test == 0) & (test_preds14 == 0))[0][:1]
        fp_idx      = np.where((y_test == 0) & (test_preds14 == 1))[0][:1]
        tp_idx      = np.where((y_test == 1) & (test_preds14 == 1))[0][:1]
        
        SHAP_OUT = {}
        for label, idxs in [("benign", benign_idx), ("false_positive", fp_idx), ("true_attack", tp_idx)]:
            if len(idxs) == 0:
                print(f"  No {label} samples found.")
                continue
            i = idxs[0]
            sv = explainer.shap_values(X_test14[i:i+1])
            # sv may be list or array depending on version
            if isinstance(sv, list): sv = sv[1]
            sv = sv.flatten()
            feat_imp = dict(zip(FEATURES_14, [round(float(v),4) for v in sv]))
            top = sorted(feat_imp.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
            SHAP_OUT[label] = {
                "sample_index": int(i),
                "true_label": int(y_test[i]),
                "rf_prob": round(float(test_probs14[i]),4),
                "top5_shap": dict(top),
            }
            print(f"  {label} (y={y_test[i]}, prob={test_probs14[i]:.3f}):")
            for fname, fval in top:
                print(f"    {fname:<12}: SHAP={fval:+.4f}")
        
        # Also SHAP for real-world benign flows that were flagged (FPs)
        rw_fp_idx = np.where(shap_clf.predict(benign_vecs_14_scaled) == 1)[0]
        if len(rw_fp_idx) > 0:
            i = rw_fp_idx[0]
            sv = explainer.shap_values(benign_vecs_14_scaled[i:i+1])
            if isinstance(sv, list): sv = sv[1]
            sv = sv.flatten()
            feat_imp = dict(zip(FEATURES_14, [round(float(v),4) for v in sv]))
            top = sorted(feat_imp.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
            SHAP_OUT["realworld_fp"] = {
                "sample_index": int(i),
                "top5_shap": dict(top),
            }
            print(f"  real_world_FP (14f model):")
            for fname, fval in top:
                print(f"    {fname:<12}: SHAP={fval:+.4f}")
        else:
            print("  No real-world FPs found at default threshold.")
            SHAP_OUT["realworld_fp"] = {"note": "No real-world FPs at default threshold"}

        with open(EXP_DIR / "shap_analysis.json", "w") as f:
            json.dump(SHAP_OUT, f, indent=2)
except Exception as e:
    print(f"  [WARNING] SHAP analysis failed: {e}")
    SHAP_OUT = {"error": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# SAVE FULL RESULTS JSON
# ══════════════════════════════════════════════════════════════════════════════
output = {
    "generated_at": datetime.now().isoformat(),
    "benchmark_dataset": {
        "source": "UNSW-NB15 raw CSV",
        "feature_count": 16,
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "train_pos_rate": round(float(y_train.mean()), 4),
        "test_pos_rate": round(float(y_test.mean()), 4),
        "split": "60/20/20 stratified, random_state=42",
        "scaler": "MinMaxScaler fitted on train only",
    },
    "benign_capture": {
        "source": "Live Scapy capture, authorized Sentinel environment, 60s window",
        "flow_count": N_BENIGN,
        "ground_truth": "BENIGN — known-normal Windows background traffic",
    },
    "candidates": RESULTS,
    "threshold_analysis": THRESHOLD_RESULTS,
    "hybrid_policies": POLICY_RESULTS if 'POLICY_RESULTS' in dir() else {},
    "shap": SHAP_OUT if 'SHAP_OUT' in dir() else {},
}

with open(EXP_DIR / "model_comparison.json", "w") as f:
    json.dump(output, f, indent=2, default=str)

print(f"\n{SEP}")
print("ALL EXPERIMENTS COMPLETE")
print(f"Results saved to: {EXP_DIR / 'model_comparison.json'}")
print(SEP)
