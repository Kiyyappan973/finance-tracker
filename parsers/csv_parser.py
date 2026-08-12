import pandas as pd

def read_csv(filepath):
    try:
        return pd.read_csv(filepath, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return pd.read_csv(filepath, encoding="latin1")
        except UnicodeDecodeError:
            return pd.read_csv(filepath, encoding="cp1252")