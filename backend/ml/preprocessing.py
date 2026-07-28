import pandas as pd
import numpy as np


def load_and_preprocess(filepath: str) -> pd.DataFrame:
    """
    Loads an IDS dataset, filters specific columns, handles missing/infinite
    values, removes duplicates, and cleans label formatting.

    Parameters:
        filepath (str): Path to the input CSV file.

    Returns:
        pd.DataFrame: Cleaned and preprocessed dataframe.
    """
    # 1. Load the dataset
    df = pd.read_csv(filepath)

    # 2. Strip whitespace from column names (CICIDS2017 has leading spaces)
    df.columns = df.columns.str.strip()

    df = df.drop(columns=[c for c in df.columns if c.startswith("Unnamed")], errors="ignore")

    # 3. Define target columns
    columns_to_keep = [
        'Destination Port', 'Flow Duration', 'Total Fwd Packets',
        'Total Backward Packets', 'Total Length of Fwd Packets',
        'Total Length of Bwd Packets', 'Fwd Packet Length Mean',
        'Bwd Packet Length Mean', 'Flow Bytes/s', 'Flow Packets/s',
        'Packet Length Mean', 'Packet Length Std', 'Average Packet Size',
        'Active Mean', 'Idle Mean', 'Label'
    ]

    # 4. Filter columns and create an explicit copy
    new_table = df[columns_to_keep].copy()

    # 5. Remove duplicate rows
    new_table = new_table.drop_duplicates()

    # 6. Replace infinite values with NaN, then drop all missing values
    new_table = new_table.replace([np.inf, -np.inf], np.nan)
    new_table = new_table.dropna()

    # 7. Clean up label formatting (strip whitespace, fix encoding artifacts)
    new_table['Label'] = new_table['Label'].str.strip()
    new_table['Label'] = new_table['Label'].str.replace('�', '-', regex=False)

    return new_table