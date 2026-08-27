import glob
import numpy as np
import pandas as pd

# 1. Broad label mapping (covers 2018 typos like 'Infilteration')
LABEL_MAPPING = {
    "BENIGN": "BENIGN",
    "Benign": "BENIGN",
    "DDoS attacks-LOIC-HTTP": "DDoS",
    "DDOS attack-HOIC": "DDoS",
    "DDOS attack-LOIC-UDP": "DDoS",
    "Bot": "Bot",
    "Botnet": "Bot",
    "FTP-BruteForce": "FTP-Patator",
    "FTP-Bruteforce": "FTP-Patator",
    "SSH-Bruteforce": "SSH-Patator",
    "DoS attacks-Hulk": "DoS Hulk",
    "DoS attacks-GoldenEye": "DoS GoldenEye",
    "DoS attacks-Slowloris": "DoS slowloris",
    "DoS attacks-SlowHTTPTest": "DoS Slowhttptest",
    "Brute Force -Web": "Web Attack - Brute Force",
    "Brute Force -XSS": "Web Attack - XSS",
    "SQL Injection": "Web Attack - Sql Injection",
    "Infiltration": "Infiltration",
    "Infilteration": "Infiltration",  # Standardizes 2018 typo
}

EXPECTED_FEATURES = [
    "Destination Port",
    "Flow Duration",
    "Total Fwd Packets",
    "Total Backward Packets",
    "Total Length of Fwd Packets",
    "Total Length of Bwd Packets",
    "Fwd Packet Length Mean",
    "Bwd Packet Length Mean",
    "Flow Bytes/s",
    "Flow Packets/s",
    "Packet Length Mean",
    "Packet Length Std",
    "Average Packet Size",
    "Active Mean",
    "Idle Mean",
]

files = glob.glob("data/archive/*.parquet")
frames = []

print(f"Processing {len(files)} parquet files from 2018 dataset...")

for f in files:
    df = pd.read_parquet(f)

    # Clean whitespace from column names
    df.columns = df.columns.str.strip()

    # Dynamically find the Destination Port column across all naming variants
    port_col = None
    for col in df.columns:
        if col.lower().replace("_", "").replace(" ", "") in ["dstport", "destinationport"]:
            port_col = col
            break

    if port_col:
        df = df.rename(columns={port_col: "Destination Port"})
    else:
        # Fallback placeholder if file lacks port data entirely
        df["Destination Port"] = 0

    # Additional standard column renames
    col_rename = {
        "Fwd Packets Length Total": "Total Length of Fwd Packets",
        "Bwd Packets Length Total": "Total Length of Bwd Packets",
        "Avg Packet Size": "Average Packet Size",
        "Tot Fwd Pkts": "Total Fwd Packets",
        "Tot Bwd Pkts": "Total Backward Packets",
        "TotLen Fwd Pkts": "Total Length of Fwd Packets",
        "TotLen Bwd Pkts": "Total Length of Bwd Packets",
    }
    df = df.rename(columns=col_rename)

    # Standardize string label values
    if "Label" in df.columns:
        df["Label"] = df["Label"].astype(str).str.strip()

    df["mapped_label"] = df["Label"].map(LABEL_MAPPING)

    # Fill remaining unmapped entries with BENIGN
    unmapped_mask = df["mapped_label"].isna()
    if unmapped_mask.sum() > 0:
        unmapped_labels = df.loc[unmapped_mask, "Label"].unique()
        print(f"[WARN] {f}: Found unmapped labels {unmapped_labels}. Mapping to BENIGN.")
        df["mapped_label"] = df["mapped_label"].fillna("BENIGN")

    # Verify features exist
    missing_cols = [col for col in EXPECTED_FEATURES if col not in df.columns]
    if missing_cols:
        print(f"[ERROR] {f} missing columns: {missing_cols}. Skipping file.")
        continue

    keep_cols = EXPECTED_FEATURES + ["mapped_label"]
    sub_df = df[keep_cols].rename(columns={"mapped_label": "Label"})

    # Clean infinite/NaN values
    sub_df[EXPECTED_FEATURES] = (
        sub_df[EXPECTED_FEATURES]
        .replace([np.inf, -np.inf], np.nan)
        .apply(pd.to_numeric, errors="coerce")
    )
    sub_df = sub_df.dropna(subset=EXPECTED_FEATURES)
    frames.append(sub_df)

if frames:
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
    output_path = "ml/cicids2018_simulation.csv"
    combined.to_csv(output_path, index=False)

    print(f"\nSuccess! Saved {len(combined)} rows to '{output_path}'.")
    print("\nClass breakdown:")
    print(combined["Label"].value_counts())
else:
    print("\n[ERROR] No valid data processed.")