"""
Sends real, labeled CICIDS2017 rows through the live /predict endpoint to
sanity-check the deployed model against known ground truth — as opposed to
simulate_traffic.py's synthetic "attack-like" values, which may not actually
resemble the traffic patterns the model was trained to recognize.

Usage:
    python test_attacks.py

Adjust DATA_DIR to point at the folder containing your 8 CICIDS2017 CSVs
(the same ones train.py consumes), and SAMPLES_PER_LABEL to control how many
rows of each attack type to test.
"""

import glob
import os
import random

import pandas as pd
import requests

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
URL = "http://127.0.0.1:8000/predict"
SAMPLES_PER_LABEL = 5

# The 15 raw column names the model expects (Matches schemas.py aliases)
FEATURES = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Packet Length Mean",
    "Packet Length Std",
    "Average Packet Size",
    "Active Mean",
    "Idle Mean",
]

# Labels worth specifically checking: strong classes as a sanity check,
# plus the known-weak classes from Week 1's confusion-matrix diagnostics.
LABELS_TO_TEST = [
    "DDoS",                          # strong class 
    "PortScan",                      # strong class 
    "Web Attack - Sql Injection",    # weak class
    "Web Attack - XSS",              # weak class
    "Web Attack - Brute Force",      # weak class
    "Bot",                           # weak class
]


def load_data():
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSVs found in {DATA_DIR} — update DATA_DIR")
    frames = [pd.read_csv(f, low_memory=False) for f in csv_files]
    df = pd.concat(frames, ignore_index=True)
    df.columns = df.columns.str.strip()  # CICIDS2017 columns often have leading spaces
    return df


def run_test():
    df = load_data()

    if "Label" not in df.columns:
        raise KeyError("Expected a 'Label' column after stripping whitespace — check your CSV headers")

    correct, total = 0, 0

    for label in LABELS_TO_TEST:
        subset = df[df["Label"] == label]
        if subset.empty:
            print(f"[SKIP] No rows found for label '{label}'")
            continue

        sample = subset.sample(n=min(SAMPLES_PER_LABEL, len(subset)), random_state=42)

        print(f"\n=== {label} ({len(sample)} samples) ===")
        for _, row in sample.iterrows():
            payload = {feat: float(row[feat]) for feat in FEATURES}
            try:
                res = requests.post(URL, json=payload, timeout=5)
                res.raise_for_status()
                data = res.json()
                predicted = data.get("prediction")
                confidence = data.get("confidence")
                match = "✓" if predicted == label else "✗"
                if predicted == label:
                    correct += 1
                total += 1
                print(f"  {match} actual={label:30s} predicted={predicted:30s} confidence={confidence:.3f}")
            except Exception as e:
                print(f"  [ERROR] {e}")

    if total:
        print(f"\nOverall match rate: {correct}/{total} ({correct/total:.1%})")


if __name__ == "__main__":
    run_test()