import sys
import pandas as pd
 
 
def main():
    if len(sys.argv) < 2:
        print("Usage: python -m ml.check_columns <path_to_csv>")
        return
 
    path = sys.argv[1]
    df = pd.read_csv(path, nrows=5)  # only read a few rows, just need headers
    df.columns = df.columns.str.strip()
 
    print(f"Columns in {path}:\n")
    for col in df.columns:
        print(f"  {col!r}")
 
 
if __name__ == "__main__":
    main()