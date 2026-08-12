import pandas as pd


def clean_amount(value):
    """
    Convert amount into float safely.
    """

    if pd.isna(value):
        return 0.0

    value = str(value)

    value = value.replace(",", "")
    value = value.replace("₹", "")
    value = value.replace(" ", "")

    try:
        return float(value)

    except:
        return 0.0


def normalize_transactions(df):

    # Create columns if missing
    for column in ["date", "description", "debit", "credit", "balance"]:

        if column not in df.columns:
            df[column] = ""

    # Handle Amount + Type format
    if "amount" in df.columns and "type" in df.columns:

        df["debit"] = 0.0
        df["credit"] = 0.0

        for index, row in df.iterrows():

            amount = clean_amount(row["amount"])

            tx_type = str(row["type"]).strip().lower()

            if tx_type in ["dr", "debit", "withdrawal"]:
                df.at[index, "debit"] = amount

            elif tx_type in ["cr", "credit", "deposit"]:
                df.at[index, "credit"] = amount

    return df