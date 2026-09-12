"""
backend/diagnostics/analyze_live_model_behavior.py
====================================================
READ-ONLY diagnostic.  Does NOT modify the database, models, or source code.

Run from the project root:
    python backend/diagnostics/analyze_live_model_behavior.py
"""

import json
import os
import sqlite3
import sys
from collections import defaultdict

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

DB_PATHS = [
    os.path.join(PROJECT_ROOT, "instance",          "iot_security.db"),
    os.path.join(PROJECT_ROOT, "backend", "instance", "iot_security.db"),
]

IPS_OF_INTEREST = {
    "192.168.31.86": "Phone",
    "192.168.31.79": "Sentinel PC",
    "192.168.31.1":  "Wi-Fi Gateway",
}

SEP = "-" * 72


def main():
    available = [(p, os.path.getsize(p)) for p in DB_PATHS if os.path.exists(p)]
    if not available:
        sys.exit(f"[ERROR] No database found. Checked: {DB_PATHS}")

    print("All DB files found:")
    for p, sz in available:
        print(f"  {p}  ({sz:,} bytes)")

    DB_PATH = max(available, key=lambda x: x[1])[0]
    print(f"\nUsing (largest): {DB_PATH}\n")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # ------------------------------------------------------------------
    # SECTION 0 -- Overview
    # ------------------------------------------------------------------
    print(SEP)
    print("SECTION 0 -- DATABASE OVERVIEW")
    print(SEP)

    cur.execute("SELECT COUNT(*) FROM predictions")
    total_predictions = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cur.fetchone()[0]
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM predictions")
    ts = cur.fetchone()

    print(f"Total predictions : {total_predictions}")
    print(f"Total alerts      : {total_alerts}")
    print(f"Timestamp range   : {ts[0]}  to  {ts[1]}")
    print("(Timestamps are UTC naive strings -- add +05:30 for local IST)")

    # ------------------------------------------------------------------
    # SECTION 1 -- run_id distribution
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 1 -- run_id DISTRIBUTION")
    print(SEP)

    cur.execute("""
        SELECT run_id,
               COUNT(*) AS total,
               SUM(CASE WHEN threat = 1 THEN 1 ELSE 0 END) AS threats
        FROM predictions
        GROUP BY run_id
        ORDER BY total DESC
    """)
    run_rows = cur.fetchall()
    print(f"{'run_id':<30}  {'total':>8}  {'threats':>8}  {'threat%':>8}")
    print("-" * 62)
    for r in run_rows:
        pct = (r["threats"] / r["total"] * 100) if r["total"] else 0
        print(f"{str(r['run_id']):<30}  {r['total']:>8}  "
              f"{r['threats']:>8}  {pct:>7.1f}%")

    # ------------------------------------------------------------------
    # Fetch all predictions
    # ------------------------------------------------------------------
    cur.execute("""
        SELECT id, timestamp, source_ip, dest_ip,
               threat, confidence, threat_type,
               rf_prediction, if_prediction,
               explanation, run_id
        FROM predictions
        ORDER BY timestamp DESC
    """)
    all_preds = cur.fetchall()

    if not all_preds:
        print("No prediction records found.")
        con.close()
        return

    total_n = len(all_preds)

    # ------------------------------------------------------------------
    # SECTION 2 -- Vote breakdown
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 2 -- MODEL VOTE BREAKDOWN")
    print(SEP)

    bucket_labels = {
        (0,  1): "RF=normal  + IF=normal  ",
        (1,  1): "RF=attack  + IF=normal  ",
        (0, -1): "RF=normal  + IF=anomaly ",
        (1, -1): "RF=attack  + IF=anomaly ",
    }

    buckets = defaultdict(list)
    for p in all_preds:
        rf  = p["rf_prediction"]
        ifv = p["if_prediction"]
        if rf is None or ifv is None:
            continue
        buckets[(int(rf), int(ifv))].append(p)

    total_with_votes = sum(len(v) for v in buckets.values())
    print(f"{'Combination':<36}  {'Count':>7}  {'%':>6}  "
          f"{'AvgConf':>8}  {'Threats':>8}  {'Threat%':>8}")
    print("-" * 84)

    for key in [(0, 1), (1, 1), (0, -1), (1, -1)]:
        rows     = buckets.get(key, [])
        n        = len(rows)
        pct      = (n / total_with_votes * 100) if total_with_votes else 0
        avg_conf = (sum(r["confidence"] for r in rows) / n) if n else 0.0
        threats  = sum(1 for r in rows if r["threat"])
        tpct     = (threats / n * 100) if n else 0.0
        print(f"{bucket_labels[key]:<36}  {n:>7}  {pct:>5.1f}%  "
              f"{avg_conf:>8.3f}  {threats:>8}  {tpct:>7.1f}%")

    # ------------------------------------------------------------------
    # SECTION 3 -- Confidence distribution per bucket
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 3 -- CONFIDENCE DISTRIBUTION PER BUCKET")
    print(SEP)

    thresholds = [0.50, 0.60, 0.70, 0.80, 0.90]
    for key in [(0, 1), (1, 1), (0, -1), (1, -1)]:
        rows = buckets.get(key, [])
        if not rows:
            continue
        confs = [r["confidence"] for r in rows]
        n     = len(confs)
        print(f"\n  {bucket_labels[key].strip()}  (n={n})")
        print(f"    min={min(confs):.3f}  max={max(confs):.3f}  "
              f"mean={sum(confs)/n:.3f}")
        for t in thresholds:
            above = sum(1 for c in confs if c >= t)
            print(f"    >= {t:.2f} : {above:>5}  ({above/n*100:>5.1f}%)")

    # ------------------------------------------------------------------
    # SECTION 4 -- Source IP breakdown
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 4 -- SOURCE IP BREAKDOWN")
    print(SEP)

    ip_stats = defaultdict(lambda: {"total": 0, "threat": 0,
                                     "rf_attack": 0, "if_anomaly": 0,
                                     "confs": []})
    for p in all_preds:
        ip = p["source_ip"] or "unknown"
        ip_stats[ip]["total"]    += 1
        ip_stats[ip]["threat"]   += 1 if p["threat"] else 0
        ip_stats[ip]["rf_attack"]+= 1 if p["rf_prediction"] == 1 else 0
        ip_stats[ip]["if_anomaly"]+= 1 if p["if_prediction"] == -1 else 0
        ip_stats[ip]["confs"].append(p["confidence"])

    sorted_ips = sorted(ip_stats.items(), key=lambda x: x[1]["total"], reverse=True)

    print(f"{'Source IP':<22}  {'Label':<16}  {'Total':>6}  "
          f"{'Threat':>7}  {'T%':>6}  {'RF_atk':>6}  {'IF_ano':>6}  {'AvgConf':>8}")
    print("-" * 90)
    for ip, s in sorted_ips:
        label  = IPS_OF_INTEREST.get(ip, "")
        total  = s["total"]
        threat = s["threat"]
        tpct   = threat / total * 100 if total else 0
        aconf  = sum(s["confs"]) / total if total else 0
        print(f"{ip:<22}  {label:<16}  {total:>6}  "
              f"{threat:>7}  {tpct:>5.1f}%  {s['rf_attack']:>6}  "
              f"{s['if_anomaly']:>6}  {aconf:>8.3f}")

    # ------------------------------------------------------------------
    # SECTION 5 -- Destination IP breakdown (top 15)
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 5 -- DESTINATION IP BREAKDOWN (top 15)")
    print(SEP)

    dst_stats = defaultdict(lambda: {"total": 0, "threat": 0})
    for p in all_preds:
        dst = p["dest_ip"] or "unknown"
        dst_stats[dst]["total"]  += 1
        dst_stats[dst]["threat"] += 1 if p["threat"] else 0

    sorted_dst = sorted(dst_stats.items(),
                        key=lambda x: x[1]["total"], reverse=True)[:15]
    print(f"{'Dest IP':<22}  {'Label':<16}  {'Total':>6}  {'Threat':>7}  {'T%':>6}")
    print("-" * 66)
    for ip, s in sorted_dst:
        label = IPS_OF_INTEREST.get(ip, "")
        tpct  = s["threat"] / s["total"] * 100 if s["total"] else 0
        print(f"{ip:<22}  {label:<16}  {s['total']:>6}  {s['threat']:>7}  {tpct:>5.1f}%")

    # ------------------------------------------------------------------
    # SECTION 6 -- Threat type distribution
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 6 -- THREAT TYPE DISTRIBUTION")
    print(SEP)

    type_stats = defaultdict(lambda: {"total": 0, "threat": 0})
    for p in all_preds:
        tt = p["threat_type"] or "none"
        type_stats[tt]["total"]  += 1
        type_stats[tt]["threat"] += 1 if p["threat"] else 0

    print(f"{'threat_type':<26}  {'Total':>7}  {'Flagged':>8}  {'Flagged%':>9}")
    print("-" * 58)
    for tt, s in sorted(type_stats.items(),
                        key=lambda x: x[1]["total"], reverse=True):
        tpct = s["threat"] / s["total"] * 100 if s["total"] else 0
        print(f"{tt:<26}  {s['total']:>7}  {s['threat']:>8}  {tpct:>8.1f}%")

    # ------------------------------------------------------------------
    # SECTION 7 -- IPs of interest
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 7 -- TRAFFIC INVOLVING IPs OF INTEREST")
    print(SEP)

    for ip, label in IPS_OF_INTEREST.items():
        involved  = [p for p in all_preds
                     if p["source_ip"] == ip or p["dest_ip"] == ip]
        total_ip  = len(involved)
        threat_ip = sum(1 for p in involved if p["threat"])
        tpct      = threat_ip / total_ip * 100 if total_ip else 0

        print(f"\n  {label} ({ip})")
        print(f"  Total (any direction): {total_ip}  | Threats: {threat_ip} ({tpct:.1f}%)")

        if involved:
            sample = involved[:20]
            print(f"  {'Timestamp':<22}  {'Src':<16}  {'Dst':<16}  "
                  f"{'RF':>6}  {'IF':>6}  {'Conf':>6}  {'Type':<24}  Threat")
            print("  " + "-" * 108)
            for r in sample:
                rf_sym = "ATTACK" if r["rf_prediction"] == 1 else "normal"
                if_sym = "ANOMAL" if r["if_prediction"] == -1 else "normal"
                t_sym  = "YES" if r["threat"] else " no"
                print(f"  {str(r['timestamp']):<22}  {str(r['source_ip']):<16}  "
                      f"{str(r['dest_ip']):<16}  {rf_sym:>6}  {if_sym:>6}  "
                      f"{r['confidence']:>6.3f}  {str(r['threat_type']):<24}  {t_sym}")
        else:
            print("  No predictions found for this IP.")

    # ------------------------------------------------------------------
    # SECTION 8 -- 20 most recent THREAT predictions
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 8 -- 20 MOST RECENT THREAT PREDICTIONS (detailed)")
    print(SEP)

    cur.execute("""
        SELECT id, timestamp, source_ip, dest_ip,
               threat, confidence, threat_type,
               rf_prediction, if_prediction,
               explanation, run_id
        FROM predictions
        WHERE threat = 1
        ORDER BY timestamp DESC
        LIMIT 20
    """)
    threat_rows = cur.fetchall()

    if not threat_rows:
        print("  No threat predictions in the database.")
    else:
        for i, r in enumerate(threat_rows, 1):
            rf_str = "ATTACK" if r["rf_prediction"] == 1 else "normal"
            if_str = "ANOMALY" if r["if_prediction"] == -1 else "normal"
            try:
                exp = json.loads(r["explanation"]) if r["explanation"] else {}
            except Exception:
                exp = {}
            print(f"\n  [{i:02d}] {r['timestamp']}  run_id: {r['run_id']}")
            print(f"       {r['source_ip']}  ->  {r['dest_ip']}")
            print(f"       RF: {rf_str:<8}  IF: {if_str:<8}  "
                  f"conf: {r['confidence']:.3f}  type: {r['threat_type']}")
            if exp.get("text"):
                print(f"       {exp['text'][:115]}")

    # ------------------------------------------------------------------
    # SECTION 9 -- Root cause analysis
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 9 -- ROOT CAUSE ANALYSIS")
    print(SEP)

    total_threats      = sum(1 for p in all_preds if p["threat"])
    rf_only_flagged    = sum(1 for r in buckets.get((1,  1), []) if r["threat"])
    if_only_threats    = sum(1 for r in buckets.get((0, -1), []) if r["threat"])
    both_agree_threats = sum(1 for r in buckets.get((1, -1), []) if r["threat"])
    rf_attack_total    = sum(1 for p in all_preds if p["rf_prediction"] == 1)
    if_anomaly_n       = sum(1 for p in all_preds if p["if_prediction"] == -1)

    if_anomaly_total  = (len(buckets.get((0, -1), []))
                         + len(buckets.get((1, -1), [])))
    if_anomaly_threat = if_only_threats + both_agree_threats

    print(f"  Total threat predictions : {total_threats} / {total_n} "
          f"({total_threats/total_n*100:.1f}%)")
    print()
    print(f"  RF predicts ATTACK  : {rf_attack_total}/{total_n} "
          f"({rf_attack_total/total_n*100:.1f}%)")
    print(f"  IF detects ANOMALY  : {if_anomaly_n}/{total_n} "
          f"({if_anomaly_n/total_n*100:.1f}%)")
    print()
    print(f"  Threat breakdown by vote combination:")
    print(f"    RF-only (RF=atk, IF=nrm)  : {rf_only_flagged} threats")
    print(f"    IF-only (RF=nrm, IF=ano)  : {if_only_threats} threats")
    print(f"    Both agree  (RF+IF)       : {both_agree_threats} threats")
    if if_anomaly_total:
        print(f"\n  IF anomaly -> threat conversion rate: "
              f"{if_anomaly_threat}/{if_anomaly_total} "
              f"({if_anomaly_threat/if_anomaly_total*100:.1f}%)")

    drivers  = {"RF-alone": rf_only_flagged,
                "IF-alone": if_only_threats,
                "both-agree": both_agree_threats}
    primary  = max(drivers, key=drivers.get)
    print(f"\n  PRIMARY THREAT DRIVER: {primary}  ({drivers[primary]} threats)")

    # ------------------------------------------------------------------
    # SECTION 10 -- Per-run summary
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 10 -- PER-RUN SUMMARY")
    print(SEP)

    run_groups = defaultdict(list)
    for p in all_preds:
        run_groups[p["run_id"]].append(p)

    print(f"{'run_id':<30}  {'n':>6}  {'threats':>8}  {'T%':>6}  "
          f"{'RF_atk':>7}  {'IF_ano':>7}  {'avgConf':>8}")
    print("-" * 80)
    for run_id, preds in sorted(run_groups.items(),
                                 key=lambda x: len(x[1]), reverse=True):
        n       = len(preds)
        threats = sum(1 for p in preds if p["threat"])
        rf_atk  = sum(1 for p in preds if p["rf_prediction"] == 1)
        if_ano  = sum(1 for p in preds if p["if_prediction"] == -1)
        avg_c   = sum(p["confidence"] for p in preds) / n
        tpct    = threats / n * 100
        print(f"{str(run_id):<30}  {n:>6}  {threats:>8}  {tpct:>5.1f}%  "
              f"{rf_atk:>7}  {if_ano:>7}  {avg_c:>8.3f}")

    # ------------------------------------------------------------------
    # SECTION 11 -- SHAP top features in threats
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 11 -- MOST INFLUENTIAL SHAP FEATURES IN THREAT PREDICTIONS")
    print(SEP)

    feature_vote = defaultdict(lambda: {"count": 0, "toward": 0, "away": 0})
    for p in all_preds:
        if not p["threat"] or not p["explanation"]:
            continue
        try:
            exp = json.loads(p["explanation"])
            for feat in exp.get("top_features", []):
                name = feat.get("feature", "?")
                feature_vote[name]["count"] += 1
                if feat.get("direction") == "toward_threat":
                    feature_vote[name]["toward"] += 1
                else:
                    feature_vote[name]["away"] += 1
        except Exception:
            continue

    sorted_feats = sorted(feature_vote.items(),
                          key=lambda x: x[1]["count"], reverse=True)[:15]
    print(f"  {'Feature':<25}  {'Count':>6}  {'Toward_threat':>14}  {'Away_threat':>12}")
    print("  " + "-" * 62)
    for feat, v in sorted_feats:
        print(f"  {feat:<25}  {v['count']:>6}  {v['toward']:>14}  {v['away']:>12}")

    # ------------------------------------------------------------------
    # SECTION 12 -- IF-anomaly flows NOT flagged as threats
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 12 -- IF-ANOMALY FLOWS NOT FLAGGED AS THREATS (sample)")
    print(SEP)

    not_flagged = [r for r in buckets.get((0, -1), []) if not r["threat"]]
    print(f"  (RF=normal, IF=anomaly) rows NOT marked threat: {len(not_flagged)}")
    if not_flagged:
        confs = [r["confidence"] for r in not_flagged]
        print(f"  Confidence: min={min(confs):.3f}  max={max(confs):.3f}  "
              f"mean={sum(confs)/len(confs):.3f}")
        for r in not_flagged[:10]:
            print(f"    {r['timestamp']}  {r['source_ip']}  ->  {r['dest_ip']}  "
                  f"conf={r['confidence']:.3f}  type={r['threat_type']}")

    con.close()
    print()
    print(SEP)
    print("Diagnostic complete. NO data was modified.")
    print(SEP)


if __name__ == "__main__":
    main()
