import os
import time
import requests
import pandas as pd

# URL of local FastAPI endpoint
URL = "http://127.0.0.1:8000/predict"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 1. Update path to point to 2018 simulation dataset
DATA_PATH = os.path.join(
    BASE_DIR, "..", "ml", "cicids2018_simulation.csv"
)


def run_simulation():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Processed dataset not found at {DATA_PATH}"
        )

    print(f"Loading dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    print("Starting Multi-Class Threat Simulator (2018 Data)...")
    while True:
        for index, row in df.iterrows():
            payload = row.to_dict()

            # Extract label and pass as ground truth
            label = payload.get("Label") or payload.get(
                "attack_type", "BENIGN"
            )
            payload["attack_type"] = str(label)

            # 2. Add data source tag
            payload["data_source"] = "CSE-CIC-IDS2018"

            try:
                res = requests.post(URL, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    sent_type = payload["attack_type"]
                    pred_type = data.get("prediction")
                    print(
                        f"[SENT] Sent: {sent_type:<25} | Pred: {pred_type}"
                    )
                else:
                    print(
                        f"[ERROR] HTTP {res.status_code}: {res.text}",
                        flush=True,
                    )
            except Exception as e:
                print(f"[ERROR] {e}", flush=True)

            time.sleep(0.3)


if __name__ == "__main__":
    run_simulation()