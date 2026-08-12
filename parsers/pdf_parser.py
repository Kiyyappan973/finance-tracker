import pdfplumber
import pandas as pd

from bank_detector import detect_bank


def read_pdf(filepath):

    bank = detect_bank(filepath)

    rows = []

    with pdfplumber.open(filepath) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            if tables:

                for table in tables:

                    for row in table:

                        if row:
                            rows.append(row)

    if not rows:
        raise Exception("No table found inside PDF.")

    # Create dataframe
    df = pd.DataFrame(rows)

    # Remove empty rows
    df = df.dropna(how="all")

    # First row becomes header
    df.columns = df.iloc[0]

    df = df.iloc[1:].reset_index(drop=True)

    # Clean column names
    df.columns = [
        str(col).strip().replace("\n", " ")
        for col in df.columns
    ]

    # Remove completely empty columns
    df = df.loc[:, df.columns.notnull()]

    print("\n====== PDF Columns ======")
    print(df.columns.tolist())
    print("=========================\n")

    return df