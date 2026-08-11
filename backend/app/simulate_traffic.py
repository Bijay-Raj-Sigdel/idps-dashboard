import time
import random
import requests

# URL of your local FastAPI endpoint
URL = "http://127.0.0.1:8000/predict"

# Base sample payload matching your 15 features
def generate_mock_flow():
    is_attack = random.random() < 0.3  # 30% chance of threat traffic
    
    return {
        "Active Mean": round(random.uniform(0, 500 if is_attack else 10), 2),
        "Average Packet Size": random.randint(200, 1200) if is_attack else random.randint(40, 150),
        "Bwd Packet Length Mean": random.randint(100, 800),
        "Destination Port": random.choice([80, 443, 22, 8080, 21]),
        "Flow Bytes/s": random.randint(5000, 500000) if is_attack else random.randint(100, 2000),
        "Flow Duration": random.randint(100, 10000),
        "Flow Packets/s": random.randint(50, 1000) if is_attack else random.randint(1, 20),
        "Fwd Packet Length Mean": random.randint(20, 200),
        "Idle Mean": 0,
        "Packet Length Mean": random.randint(50, 500),
        "Packet Length Std": round(random.uniform(5, 50), 2),
        "Total Backward Packets": random.randint(1, 50),
        "Total Fwd Packets": random.randint(1, 50),
        "Total Length of Bwd Packets": random.randint(100, 5000),
        "Total Length of Fwd Packets": random.randint(100, 5000)
    }

def run_simulation():
    print("Starting IDPS Traffic Simulator... (Press CTRL+C to stop)")
    while True:
        payload = generate_mock_flow()
        try:
            res = requests.post(URL, json=payload)
            if res.status_code == 200:
                data = res.json()
                print(f"[SENT] Pred: {data.get('prediction')} | Conf: {data.get('confidence')} | ID: {data.get('prediction_id')}")
            else:
                print(f"[ERROR] HTTP {res.status_code}: {res.text}")
        except Exception as e:
            print(f"[CONNECTION FAILED] Ensure FastAPI is running on port 8000. Error: {e}")
        
        # Sleep 1 to 3 seconds between requests
        time.sleep(random.uniform(1.0, 3.0))

if __name__ == "__main__":
    run_simulation()