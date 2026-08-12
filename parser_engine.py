from bank_detector import detect_bank
from universal_parser import map_columns, normalize_dataframe
from transaction_normalizer import normalize_transactions
from transaction_service import process_transactions

def process_generic(df):
    """
    Generic statement processor.
    If the bank is not specifically supported,
    keep the normalized dataframe unchanged.
    """
    return df


def process_dataframe(df, filepath, opening_balance=0):

    """
    Detect bank and process dataframe.
    """

    bank = detect_bank(filepath)

    print(f"Detected Bank : {bank}")

    if bank == "IOB":
        df = process_iob(df)

    elif bank == "SBI":
        # SBI statement already has Amount + Type columns.
        # Use generic processing for now.
        df = process_generic(df)

    elif bank == "HDFC":
        df = process_hdfc(df)

    elif bank == "ICICI":
        df = process_icici(df)

    elif bank == "AXIS":
        df = process_axis(df)

    else:
        df = process_generic(df)

    # Convert transactions
    transactions = process_transactions(
        df,
        opening_balance=opening_balance
    )

    return transactions, bank