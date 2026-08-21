import os
import time
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from backend.ml.decision_tree_scratch import DecisionTreeScratch

# Path configurations
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "processed_data.csv")
ENCODER_PATH = os.path.join(BASE_DIR, "label_encoder.pkl")
RESULTS_PATH = os.path.join(BASE_DIR, "scratch_results.txt")


def load_and_subsample_data(
    sample_size: int = 10000, random_state: int = 42
):
    """Loads preprocessed dataset and applies stratified subsampling."""
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Processed dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # Separate target column
    if "Label" in df.columns:
        target_col = "Label"
    elif "attack_type" in df.columns:
        target_col = "attack_type"
    else:
        target_col = df.columns[-1]

    X = df.drop(columns=[target_col]).values
    y = df[target_col].values

    # Encode target labels using existing fitted encoder if available
    if os.path.exists(ENCODER_PATH):
        encoder = joblib.load(ENCODER_PATH)
        y = encoder.transform(y)

    # Perform stratified subsampling to keep runtime manageable
    if len(y) > sample_size:
        _, X_sample, _, y_sample = train_test_split(
            X,
            y,
            test_size=sample_size,
            stratify=y,
            random_state=random_state,
        )
    else:
        X_sample, y_sample = X, y

    return train_test_split(
        X_sample,
        y_sample,
        test_size=0.2,
        stratify=y_sample,
        random_state=random_state,
    )


def run_benchmark():
    print("Loading and subsampling data...")
    X_train, X_test, y_train, y_test = load_and_subsample_data(
        sample_size=10000
    )

    max_depth = 8
    min_samples_split = 10

    # 1. Benchmark Custom Scratch Decision Tree
    print("\nTraining DecisionTreeScratch...")
    scratch_tree = DecisionTreeScratch(
        max_depth=max_depth, min_samples_split=min_samples_split
    )

    start_scratch = time.time()
    scratch_tree.fit(X_train, y_train)
    scratch_train_time = time.time() - start_scratch

    scratch_preds = scratch_tree.predict(X_test)
    scratch_acc = accuracy_score(y_test, scratch_preds)
    scratch_f1 = f1_score(y_test, scratch_preds, average="macro")

    # 2. Benchmark Scikit-Learn Decision Tree
    print("Training sklearn DecisionTreeClassifier...")
    sklearn_tree = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        random_state=42,
    )

    start_sklearn = time.time()
    sklearn_tree.fit(X_train, y_train)
    sklearn_train_time = time.time() - start_sklearn

    sklearn_preds = sklearn_tree.predict(X_test)
    sklearn_acc = accuracy_score(y_test, sklearn_preds)
    sklearn_f1 = f1_score(y_test, sklearn_preds, average="macro")

    # 3. Format and Output Results
    results_header = (
        f"{'Model':<24} | {'Train Time (s)':<14} | {'Accuracy':<10} | {'Macro-F1':<10}\n"
        + "-" * 67
    )
    scratch_row = f"{'DecisionTreeScratch':<24} | {scratch_train_time:<14.4f} | {scratch_acc:<10.4f} | {scratch_f1:<10.4f}"
    sklearn_row = f"{'sklearn DecisionTree':<24} | {sklearn_train_time:<14.4f} | {sklearn_acc:<10.4f} | {sklearn_f1:<10.4f}"

    report = f"{results_header}\n{scratch_row}\n{sklearn_row}"

    print("\nBenchmark Results:")
    print(report)

    # Save output report
    with open(RESULTS_PATH, "w") as f:
        f.write(report)

    print(f"\nResults successfully saved to {RESULTS_PATH}")


if __name__ == "__main__":
    run_benchmark()