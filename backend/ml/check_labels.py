import glob
import os
from collections import Counter
 
import pandas as pd
 
from ml.preprocessing import load_and_preprocess
 
RAW_DATA_DIR = os.path.join("data", "raw")
 
 
def main():
    csv_paths = sorted(glob.glob(os.path.join(RAW_DATA_DIR, "*.csv")))
 
    if not csv_paths:
        print(f"No CSV files found in {RAW_DATA_DIR}/")
        return
 
    print(f"Found {len(csv_paths)} CSV file(s):")
    for p in csv_paths:
        print(f"  - {p}")
    print()
 
    overall_counts = Counter()
    per_file_labels = {}
 
    for path in csv_paths:
        fname = os.path.basename(path)
        try:
            df = load_and_preprocess(path)
        except Exception as e:
            print(f"[ERROR] Failed to process {fname}: {e}")
            continue
 
        counts = df["Label"].value_counts()
        per_file_labels[fname] = set(counts.index)
        overall_counts.update(counts.to_dict())
 
        print(f"--- {fname} ---")
        print(counts)
        print()
 
    print("=== Combined label counts across all files ===")
    for label, count in overall_counts.most_common():
        print(f"{label!r}: {count}")
    print()
 
    # Flag labels that look similar but aren't identical strings
    # (simple heuristic: same label with punctuation/spacing normalized)
    all_labels = list(overall_counts.keys())
    normalized_map = {}
    for label in all_labels:
        norm = (
            label.lower()
            .replace("–", "-")
            .replace("—", "-")
            .replace(" - ", "-")
            .replace(" ", "")
        )
        normalized_map.setdefault(norm, set()).add(label)
 
    suspicious = {k: v for k, v in normalized_map.items() if len(v) > 1}
 
    if suspicious:
        print("=== Possible label inconsistencies (review these) ===")
        for norm, variants in suspicious.items():
            print(f"  {variants}")
    else:
        print("No obvious label spelling inconsistencies detected.")
 
    # Which files contain which labels — useful to see if a label only
    # shows up in some daily CSVs (may indicate a naming drift over days)
    print()
    print("=== Label presence per file ===")
    label_to_files = {}
    for fname, labels in per_file_labels.items():
        for label in labels:
            label_to_files.setdefault(label, []).append(fname)
 
    for label, files in sorted(label_to_files.items()):
        print(f"{label!r}: present in {len(files)}/{len(csv_paths)} file(s)")
 
 
if __name__ == "__main__":
    main()
 