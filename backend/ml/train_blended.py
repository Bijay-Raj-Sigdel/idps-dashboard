import glob
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from ml.preprocessing import load_and_preprocess

RAW_DATA_DIR = os.path.join("data", "raw")
DATA_2018_PATH = os.path.join("ml", "cicids2018_simulation.csv")
OUTPUT_ML_DIR = "ml"

HOLDOUT_FRAC = 0.30  # portion of 2018 data NEVER used in training


def get_combined_2017_dataset(data_dir: str) -> pd.DataFrame:
    """Same loader as train.py: discovers, processes, and merges the raw 2017 CSVs."""
    csv_paths = sorted(glob.glob(os.path.join(data_dir, "*.csv")))
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in {data_dir}/")

    df_list = []
    for path in csv_paths:
        fname = os.path.basename(path)
        try:
            df_list.append(load_and_preprocess(path))
            print(f"  [SUCCESS] {fname}")
        except Exception as e:
            print(f"  [ERROR] Skipping {fname}: {e}")

    if not df_list:
        raise ValueError("No 2017 dataframes were successfully loaded.")
    return pd.concat(df_list, ignore_index=True)


def split_2018_holdout(random_state: int = 42):
    """
    Splits cicids2018_simulation.csv into two disjoint, stratified slices:
      - train_slice: folded into training alongside 2017 data
      - holdout_slice: NEVER touched during training, used only for the
        final "does this generalize" evaluation
    """
    df_2018 = pd.read_csv(DATA_2018_PATH)
    df_2018["Label"] = df_2018["Label"].str.strip()

    train_slice, holdout_slice = train_test_split(
        df_2018,
        test_size=HOLDOUT_FRAC,
        stratify=df_2018["Label"],
        random_state=random_state,
    )
    return train_slice.reset_index(drop=True), holdout_slice.reset_index(drop=True)


def main():
    print("Loading 2017 dataset...")
    df_2017 = get_combined_2017_dataset(RAW_DATA_DIR)
    print(f"2017 dataset: {df_2017.shape}")

    print(f"\nSplitting 2018 data ({int((1 - HOLDOUT_FRAC) * 100)}% train-blend / "
          f"{int(HOLDOUT_FRAC * 100)}% holdout, stratified)...")
    df_2018_train, df_2018_holdout = split_2018_holdout()
    print(f"2018 train-blend slice: {df_2018_train.shape}")
    print(f"2018 holdout slice (never trained on): {df_2018_holdout.shape}")

    holdout_path = os.path.join(OUTPUT_ML_DIR, "cicids2018_holdout.csv")
    df_2018_holdout.to_csv(holdout_path, index=False)
    print(f"  [SAVED] 2018 holdout set -> {holdout_path}")

    combined = pd.concat([df_2017, df_2018_train], ignore_index=True)
    print(f"\nCombined training pool (2017 full + 2018 train-blend): {combined.shape}")

    X = combined.drop(columns=["Label"])
    y = combined["Label"]

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, stratify=y_encoded, random_state=42
    )
    print(f"Train: {X_train.shape} | Test (combined held-out 20%): {X_test.shape}")

    print("\nComputing balanced sample weights...")
    sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)

    print("Training Random Forest...")
    rf_model = RandomForestClassifier(n_estimators=40, max_depth=40, min_samples_leaf=5, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train, sample_weight=sample_weights)
    y_pred_rf = rf_model.predict(X_test)
    rf_macro_f1 = f1_score(y_test, y_pred_rf, average="macro")

    print("Training XGBoost...")
    xgb_model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1,
        objective="multi:softprob",
    )
    xgb_model.fit(X_train, y_train, sample_weight=sample_weights)
    y_pred_xgb = xgb_model.predict(X_test)
    xgb_macro_f1 = f1_score(y_test, y_pred_xgb, average="macro")

    print(f"\nRF Macro-F1:  {rf_macro_f1:.4f}")
    print(f"XGB Macro-F1: {xgb_macro_f1:.4f}")

    if xgb_macro_f1 > rf_macro_f1:
        winning_model, winner_name, winning_score = xgb_model, "XGBoost", xgb_macro_f1
        y_pred_winner = y_pred_xgb
    else:
        winning_model, winner_name, winning_score = rf_model, "Random Forest", rf_macro_f1
        y_pred_winner = y_pred_rf

    print(f"WINNER: {winner_name} (Macro-F1: {winning_score:.4f})")

    combined_test_report = classification_report(
        y_test, y_pred_winner,
        target_names=label_encoder.classes_, digits=4, zero_division=0,
    )
    with open(os.path.join(OUTPUT_ML_DIR, "metrics_blended_combined_test.txt"), "w") as f:
        f.write("Blended Model Evaluation (2017 + 2018-train, 20% combined held-out test)\n")
        f.write(f"Winner: {winner_name} | Macro-F1: {winning_score:.4f}\n\n")
        f.write(combined_test_report)
    print("[SAVED] metrics_blended_combined_test.txt")

    # --- The real test: performance on the 2018 slice the model NEVER saw ---
    print("\nEvaluating on the untouched 2018 holdout slice...")
    X_holdout = df_2018_holdout[list(X_train.columns)]
    y_holdout_labels = df_2018_holdout["Label"]

    known_classes = set(label_encoder.classes_)
    valid_mask = y_holdout_labels.isin(known_classes)
    if not valid_mask.all():
        dropped = (~valid_mask).sum()
        print(f"[WARN] Dropping {dropped} holdout rows with labels unseen in training.")
        X_holdout = X_holdout[valid_mask]
        y_holdout_labels = y_holdout_labels[valid_mask]

    y_holdout = label_encoder.transform(y_holdout_labels)
    y_pred_holdout = winning_model.predict(X_holdout)
    holdout_acc = float((y_pred_holdout == y_holdout).mean())

    holdout_report = classification_report(
        y_holdout, y_pred_holdout,
        labels=list(range(len(label_encoder.classes_))),
        target_names=label_encoder.classes_, digits=4, zero_division=0,
    )
    with open(os.path.join(OUTPUT_ML_DIR, "metrics_blended_2018_holdout.txt"), "w") as f:
        f.write("Blended Model — 2018 Holdout Evaluation (never trained on, "
                 f"{int(HOLDOUT_FRAC * 100)}% stratified slice)\n")
        f.write(f"Overall Accuracy: {holdout_acc:.4f}\n\n")
        f.write(holdout_report)
    print(f"[SAVED] metrics_blended_2018_holdout.txt (accuracy: {holdout_acc:.4f})")

    # --- Persist artifacts under _blended names — does NOT touch production model.pkl ---
    joblib.dump(winning_model, os.path.join(OUTPUT_ML_DIR, "model_blended.pkl"))
    joblib.dump(label_encoder, os.path.join(OUTPUT_ML_DIR, "label_encoder_blended.pkl"))
    pipeline_metadata = {
        "expected_features": list(X_train.columns),
        "feature_count": X_train.shape[1],
    }
    joblib.dump(pipeline_metadata, os.path.join(OUTPUT_ML_DIR, "preprocessing_metadata_blended.pkl"))
    print("\n[SAVED] model_blended.pkl, label_encoder_blended.pkl, preprocessing_metadata_blended.pkl")

    print("\nDone. Compare metrics_blended_2018_holdout.txt against your existing")
    print("metrics_2018_cross_test.txt (zero-shot) to quantify the generalization gain.")


if __name__ == "__main__":
    main()