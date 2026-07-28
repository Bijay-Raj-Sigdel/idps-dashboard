import glob
import os
import pandas as pd
import joblib

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

# 1. Importing established preprocessing function
from ml.preprocessing import load_and_preprocess

#  relative path to project root
RAW_DATA_DIR = os.path.join("data", "raw")
OUTPUT_ML_DIR = "ml"


def get_combined_dataset(data_dir: str) -> pd.DataFrame:
    """Discovers, processes, and merges all CSV raw files into one DataFrame."""
    csv_paths = sorted(glob.glob(os.path.join(data_dir, "*.csv")))

    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in {data_dir}/")

    print(f"Found {len(csv_paths)} CSV file(s). Processing...")

    df_list = []
    for path in csv_paths:
        fname = os.path.basename(path)
        try:
            df = load_and_preprocess(path)
            df_list.append(df)
            print(f"  [SUCCESS] {fname} | Rows: {df.shape[0]}")
        except Exception as e:
            print(f"  [ERROR] Skipping {fname}: {e}")

    if not df_list:
        raise ValueError("No dataframes were successfully loaded.")

    print("Concatenating datasets...")
    return pd.concat(df_list, ignore_index=True)


def main():
    # 2. Loading the entire dataset
    try:
        dataset = get_combined_dataset(RAW_DATA_DIR)
        print(f"\nFinal dataset ready. Total Shape: {dataset.shape}")
    except Exception as e:
        print(f"Training initialization failed: {e}")
        return

    # 3. Separate features (X) and target (y)
    X = dataset.drop(columns=["Label"])
    y = dataset["Label"]

    print("Data Split COnfirmation")
    print(f"Features shape (X): {X.shape}")
    print(f"Target shape (y): {y.shape}")
    print(f"Unique classes in y: {y.nunique()}")

    print("Ready for train/test split, encoding, and model fitting.")

    # 4 Initializing the LableEncoder
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    print("Label Encoding Mapping")
    for index, class_name in enumerate(label_encoder.classes_):
        print(f"{index} -> {class_name}")

    print(f"Target encoded successfully. Sample Values: {y_encoded[:5]}")


    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size = 0.2,
        stratify = y_encoded,
        random_state=42
    )

    print("=== Stratified Split Complete ===")
    print(f"Train features shape: {X_train.shape} | Test features shape: {X_test.shape}")
    print(f"Train target shape:   {y_train.shape}   | Test target shape:   {y_test.shape}")

    print("=== Test Set Class Distribution ===")
    print(pd.Series(y_test).value_counts().sort_index())

    # 5. Compute sample weights for the training set
    # This handles the severe class imbalance by weighting the loss function
    print("Computing balanced sample weights for training.")
    sample_weights = compute_sample_weight(class_weight="balanced", y=y_train)

    # 6. Initialize the Baseline Random Forest Classifier
    # Setting n_jobs=-1 to utilize all CPU cores for faster training
    rf_model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        n_jobs=-1,
        verbose=0
    )
    rf_model.fit(X_train, y_train, sample_weight=sample_weights)
    y_pred_rf = rf_model.predict(X_test)

    # 7. Train XGBoost Model
    print("\nTraining XGBoost model...")
    print("Training complete!")# multi:softprob handles multi-class targets elegantly
    xgb_model = XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1,
        objective="multi:softprob",
    )
    xgb_model.fit(X_train, y_train, sample_weight=sample_weights)
    y_pred_xgb = xgb_model.predict(X_test)


    # 8. Compare Models (Primary Metric: Macro-F1)
    print("\n=== Evaluating Performance Metrics ===")
    rf_macro_f1 = f1_score(y_test, y_pred_rf, average="macro")
    xgb_macro_f1 = f1_score(y_test, y_pred_xgb, average="macro")

    print(f"Random Forest Macro-F1:       {rf_macro_f1:.4f}")
    print(f"XGBoost Classifier Macro-F1: {xgb_macro_f1:.4f}")

    # Determine winning model programmatically
    if xgb_macro_f1 > rf_macro_f1:
        winning_model = xgb_model
        winner_name = "XGBoost"
        winning_score = xgb_macro_f1
    else:
        winning_model = rf_model
        winner_name = "Random Forest"
        winning_score = rf_macro_f1

    print(f"\n WINNER SELECTED: {winner_name} (Macro-F1: {winning_score:.4f})")

    # Generate full reports
    rf_report = classification_report(
        y_test, y_pred_rf, target_names=label_encoder.classes_, digits=4
    )
    xgb_report = classification_report(
        y_test, y_pred_xgb, target_names=label_encoder.classes_, digits=4
    )

    # Print winning report to console
    print(f"\n=== Classification Report for Winner ({winner_name}) ===")
    print(xgb_report if winner_name == "XGBoost" else rf_report)
    joblib.dump(rf_model, "ml/model_rf.pkl")

    # Persist metrics to .txt files for version control/README documentation
    rf_metrics_path = os.path.join(OUTPUT_ML_DIR, "metrics_rf.txt")
    xgb_metrics_path = os.path.join(OUTPUT_ML_DIR, "metrics_xgb.txt")

    with open(rf_metrics_path, "w") as f:
        f.write(
            f"Random Forest Baseline Evaluation\nMacro-F1: {rf_macro_f1:.4f}\n\n"
        )
        f.write(rf_report)

    with open(xgb_metrics_path, "w") as f:
        f.write(f"XGBoost Evaluation\nMacro-F1: {xgb_macro_f1:.4f}\n\n")
        f.write(xgb_report)

    print(f"  [SAVED] Performance logs -> metrics_rf.txt and metrics_xgb.txt")

    # 9. Serialize Production Artifacts
    print(f"\nSerializing training production artifacts to {OUTPUT_ML_DIR}...")

    # Save winning model
    model_path = os.path.join(OUTPUT_ML_DIR, "model.pkl")
    joblib.dump(winning_model, model_path)
    print(f"  [SAVED] Winning Model Engine -> {model_path}")

    # Save label encoder
    encoder_path = os.path.join(OUTPUT_ML_DIR, "label_encoder.pkl")
    joblib.dump(label_encoder, encoder_path)
    print(f"  [SAVED] Label Encoder Object -> {encoder_path}")


    # Save preprocessing structural metadata
    pipeline_metadata = {
        "expected_features": list(X_train.columns),
        "feature_count": X_train.shape[1],
    }
    metadata_path = os.path.join(OUTPUT_ML_DIR, "preprocessing_metadata.pkl")
    joblib.dump(pipeline_metadata, metadata_path)
    print(f"  [SAVED] Feature Metadata Schema -> {metadata_path}")

    print("\nTraining workflow fully resolved. Project ready for API hookup.")


if __name__ == "__main__":
    main()
