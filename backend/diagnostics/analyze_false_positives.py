"""
backend/diagnostics/analyze_false_positives.py
================================================
READ-ONLY diagnostic for deep feature & SHAP analysis.
"""

import json
import os
import sqlite3
import statistics
import sys
import pickle
from collections import defaultdict

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

DB_PATHS = [
    os.path.join(PROJECT_ROOT, "backend", "instance", "iot_security.db"),
    os.path.join(PROJECT_ROOT, "instance", "iot_security.db"),
]

LIVE_MODEL_DIR = os.path.join(PROJECT_ROOT, "backend", "models", "live")

SEP = "-" * 80

def percentile(sorted_vals, p):
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)

def feature_stats(vals):
    if not vals:
        return {}
    sv = sorted(vals)
    n = len(sv)
    return {
        "min": sv[0],
        "max": sv[-1],
        "mean": sum(sv)/n,
        "median": statistics.median(sv),
        "P25": percentile(sv, 25),
        "P75": percentile(sv, 75),
        "P90": percentile(sv, 90),
        "P95": percentile(sv, 95),
        "P99": percentile(sv, 99)
    }

def main():
    # Find correct DB
    available = [(p, os.path.getsize(p)) for p in DB_PATHS if os.path.exists(p)]
    if not available:
        sys.exit(f"[ERROR] No database found.")
    
    DB_PATH = max(available, key=lambda x: x[1])[0]
    
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    
    cur.execute("SELECT COUNT(*) FROM predictions")
    total_preds = cur.fetchone()[0]
    
    print(f"DATABASE VERIFICATION")
    print(f"Path: {DB_PATH}")
    print(f"Total predictions: {total_preds}")
    if total_preds != 5992:
        print(f"WARNING: Expected 5992 predictions, found {total_preds}")
    print(SEP)

    cur.execute("""
        SELECT id, timestamp, source_ip, dest_ip,
               threat, confidence, threat_type,
               rf_prediction, if_prediction,
               explanation, run_id
        FROM predictions
    """)
    all_preds = cur.fetchall()

    # PART 1: Top False-Positive Traffic Patterns
    print("PART 1: IDENTIFY FALSE-POSITIVE TRAFFIC")
    print(SEP)
    
    patterns = defaultdict(lambda: {
        "count": 0, "threats": 0, "rf_only": 0, "rf_if": 0, "confs": []
    })
    
    for p in all_preds:
        src = p["source_ip"] or "unknown"
        dst = p["dest_ip"] or "unknown"
        key = f"{src} -> {dst}"
        patterns[key]["count"] += 1
        if p["threat"]:
            patterns[key]["threats"] += 1
            if p["rf_prediction"] == 1 and p["if_prediction"] == 1:
                patterns[key]["rf_only"] += 1
            if p["rf_prediction"] == 1 and p["if_prediction"] == -1:
                patterns[key]["rf_if"] += 1
            patterns[key]["confs"].append(p["confidence"])
            
    sorted_patterns = sorted(patterns.items(), key=lambda x: x[1]["threats"], reverse=True)
    
    print(f"{'Pattern (Src -> Dst)':<35} | {'Count':<6} | {'Threats':<7} | {'RF-only':<7} | {'RF+IF':<5} | {'AvgConf':<7} | {'Conf Range'}")
    for k, v in sorted_patterns[:20]:
        if v["threats"] > 0:
            avg_c = sum(v["confs"])/len(v["confs"])
            c_range = f"{min(v['confs']):.2f}-{max(v['confs']):.2f}"
            print(f"{k:<35} | {v['count']:<6} | {v['threats']:<7} | {v['rf_only']:<7} | {v['rf_if']:<5} | {avg_c:<7.3f} | {c_range}")

    print(SEP)

    # Note: We need raw features to do Part 2. But raw features are NOT in the predictions table.
    # We must fetch the flow inputs from explanation or re-run feature extraction if they were stored?
    # Actually, the explanation JSON often contains the feature values! Let's check.
    sample_exp = None
    for p in all_preds:
        if p["explanation"]:
            try:
                sample_exp = json.loads(p["explanation"])
                break
            except: pass
            
    print(f"Sample explanation keys: {list(sample_exp.keys()) if sample_exp else 'None'}")
    if sample_exp and 'top_features' in sample_exp:
        print(f"Sample top_features: {sample_exp['top_features'][:2]}")
        # The explanation 'top_features' has 'feature', 'value', 'impact', 'direction'
        
    # Let's collect feature values from explanations
    rf_only_feats = defaultdict(list)
    rf_if_feats = defaultdict(list)
    benign_feats = defaultdict(list) # Sentinel -> Google/router but threat=0
    
    for p in all_preds:
        if not p["explanation"]: continue
        try:
            exp = json.loads(p["explanation"])
            feats = {f["feature"]: f.get("raw_value") for f in exp.get("top_features", []) if "raw_value" in f}
            
            is_rf_only = p["threat"] and p["rf_prediction"] == 1 and p["if_prediction"] == 1
            is_rf_if = p["threat"] and p["rf_prediction"] == 1 and p["if_prediction"] == -1
            is_benign_sentinel = not p["threat"] and p["source_ip"] == "192.168.31.79" and p["dest_ip"] in ["192.168.31.1", "172.217.114.4", "172.217.112.4"]
            
            for k, v in feats.items():
                if is_rf_only: rf_only_feats[k].append(v)
                elif is_rf_if: rf_if_feats[k].append(v)
                elif is_benign_sentinel: benign_feats[k].append(v)
        except:
            pass

    print("PART 2: FEATURE-LEVEL FALSE POSITIVE ANALYSIS")
    print("Due to space, we will print medians and P95s for key features.")
    key_features = ["sttl", "dttl", "sbytes", "dbytes", "dur", "smean", "dmean", "rate", "proto_tcp", "proto_udp"]
    
    for feat in key_features:
        rfo = feature_stats(rf_only_feats[feat])
        rfi = feature_stats(rf_if_feats[feat])
        ben = feature_stats(benign_feats[feat])
        
        print(f"Feature: {feat}")
        print(f"  RF-only threats : median={rfo.get('median', 'N/A')}, P95={rfo.get('P95', 'N/A')}")
        print(f"  RF+IF threats   : median={rfi.get('median', 'N/A')}, P95={rfi.get('P95', 'N/A')}")
        print(f"  Benign Sentinel : median={ben.get('median', 'N/A')}, P95={ben.get('P95', 'N/A')}")

    print(SEP)
    
    # PART 3: SHAP FALSE-POSITIVE ANALYSIS
    print("PART 3: SHAP FALSE-POSITIVE ANALYSIS")
    shap_stats = defaultdict(lambda: {"impact_sum": 0, "count": 0, "toward": 0, "away": 0})
    
    for p in all_preds:
        if p["threat"] and p["rf_prediction"] == 1 and p["if_prediction"] == 1:
            try:
                exp = json.loads(p["explanation"])
                for f in exp.get("top_features", []):
                    name = f["feature"]
                    shap_stats[name]["impact_sum"] += abs(f.get("impact", 0))
                    shap_stats[name]["count"] += 1
                    if f.get("direction") == "toward_threat":
                        shap_stats[name]["toward"] += 1
                    else:
                        shap_stats[name]["away"] += 1
            except: pass

    print("Top features in RF-only threats by occurrence in SHAP explanations:")
    sorted_shap = sorted(shap_stats.items(), key=lambda x: x[1]["count"], reverse=True)
    for k, v in sorted_shap[:10]:
        avg_imp = v["impact_sum"] / v["count"] if v["count"] else 0
        print(f"  {k:<15} | count: {v['count']:<4} | avg_impact: {avg_imp:.4f} | toward: {v['toward']:<4} | away: {v['away']:<4}")

    print(SEP)

    # PART 4: TRAINING-DATA VS REAL-TRAFFIC DISTRIBUTION
    print("PART 4: TRAINING-DATA VS REAL-TRAFFIC DISTRIBUTION")
    scaler_path = os.path.join(LIVE_MODEL_DIR, "live_scaler.pkl")
    rf_path = os.path.join(LIVE_MODEL_DIR, "live_rf.pkl")
    meta_path = os.path.join(LIVE_MODEL_DIR, "live_metadata.json")
    feature_names_path = os.path.join(LIVE_MODEL_DIR, "live_feature_names.json")
    
    try:
        with open(scaler_path, "rb") as f:
            scaler = pickle.load(f)
        with open(feature_names_path, "r") as f:
            feature_names = json.load(f)
            
        print(f"Scaler type: {type(scaler).__name__}")
        if hasattr(scaler, "mean_"):
            for i, fname in enumerate(feature_names):
                if fname in key_features:
                    ben = feature_stats(benign_feats[fname])
                    print(f"  {fname:<12}: Train Mean={scaler.mean_[i]:.2f}, Scale={scaler.scale_[i]:.2f} | Real Benign Med={ben.get('median', 'N/A')}")
        elif hasattr(scaler, "data_min_"):
            for i, fname in enumerate(feature_names):
                if fname in key_features:
                    ben = feature_stats(benign_feats[fname])
                    print(f"  {fname:<12}: Train Min={scaler.data_min_[i]:.2f}, Max={scaler.data_max_[i]:.2f} | Real Benign Med={ben.get('median', 'N/A')}, P95={ben.get('P95', 'N/A')}")
    except Exception as e:
        print(f"Error loading scaler: {e}")

    print(SEP)

    # PART 5: MODEL BEHAVIOR
    print("PART 5: MODEL BEHAVIOR")
    try:
        with open(rf_path, "rb") as f:
            rf = pickle.load(f)
        with open(meta_path, "r") as f:
            meta = json.load(f)
            
        print(f"Model type: {type(rf).__name__}")
        if hasattr(rf, "n_estimators"):
            print(f"Trees: {rf.n_estimators}")
        if hasattr(rf, "max_depth"):
            print(f"Max depth: {rf.max_depth}")
        print(f"Metadata: {meta}")
    except Exception as e:
        print(f"Error loading model: {e}")


if __name__ == "__main__":
    main()
