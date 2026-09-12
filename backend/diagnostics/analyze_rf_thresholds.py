"""
backend/diagnostics/analyze_rf_thresholds.py
=============================================
READ-ONLY threshold sensitivity analysis.
Does NOT modify the database, models, or source code.

Run from the project root:
    python backend/diagnostics/analyze_rf_thresholds.py
"""

import json
import os
import sqlite3
import statistics
import sys

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

DB_PATHS = [
    os.path.join(PROJECT_ROOT, "instance",           "iot_security.db"),
    os.path.join(PROJECT_ROOT, "backend", "instance", "iot_security.db"),
]

SEP  = "-" * 72
SEP2 = "=" * 72

THRESHOLDS = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 0.98]


def percentile(sorted_vals, p):
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def describe(label, vals):
    if not vals:
        print(f"  {label}: no data")
        return
    sv = sorted(vals)
    n  = len(sv)
    mn = sv[0]
    mx = sv[-1]
    mu = sum(sv) / n
    md = statistics.median(sv)
    p50 = percentile(sv, 50)
    p75 = percentile(sv, 75)
    p90 = percentile(sv, 90)
    p95 = percentile(sv, 95)
    p99 = percentile(sv, 99)
    print(f"  {label}  (n={n})")
    print(f"    min={mn:.4f}  max={mx:.4f}  mean={mu:.4f}  median={md:.4f}")
    print(f"    P50={p50:.4f}  P75={p75:.4f}  P90={p90:.4f}  "
          f"P95={p95:.4f}  P99={p99:.4f}")


def main():
    available = [(p, os.path.getsize(p)) for p in DB_PATHS if os.path.exists(p)]
    if not available:
        sys.exit(f"[ERROR] No database found. Checked: {DB_PATHS}")

    DB_PATH = max(available, key=lambda x: x[1])[0]
    print(f"Using database: {DB_PATH}\n")

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Fetch all predictions
    cur.execute("""
        SELECT id, timestamp, source_ip, dest_ip,
               threat, confidence, threat_type,
               rf_prediction, if_prediction,
               explanation, run_id
        FROM predictions
        ORDER BY timestamp DESC
    """)
    all_preds = cur.fetchall()
    total_n   = len(all_preds)

    # Separate into the four vote buckets
    rf_atk_if_nrm = [p for p in all_preds
                     if p["rf_prediction"] == 1 and p["if_prediction"] == 1]
    rf_atk_if_ano = [p for p in all_preds
                     if p["rf_prediction"] == 1 and p["if_prediction"] == -1]
    rf_nrm_if_ano = [p for p in all_preds
                     if p["rf_prediction"] == 0 and p["if_prediction"] == -1]
    rf_nrm_if_nrm = [p for p in all_preds
                     if p["rf_prediction"] == 0 and p["if_prediction"] == 1]

    # confidence is stored as the final hybrid value.
    # For RF-attack flows it corresponds to the RF attack probability.
    confs_rf_only  = [p["confidence"] for p in rf_atk_if_nrm]
    confs_rf_and_if = [p["confidence"] for p in rf_atk_if_ano]

    # ------------------------------------------------------------------
    # SECTION 0 -- Recap
    # ------------------------------------------------------------------
    print(SEP2)
    print("SECTION 0 -- BUCKET RECAP")
    print(SEP2)
    print(f"  Total predictions                : {total_n}")
    print(f"  RF=attack + IF=normal  (RF-only) : {len(rf_atk_if_nrm)}")
    print(f"  RF=attack + IF=anomaly (RF+IF)   : {len(rf_atk_if_ano)}")
    print(f"  RF=normal + IF=anomaly (IF-only) : {len(rf_nrm_if_ano)}")
    print(f"  RF=normal + IF=normal  (benign)  : {len(rf_nrm_if_nrm)}")

    # ------------------------------------------------------------------
    # SECTION 1 -- Distribution statistics
    # ------------------------------------------------------------------
    print()
    print(SEP2)
    print("SECTION 1 -- RF CONFIDENCE DISTRIBUTION STATISTICS")
    print(SEP2)
    print()
    describe("RF=attack + IF=normal  (RF-only)", confs_rf_only)
    print()
    describe("RF=attack + IF=anomaly (RF+IF)  ", confs_rf_and_if)

    # ------------------------------------------------------------------
    # SECTION 2 -- Histogram of RF-only confidence
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 2 -- HISTOGRAM: RF=attack + IF=normal confidence")
    print(SEP)
    bins = [(i/100, (i+5)/100) for i in range(0, 100, 5)]
    print(f"  {'Bin':<14}  {'Count':>6}  {'%':>6}  Bar")
    print("  " + "-" * 60)
    for lo, hi in bins:
        cnt = sum(1 for c in confs_rf_only if lo <= c < hi)
        if cnt == 0 and lo < 0.30:
            continue
        bar = "#" * min(cnt, 60)
        print(f"  [{lo:.2f}, {hi:.2f})  {cnt:>6}  "
              f"{cnt/len(confs_rf_only)*100:>5.1f}%  {bar}")

    # ------------------------------------------------------------------
    # SECTION 3 -- Threshold sensitivity table
    # ------------------------------------------------------------------
    print()
    print(SEP2)
    print("SECTION 3 -- THRESHOLD SENSITIVITY ANALYSIS")
    print(SEP2)
    print()

    # IF-only threats (legacy + current policy — these don't change with RF threshold)
    if_only_threats = sum(1 for p in rf_nrm_if_ano if p["threat"])

    # RF+IF threats (always 100% flagged regardless of threshold — both models agree)
    rf_and_if_total = len(rf_atk_if_ano)

    header = (f"{'Threshold':>10}  "
              f"{'RF-only above':>14}  {'RF-only %':>10}  "
              f"{'RF+IF above':>12}  {'RF+IF %':>8}  "
              f"{'Total threats':>14}  {'% of all preds':>15}")
    print(header)
    print("-" * 90)

    rows_for_report = []
    for t in THRESHOLDS:
        rf_only_above  = sum(1 for c in confs_rf_only  if c >= t)
        rf_and_if_above = sum(1 for c in confs_rf_and_if if c >= t)

        rf_only_pct    = rf_only_above  / len(confs_rf_only)  * 100 if confs_rf_only else 0
        rf_and_if_pct  = rf_and_if_above / rf_and_if_total * 100 if rf_and_if_total else 0

        total_threats  = rf_only_above + rf_and_if_above + if_only_threats
        pct_of_all     = total_threats / total_n * 100

        rows_for_report.append((t, rf_only_above, rf_only_pct,
                                  rf_and_if_above, rf_and_if_pct,
                                  total_threats, pct_of_all))

        print(f"  >= {t:.2f}    "
              f"{rf_only_above:>6} / {len(confs_rf_only):<5}  {rf_only_pct:>8.1f}%  "
              f"{rf_and_if_above:>5} / {rf_and_if_total:<4}  {rf_and_if_pct:>6.1f}%  "
              f"{total_threats:>8}           {pct_of_all:>8.2f}%")

    print()
    print(f"  (IF-only threats included in total but constant at: {if_only_threats})")

    # ------------------------------------------------------------------
    # SECTION 4 -- Detailed breakdown per threshold
    # ------------------------------------------------------------------
    print()
    print(SEP2)
    print("SECTION 4 -- DETAILED BREAKDOWN PER THRESHOLD")
    print(SEP2)

    for t, rf_only_above, rf_only_pct, rf_and_if_above, rf_and_if_pct, total_threats, pct_of_all in rows_for_report:
        rf_only_suppressed = len(confs_rf_only)  - rf_only_above
        print()
        print(f"  THRESHOLD >= {t:.2f}")
        print(f"  {'A) RF=attack + IF=normal  (RF-only)':}")
        print(f"     Total in bucket     : {len(confs_rf_only)}")
        print(f"     ABOVE threshold     : {rf_only_above}  ({rf_only_pct:.1f}%)  -> THREAT")
        print(f"     Below threshold     : {rf_only_suppressed}  -> suppressed (no alert)")
        print(f"  {'B) RF=attack + IF=anomaly (RF+IF)  ':}")
        print(f"     Total in bucket     : {rf_and_if_total}")
        print(f"     ABOVE threshold     : {rf_and_if_above}  ({rf_and_if_pct:.1f}%)  -> THREAT")
        print(f"  {'C) Combined':}")
        print(f"     Total threats       : {total_threats}  "
              f"({pct_of_all:.2f}% of all {total_n} predictions)")
        print(f"     False positives eliminated vs current (>=0.80): "
              f"{rows_for_report[2][1] - rf_only_above} fewer RF-only threats")

    # ------------------------------------------------------------------
    # SECTION 5 -- 20 flows closest to each boundary
    # ------------------------------------------------------------------
    boundaries = [0.80, 0.85, 0.90, 0.95, 0.98]

    print()
    print(SEP2)
    print("SECTION 5 -- RF-ONLY FLOWS NEAREST EACH BOUNDARY (10 below + 10 above)")
    print(SEP2)

    for boundary in boundaries:
        # All RF-only flows sorted by confidence
        sorted_rf_only = sorted(rf_atk_if_nrm, key=lambda p: p["confidence"])
        below = [p for p in sorted_rf_only if p["confidence"] < boundary][-10:]
        above = [p for p in sorted_rf_only if p["confidence"] >= boundary][:10]

        print()
        print(f"  Boundary: {boundary:.2f}")
        print(f"  -- 10 BELOW {boundary:.2f} (would be suppressed) --")
        if below:
            print(f"  {'Conf':>6}  {'Src':<16}  {'Dst':<16}  {'run_id'}")
            for p in reversed(below):
                print(f"  {p['confidence']:>6.3f}  {str(p['source_ip']):<16}  "
                      f"{str(p['dest_ip']):<16}  {p['run_id']}")
        else:
            print("  (none below this boundary)")

        print(f"  -- 10 ABOVE {boundary:.2f} (would be flagged as threat) --")
        if above:
            print(f"  {'Conf':>6}  {'Src':<16}  {'Dst':<16}  {'run_id'}")
            for p in above:
                print(f"  {p['confidence']:>6.3f}  {str(p['source_ip']):<16}  "
                      f"{str(p['dest_ip']):<16}  {p['run_id']}")
        else:
            print("  (none above this boundary)")

    # ------------------------------------------------------------------
    # SECTION 6 -- Confidence of current threats vs suppressed at 0.80
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 6 -- CURRENT THREATS (RF-only, conf >= 0.80): SOURCE IP MIX")
    print(SEP)

    current_threats_rf_only = [p for p in rf_atk_if_nrm if p["confidence"] >= 0.80]
    src_dist = {}
    for p in current_threats_rf_only:
        ip = p["source_ip"] or "unknown"
        src_dist[ip] = src_dist.get(ip, 0) + 1

    print(f"  Total RF-only threats at current >= 0.80 : {len(current_threats_rf_only)}")
    print(f"  Source IP breakdown:")
    for ip, cnt in sorted(src_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"    {ip:<22}  {cnt:>5} flows ({cnt/len(current_threats_rf_only)*100:.1f}%)")

    # ------------------------------------------------------------------
    # SECTION 7 -- Suppressed flows at each threshold: what do we give up?
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 7 -- FLOWS SUPPRESSED BY RAISING THRESHOLD: SOURCE IP MIX")
    print(SEP)

    base_threshold = 0.80
    base_set = set(p["id"] for p in rf_atk_if_nrm if p["confidence"] >= base_threshold)

    for t in [0.85, 0.90, 0.95]:
        new_set  = set(p["id"] for p in rf_atk_if_nrm if p["confidence"] >= t)
        dropped  = [p for p in rf_atk_if_nrm
                    if p["id"] in base_set and p["id"] not in new_set]

        src_d = {}
        for p in dropped:
            ip = p["source_ip"] or "unknown"
            src_d[ip] = src_d.get(ip, 0) + 1

        print(f"\n  Raising 0.80 -> {t:.2f}: drops {len(dropped)} RF-only threats")
        for ip, cnt in sorted(src_d.items(), key=lambda x: x[1], reverse=True):
            print(f"    {ip:<22}  {cnt:>5} flows ({cnt/len(dropped)*100:.1f}% of dropped)")

    # ------------------------------------------------------------------
    # SECTION 8 -- RF+IF anomaly confidence (these should always be threats)
    # ------------------------------------------------------------------
    print()
    print(SEP)
    print("SECTION 8 -- RF+IF ANOMALY FLOWS (always threat, verify confidence range)")
    print(SEP)

    print(f"  Count: {len(rf_atk_if_ano)}")
    print(f"  These should remain threats at ANY threshold we choose.")
    if rf_atk_if_ano:
        sorted_both = sorted(rf_atk_if_ano, key=lambda p: p["confidence"])
        print(f"  Confidence range: {sorted_both[0]['confidence']:.3f} "
              f"to {sorted_both[-1]['confidence']:.3f}")
        print(f"  Lowest-confidence RF+IF flows:")
        for p in sorted_both[:5]:
            print(f"    conf={p['confidence']:.3f}  {p['source_ip']}  ->  {p['dest_ip']}  "
                  f"run: {p['run_id']}")

    con.close()

    # ------------------------------------------------------------------
    # Final recommendation
    # ------------------------------------------------------------------
    print()
    print(SEP2)
    print("FINAL RECOMMENDATION (read-only — NOT yet implemented)")
    print(SEP2)
    print("""
  Based on the threshold sensitivity analysis:

  The key question is: at what confidence does the RF-only bucket
  produce genuine attacks vs ordinary Wi-Fi background traffic?

  The source IP mix of current threats (>=0.80) will show whether
  flows suppressed by raising the threshold are from the Sentinel PC
  itself (false positives) or from genuinely suspicious external IPs.

  Review the output of Sections 6 and 7 above to see which IPs are
  dropped at each candidate threshold, then derive the recommendation.
    """)
    print(SEP2)
    print("Diagnostic complete. NO data was modified.")
    print(SEP2)


if __name__ == "__main__":
    main()
