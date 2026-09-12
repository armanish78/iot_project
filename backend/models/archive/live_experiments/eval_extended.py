import json
import numpy as np
import joblib
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BENCH_DATA = os.path.join(SCRIPT_DIR, "benchmark_data")
PROD_MODELS = os.path.join(SCRIPT_DIR, "..", "live")

def evaluate():
    print("Loading extended benign capture (539 flows)...")
    with open(os.path.join(BENCH_DATA, "extended_benign_flows.json")) as f:
        flows = json.load(f)
        
    vecs_16 = np.array([f["vector"] for f in flows], dtype=np.float32)
    
    # Load scalers
    bench_scaler = joblib.load(os.path.join(BENCH_DATA, "scaler.pkl"))
    prod_scaler = joblib.load(os.path.join(PROD_MODELS, "live_scaler.pkl"))
    
    # Scale
    vecs_16_bench_scaled = bench_scaler.transform(vecs_16)
    vecs_16_prod_scaled = prod_scaler.transform(vecs_16)
    
    idx_14 = [0, 1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    vecs_14_bench_scaled = vecs_16_bench_scaled[:, idx_14]
    
    # Evaluate Proposed RF 14f @ 0.80
    rf14_clf = joblib.load(os.path.join(SCRIPT_DIR, "rf_14f", "model.pkl"))
    rf14_probs = rf14_clf.predict_proba(vecs_14_bench_scaled)[:, 1]
    rf14_preds = (rf14_probs >= 0.80).astype(int)
    fp_14 = rf14_preds.sum()
    
    # Evaluate Prod RF 16f
    prod_rf = joblib.load(os.path.join(PROD_MODELS, "live_rf.pkl"))
    prod_preds = prod_rf.predict(vecs_16_prod_scaled)
    fp_prod = prod_preds.sum()
    
    # Evaluate ET 14f @ 0.70
    et14_clf = joblib.load(os.path.join(SCRIPT_DIR, "et_14f", "model.pkl"))
    et14_probs = et14_clf.predict_proba(vecs_14_bench_scaled)[:, 1]
    et14_preds = (et14_probs >= 0.70).astype(int)
    fp_et = et14_preds.sum()
    
    print(f"\nEXTENDED BENIGN FP RESULTS (Total Flows: {len(flows)}):")
    print(f"Prod 16f RF:     {fp_prod} FPs ({fp_prod/len(flows):.2%})")
    print(f"Prop 14f RF @.80:{fp_14} FPs ({fp_14/len(flows):.2%})")
    print(f"ET 14f @.70:     {fp_et} FPs ({fp_et/len(flows):.2%})")

if __name__ == "__main__":
    evaluate()
