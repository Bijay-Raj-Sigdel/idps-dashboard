import os
import joblib
import pandas as pd
from typing import Dict, Any, List

ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml")

MODEL_PATH = os.path.join(ML_DIR, "model_blended.pkl")
ENCODER_PATH = os.path.join(ML_DIR, "label_encoder_blended.pkl")
METADATA_PATH = os.path.join(ML_DIR, "preprocessing_metadata_blended.pkl")

# Paths for anomaly detection artifacts
ANOMALY_MODEL_PATH = os.path.join(ML_DIR, "anomaly_model.pkl")
ANOMALY_METADATA_PATH = os.path.join(ML_DIR, "anomaly_metadata.pkl")


class ModelHandler:
    """Handles loading artifacts, input feature validation, classifier inference, and anomaly detection."""

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.anomaly_model = None
        self.anomaly_features: List[str] = []
        self.expected_features: List[str] = []
        self.feature_count: int = 0
        self.load_artifacts()

    def load_artifacts(self):
        """Loads serialized model, encoder, metadata, and anomaly artifacts from disk."""
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file missing at {MODEL_PATH}")
        if not os.path.exists(ENCODER_PATH):
            raise FileNotFoundError(f"Label encoder file missing at {ENCODER_PATH}")
        if not os.path.exists(METADATA_PATH):
            raise FileNotFoundError(f"Preprocessing metadata missing at {METADATA_PATH}")

        self.model = joblib.load(MODEL_PATH)
        self.label_encoder = joblib.load(ENCODER_PATH)

        metadata = joblib.load(METADATA_PATH)
        self.expected_features = metadata["expected_features"]
        self.feature_count = metadata["feature_count"]

        # Load Anomaly Detector artifacts if present
        if os.path.exists(ANOMALY_MODEL_PATH) and os.path.exists(ANOMALY_METADATA_PATH):
            self.anomaly_model = joblib.load(ANOMALY_MODEL_PATH)
            anomaly_meta = joblib.load(ANOMALY_METADATA_PATH)
            self.anomaly_features = anomaly_meta.get("expected_features", self.expected_features)
            print("[SUCCESS] Anomaly detection model loaded successfully.")
        else:
            print("[WARNING] Anomaly model artifacts missing. Anomaly checks will be skipped.")

        print(
            f"[SUCCESS] Inference engine loaded winning model ({type(self.model).__name__}) "
            f"with {self.feature_count} features."
        )

    def validate_features(self, payload: Dict[str, Any]):
        """Validates that the incoming dictionary has all expected features."""
        missing = [f for f in self.expected_features if f not in payload]
        if missing:
            raise ValueError(f"Missing required features in payload: {missing}")

    def detect_anomaly(self, input_df: pd.DataFrame) -> bool:
        """ 
        Runs the anomaly model on input features. 
        Returns True only for actual anomalies (-1). 
        """
        if self.anomaly_model is None:
            return False

        anomaly_df = input_df[self.anomaly_features]
        anomaly_pred = self.anomaly_model.predict(anomaly_df)[0]
        return bool(anomaly_pred == -1)

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a dict of features, validates them, orders them,
        runs main model inference and checks for anomalies on BENIGN flows.
        """
        self.validate_features(payload)

        input_df = pd.DataFrame([payload])[self.expected_features]
        pred_idx = self.model.predict(input_df)[0]

        probabilities = None
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(input_df)[0]
            probabilities = {
                cls_name: float(probs[i])
                for i, cls_name in enumerate(self.label_encoder.classes_)
            }

        predicted_label = str(self.label_encoder.inverse_transform([pred_idx])[0])

        # Run anomaly detection if predicted_label is BENIGN
        is_anomaly = False
        if predicted_label.upper() == "BENIGN":
            is_anomaly = self.detect_anomaly(input_df)

        return {
            "prediction": predicted_label,
            "prediction_id": int(pred_idx),
            "confidence": (float(probabilities[predicted_label]) if probabilities else None),
            "probabilities": probabilities,
            "is_anomaly": is_anomaly,
        }

    def get_feature_importance(self) -> List[Dict[str, Any]]:
        if self.model is None or not hasattr(self.model, "feature_importances_"):
            return []

        importances = self.model.feature_importances_
        feature_importance_list = [
            {"feature": feature, "importance": float(importance)}
            for feature, importance in zip(self.expected_features, importances)
        ]
        feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)
        return feature_importance_list


model_handler = ModelHandler()