import glob
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split

from ml.preprocessing import load_and_preprocess

RAW_DATA_DIR = os.path.join("data", "raw")
DATA_2018_PATH = os.path.join("ml", "cicids2018_simulation.csv")
HOLDOUT_2018_PATH = os.path.join("ml", "cicids2018_holdout.csv")
OUTPUT_ML_DIR = "ml"

HOLDOUT_FRAC = 0.30  # must match train_blended.py so the 2018 split is identical
RANDOM_STATE = 42

# Classes the multi-class classifier still misses even after blending
# (see metrics_blended_2018_holdout.txt) — this is what the anomaly
# detector needs to catch instead.
TARGET_HARD_CLASSES = [
    "Infiltration",
    "Web Attack - Brute Force",
    "Web Attack - Sql Injection",
    "Web Attack - XSS",
]


def get_combined_2017_dataset(data_dir: str) -> pd.DataFrame:
    csv_paths = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in {data_dir}/")
    df_list = []
    for path in csv_paths:
        df_list.append(load_and_preprocess(path))
    return pd.concat(df_list, ignore_index=True)


def get_2018_train_slice() -> pd.DataFrame:
    """Reproduces the exact same 70% train-blend slice train_blended.py used
    (same file, same random_state) — the other 30% is the untouched holdout
    already saved at ml/cicids2018_holdout.csv, which we evaluate against."""
    df_2018 = pd.read_csv(DATA_2018_PATH)
    df_2018["Label"] = df_2018["Label"].str.strip()
    train_slice, _ = train_test_split(
        df_2018,
        test_size=HOLDOUT_FRAC,
        stratify=df_2018["Label"],
        random_state=RANDOM_STATE,
    )
    return train_slice.reset_index(drop=True)


def main():
    print("Loading 2017 dataset...")
    df_2017 = get_combined_2017_dataset(RAW_DATA_DIR)

    print("Reproducing 2018 train-blend slice...")
    df_2018_train = get_2018_train_slice()

    combined = pd.concat([df_2017, df_2018_train], ignore_index=True)
    feature_cols = [c for c in combined.columns if c != "Label"]

    # --- Train ONLY on BENIGN traffic — the detector learns "what normal looks like" ---
    benign_only = combined[combined["Label"] == "BENIGN"]
    print(f"Training Isolation Forest on {len(benign_only)} BENIGN samples "
          f"(dropped {len(combined) - len(benign_only)} attack rows from training pool)...")

    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=0.05,  # assume ~1% of "normal-looking" traffic is still noise
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    iso_forest.fit(benign_only[feature_cols])

    joblib.dump(iso_forest, os.path.join(OUTPUT_ML_DIR, "anomaly_model.pkl"))
    joblib.dump({"expected_features": feature_cols},
                os.path.join(OUTPUT_ML_DIR, "anomaly_metadata.pkl"))
    print("[SAVED] anomaly_model.pkl, anomaly_metadata.pkl")

    # --- Evaluate on the untouched 2018 holdout — same data the blended classifier was tested on ---
    print("\nEvaluating on the 2018 holdout slice...")
    df_holdout = pd.read_csv(HOLDOUT_2018_PATH)
    df_holdout["Label"] = df_holdout["Label"].str.strip()

    predictions = iso_forest.predict(df_holdout[feature_cols])  # -1 = anomaly, 1 = normal
    df_holdout["flagged_anomaly"] = predictions == -1

    print("\n" + "=" * 70)
    print("  ANOMALY DETECTION RATE BY TRUE LABEL (2018 holdout)")
    print("=" * 70)
    print(f"{'Label':<30}{'n':>10}{'%% flagged anomaly':>22}")
    print("-" * 70)

    lines = []
    for label, group in df_holdout.groupby("Label"):
        flagged_pct = group["flagged_anomaly"].mean() * 100
        n = len(group)
        marker = "  <-- target class" if label in TARGET_HARD_CLASSES else ""
        line = f"{label:<30}{n:>10}{flagged_pct:>21.2f}%{marker}"
        print(line)
        lines.append(line)

    benign_fp_rate = df_holdout.loc[df_holdout["Label"] == "BENIGN", "flagged_anomaly"].mean() * 100

    report_path = os.path.join(OUTPUT_ML_DIR, "metrics_anomaly_detection.txt")
    with open(report_path, "w") as f:
        f.write("Isolation Forest Anomaly Detection — evaluated on 2018 holdout slice\n")
        f.write("Trained on BENIGN-only traffic from the combined 2017 + 2018-train pool\n")
        f.write(f"BENIGN false-positive rate: {benign_fp_rate:.2f}%\n\n")
        f.write(f"{'Label':<30}{'n':>10}{'%% flagged anomaly':>22}\n")
        f.write("-" * 70 + "\n")
        f.write("\n".join(lines))

    print(f"\n[SAVED] {report_path}")
    print(f"\nBENIGN false-positive rate: {benign_fp_rate:.2f}% "
          "(this is your cost — how much normal traffic gets flagged for nothing)")
    print("\nHow to read this: for the 4 target classes above, a high %% flagged")
    print("means the anomaly detector catches traffic the classifier calls BENIGN.")
    print("A useful detector needs BOTH a high flag rate on the target classes")
    print("AND a low BENIGN false-positive rate — otherwise it just adds noise.")


if __name__ == "__main__":
    main()