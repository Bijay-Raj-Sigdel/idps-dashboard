import os
import joblib
import pandas as pd
from typing import Dict, Any, List

#Defining the relative path to backend/ root directory

ML_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","ml")

MODEL_PATH = os.path.join(ML_DIR, "model.pkl")
ENCODER_PATH = os.path.join(ML_DIR, "label_encoder.pkl")
METADATA_PATH = os.path.join(ML_DIR, "preprocessing_metadata.pkl")

class ModelHandler:
    """ Handles Loading artiacts, input feature validation and model inference."""

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.expected_features: List[str] = []
        self.feature_count: int = 0
        self.load_artifacts()

    def load_artifacts(self):
        """Loads seraialized model, encoder adn metadata from disk."""

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not file missing at {MODEL_PATH}")
        if not os.path.exists(ENCODER_PATH):
            raise FileNotFoundError(f"Label encoder file missing at {ENCODER_PATH}")
        if not os.path.exists(METADATA_PATH):
            raise FileNotFoundError(f"Preprocessing metadata file missing at {METADATA_PATH}")

        self.model = joblib.load(MODEL_PATH)
        self.label_encoder = joblib.load(ENCODER_PATH)

        metadata = joblib.load(METADATA_PATH)
        self.expected_features = metadata["expected_features"]
        self.feature_count = metadata["feature_count"]

        print(f"[SUCESS] Inference engine loaded winning model ({type(self.model).__name__}) "
              f"with {self.feature_count} features.")

    def validate_features(self, payload: Dict[str, Any]):
        """ Validates that the incoming dictionary has all expected features."""
        missing = [f for f in self.expected_features if f not in payload]
        if missing:
            raise ValueError(f"Missing required features in payload: {missing}")

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a dict of features input, validated features, orders them correctly,
        runs model inference and returns prediction details.
        """
        self.validate_features(payload)

        input_df = pd.DataFrame([payload])[self.expected_features]

        pred_idx = self.model.predict(input_df)[0]

        # Softmax probabilities if supported
        probabilities = None
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(input_df)[0]
            probabilities = {
                cls_name: float(probs[i])
                for i, cls_name in enumerate(self.label_encoder.classes_)
            }

        predicted_label = str(self.label_encoder.inverse_transform([pred_idx])[0])

        return{
            "prediction": predicted_label,
            "prediction_id": int(pred_idx),
            "confidence": (float(probabilities[predicted_label]) if probabilities else None),
            "probabilities": probabilities,
        }

    def get_feature_importance(self) -> List[Dict[str, Any]]:
        """
        Pairs model feature_importances_ with expected_features 
        and returns them sorted descending by importance.
        """
        if self.model is None or not hasattr(self.model, "feature_importances_"):
            return []

        importances = self.model.feature_importances_
            
        feature_importance_list = [
            {
                "feature": feature,
                "importance": float(importance)
            }
            for feature, importance in zip(self.expected_features, importances)
        ]

        # Sort descending by importance score
        feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)
        return feature_importance_list

model_handler = ModelHandler()