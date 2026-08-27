import os
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# 1. Load trained artifacts (Trained on 2017 data via train.py)
MODEL_PATH = "ml/model.pkl"
ENCODER_PATH = "ml/label_encoder.pkl"
METADATA_PATH = "ml/preprocessing_metadata.pkl"
TEST_DATA_PATH = "ml/cicids2018_simulation.csv"

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model file missing. Please run `python ml/train.py` first.")

model = joblib.load(MODEL_PATH)
label_encoder = joblib.load(ENCODER_PATH)
metadata = joblib.load(METADATA_PATH)

expected_features = metadata["expected_features"]

# 2. Load 2018 Evaluation/Test Data
print(f"Loading 2018 test dataset from {TEST_DATA_PATH}...")
df_2018 = pd.read_csv(TEST_DATA_PATH)

# Extract features (X) and ground-truth string labels (y)
X_test = df_2018[expected_features]
y_true_labels = df_2018["Label"]

# Encode string ground-truth labels using the 2017 LabelEncoder
# (Filters out any classes not present during 2017 training)
known_classes = set(label_encoder.classes_)
valid_mask = y_true_labels.isin(known_classes)

if not valid_mask.all():
    dropped_count = (~valid_mask).sum()
    print(f"[WARN] Dropping {dropped_count} test rows with labels unseen during 2017 training.")
    X_test = X_test[valid_mask]
    y_true_labels = y_true_labels[valid_mask]

y_true = label_encoder.transform(y_true_labels)

# 3. Predict using 2017-trained model
print("Executing cross-dataset inference (2017 Model -> 2018 Test Data)...")
y_pred = model.predict(X_test)

# 4. Generate Accuracy and Performance Report
accuracy = accuracy_score(y_true, y_pred)
report = classification_report(
    y_true, 
    y_pred, 
    labels=list(range(len(label_encoder.classes_))),
    target_names=label_encoder.classes_, 
    digits=4, 
    zero_division=0
)

print("\n" + "=" * 55)
print("  CROSS-DATASET ACCURACY METRICS (2017 Train -> 2018 Test)  ")
print("=" * 55)
print(f"Overall Accuracy: {accuracy * 100:.2f}% ({accuracy:.4f})")
print(f"Total Test Samples: {len(X_test)}\n")
print("Classification Report:")
print(report)

# 5. Save report to disk
output_report_path = "ml/metrics_2018_cross_test.txt"
with open(output_report_path, "w") as f:
    f.write(f"Cross-Dataset Evaluation (Train: 2017 | Test: 2018)\n")
    f.write(f"Overall Accuracy: {accuracy:.4f}\n\n")
    f.write(report)

print(f"[SAVED] Evaluation metrics stored in '{output_report_path}'")