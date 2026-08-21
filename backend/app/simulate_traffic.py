import time
import random
import requests

# URL of local FastAPI endpoint
URL = "http://127.0.0.1:8000/predict"

def generate_mock_flow():
    # Includes weak classes to demonstrate live model degradation
    traffic_type = random.choices(
        population=[
            'BENIGN', 'DDoS', 'PortScan', 'Bot', 'SSH-Patator',
            'Web Attack - XSS', 'Web Attack - Brute Force', 'Web Attack - Sql Injection', 'Heartbleed'
        ],
        weights=[0.20, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10]
    )[0]

    base_features = {
        "Active Mean": 0, "Average Packet Size": 60, "Bwd Packet Length Mean": 40,
        "Destination Port": 80, "Flow Bytes/s": 1000, "Flow Duration": 100,
        "Flow Packets/s": 10, "Fwd Packet Length Mean": 40, "Idle Mean": 0,
        "Packet Length Mean": 50, "Packet Length Std": 5, "Total Backward Packets": 2,
        "Total Fwd Packets": 2, "Total Length of Bwd Packets": 80, "Total Length of Fwd Packets": 80,
        "attack_type": traffic_type
    }

    if traffic_type == 'DDoS':
        base_features.update({
            "Destination Port": 80, "Flow Bytes/s": random.randint(50000000, 100000000),
            "Flow Duration": random.randint(10, 500), "Flow Packets/s": random.randint(100000, 500000),
            "Total Fwd Packets": random.randint(500, 2000), "attack_type": "DDoS"
        })
    elif traffic_type == 'PortScan':
        base_features.update({
            "Destination Port": random.choice([21, 22, 23, 25, 53, 80, 443, 8080]),
            "Flow Duration": random.randint(1, 50), "Flow Packets/s": random.randint(100, 500),
            "attack_type": "PortScan"
        })
    elif traffic_type == 'Bot':
        base_features.update({
            "Destination Port": 8080, "Idle Mean": round(random.uniform(1000, 5000), 2),
            "attack_type": "Bot"
        })
    elif traffic_type == 'SSH-Patator':
        base_features.update({
            "Destination Port": 22, "Flow Packets/s": random.randint(200, 800),
            "attack_type": "SSH-Patator"
        })
    elif 'Web Attack' in traffic_type:
        base_features.update({
            "Destination Port": 80, "Flow Duration": random.randint(100, 1000),
            "Average Packet Size": random.randint(120, 300),
            "attack_type": traffic_type
        })
    elif traffic_type == 'Heartbleed':
        base_features.update({
            "Destination Port": 443, "Flow Duration": random.randint(50, 300),
            "Fwd Packet Length Mean": random.randint(10, 30),
            "attack_type": "Heartbleed"
        })

    return base_features

def run_simulation():
    print("Starting Multi-Class Threat Simulator...")
    while True:
        payload = generate_mock_flow()
        try:
            res = requests.post(URL, json=payload)
            if res.status_code == 200:
                data = res.json()
                print(f"[SENT] Sent: {payload['attack_type']} | Pred: {data.get('prediction')}")
            else:
                print(f"[ERROR] HTTP {res.status_code}: {res.text}", flush=True)
        except Exception as e:
            print(f"[ERROR] {e}", flush=True)
        time.sleep(0.3)

if __name__ == "__main__":
    run_simulation()