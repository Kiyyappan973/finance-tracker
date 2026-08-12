from bank_detector import detect_bank

from transaction_service import process_transactions


# =========================================================
# GENERIC PROCESSOR
# =========================================================

def process_generic(df):
    """
    Generic statement processor.

    If the bank does not have a specific processor,
    return the dataframe unchanged.
    """

    return df


# =========================================================
# SBI PROCESSOR
# =========================================================

def process_sbi(df):
    """
    Process SBI statement.

    SBI PDF raw columns:

    0 -> Date
    1 -> Value Date
    2 -> Description
    3 -> Reference / empty
    4 -> Debit
    5 -> Credit
    6 -> Balance
    """

    df = df.copy()

    # -----------------------------------------------------
    # Make sure there are at least 7 columns
    # -----------------------------------------------------

    if len(df.columns) >= 7:

        columns = list(df.columns)

        df = df.rename(
            columns={
                columns[0]: "date",
                columns[1]: "value_date",
                columns[2]: "description",
                columns[3]: "reference",
                columns[4]: "debit",
                columns[5]: "credit",
                columns[6]: "balance"
            }
        )

    return df


# =========================================================
# MAIN DATA PROCESSOR
# =========================================================

def process_data(
    df,
    filepath,
    opening_balance=0
):
    """
    Detect bank, prepare dataframe,
    and convert it into transactions.
    """

    print()
    print("==========================================")
    print("          PROCESS DATA")
    print("==========================================")

    # =====================================================
    # CHECK DATAFRAME
    # =====================================================

    if df is None:

        raise ValueError(
            "Dataframe is None."
        )

    if df.empty:

        raise ValueError(
            "Statement dataframe is empty."
        )

    print(
        "Input Columns:",
        list(df.columns)
    )

    print(
        "Input Rows:",
        len(df)
    )

    # =====================================================
    # DETECT BANK
    # =====================================================

    bank = detect_bank(filepath)

    print(
        "Detected Bank:",
        bank
    )

    # =====================================================
    # BANK PROCESSING
    # =====================================================

    if bank == "SBI":

        df = process_sbi(df)

    else:

        df = process_generic(df)

    # =====================================================
    # SHOW PROCESSED COLUMNS
    # =====================================================

    print()
    print(
        "Processed Columns:",
        list(df.columns)
    )

    # =====================================================
    # PROCESS TRANSACTIONS
    # =====================================================

    transactions = process_transactions(
        df,
        opening_balance=opening_balance
    )

    # =====================================================
    # RESULT
    # =====================================================

    print()
    print(
        "Transactions extracted:",
        len(transactions)
    )

    print(
        "=========================================="
    )

    return transactions, bank


# =========================================================
# BACKWARD COMPATIBILITY
# =========================================================

def process_dataframe(
    df,
    filepath,
    opening_balance=0
):
    """
    Alias for older code which uses process_dataframe().
    """

    return process_data(
        df,
        filepath,
        opening_balance
    )