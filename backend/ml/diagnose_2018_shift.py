"""
Diagnoses WHY the RF model gets 0.0000 recall on certain attack classes
when tested on CSE-CIC-IDS2018 data.

For each zero-recall class from metrics_2018_cross_test.txt, this pulls
every true sample of that class, runs predict_proba, and reports:
  - the average probability the model assigned to the TRUE class
  - the average probability the model assigned to BENIGN
  - what class the model predicted instead, most often

Run from backend/ml/ (same folder as model.pkl, label_encoder.pkl,
preprocessing_metadata.pkl, and cicids2018_simulation.csv).
"""

import os
import joblib
import pandas as pd
import numpy as np
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "label_encoder.pkl")
METADATA_PATH = os.path.join(BASE_DIR, "preprocessing_metadata.pkl")
DATA_PATH = os.path.join(BASE_DIR, "cicids2018_simulation.csv")

# Classes that came back at 0.0000 recall in metrics_2018_cross_test.txt
ZERO_RECALL_CLASSES = [
    "Bot",
    "DDoS",
    "DoS Hulk",
    "DoS Slowhttptest",
    "Infiltration",
    "SSH-Patator",
    "Web Attack - Brute Force",
    "Web Attack - Sql Injection",
    "Web Attack - XSS",
]


def main():
    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(ENCODER_PATH)
    metadata = joblib.load(METADATA_PATH)
    expected_features = metadata["expected_features"]

    df = pd.read_csv(DATA_PATH)

    # Figure out which column holds the true label
    label_col = "Label" if "Label" in df.columns else "attack_type"
    class_to_idx = {c: i for i, c in enumerate(label_encoder.classes_)}

    print(f"{'Class':<28}{'n':>6}{'P(true class)':>16}{'P(BENIGN)':>12}   Most common wrong prediction")
    print("-" * 100)

    for cls in ZERO_RECALL_CLASSES:
        subset = df[df[label_col] == cls]
        if subset.empty:
            print(f"{cls:<28}{'--':>6}   (no samples found in this file — check label spelling)")
            continue

        X = subset[expected_features]
        probs = model.predict_proba(X)  # shape: (n_samples, n_classes)

        true_idx = class_to_idx.get(cls)
        benign_idx = class_to_idx.get("BENIGN")

        avg_true_prob = probs[:, true_idx].mean() if true_idx is not None else float("nan")
        avg_benign_prob = probs[:, benign_idx].mean() if benign_idx is not None else float("nan")

        predicted_idx = probs.argmax(axis=1)
        predicted_labels = label_encoder.inverse_transform(predicted_idx)
        top_wrong = Counter(predicted_labels).most_common(1)[0]

        print(
            f"{cls:<28}{len(subset):>6}{avg_true_prob:>16.4f}{avg_benign_prob:>12.4f}   "
            f"{top_wrong[0]} ({top_wrong[1]}/{len(subset)})"
        )

    print("\nHow to read this:")
    print("- P(true class) near 0 (e.g. < 0.05) across the board = genuine distribution")
    print("  collapse. The model isn't 'close' — the 2018 feature values for this class")
    print("  don't look like anything it saw in 2017 training. Needs retraining with")
    print("  2018 data blended in, not a threshold tweak.")
    print("- P(true class) moderate (e.g. 0.15-0.40) but still losing to BENIGN/another")
    print("  class = a threshold/calibration issue. Could improve with per-class")
    print("  threshold tuning or better class weighting, without a full retrain.")


if __name__ == "__main__":
    main()