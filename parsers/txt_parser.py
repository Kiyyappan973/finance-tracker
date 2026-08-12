import pandas as pd

def read_txt(filepath):

    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    return pd.DataFrame(lines, columns=["text"])