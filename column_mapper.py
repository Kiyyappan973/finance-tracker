import pandas as pd


# =========================================================
# UNIVERSAL COLUMN MAPPING
# =========================================================

COLUMN_MAPPING = {

    "date": [
        "date",
        "txn date",
        "transaction date",
        "transaction_date",
        "value date",
        "tran date",
        "trans date"
    ],

    "description": [
        "description",
        "narration",
        "remarks",
        "particulars",
        "details",
        "transaction details",
        "transaction description",
        "narration details"
    ],

    "debit": [
        "debit",
        "debit amount",
        "debit amt",
        "dr amount",
        "dr amt",
        "withdrawal",
        "withdrawal amount",
        "withdrawal amt",
        "withdraw",
        "paid",
        "payments",
        "payment",
        "dr"
    ],

    "credit": [
        "credit",
        "credit amount",
        "credit amt",
        "cr amount",
        "cr amt",
        "deposit",
        "deposit amount",
        "deposit amt",
        "deposits",
        "received",
        "receipt",
        "cr"
    ],

    "balance": [
        "balance",
        "closing balance",
        "available balance",
        "avail balance",
        "running balance",
        "account balance",
        "closing bal",
        "balance amount"
    ],

    "amount": [
        "amount",
        "transaction amount",
        "txn amount",
        "transaction amt",
        "txn amt",
        "value"
    ],

    "type": [
        "type",
        "transaction type",
        "txn type",
        "dr/cr",
        "cr/dr",
        "credit/debit",
        "debit/credit"
    ]
}


# =========================================================
# CLEAN MONEY
# =========================================================

def clean_money(value):

    if value is None:
        return 0.0

    if pd.isna(value):
        return 0.0

    value = str(value).strip()

    if value == "":
        return 0.0

    value = (
        value
        .replace("₹", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace(",", "")
        .replace(" ", "")
    )

    # Example:
    # (500.00) -> -500.00

    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]

    # Remove common suffixes

    value = value.replace("DR", "")
    value = value.replace("CR", "")

    try:
        return float(value)

    except (ValueError, TypeError):

        return 0.0


# =========================================================
# FIND COLUMN
# =========================================================

def find_column(df, possible_names):

    columns = {}

    for column in df.columns:

        cleaned = (
            str(column)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        cleaned = " ".join(cleaned.split())

        columns[cleaned] = column

    for name in possible_names:

        name = (
            str(name)
            .strip()
            .lower()
            .replace("_", " ")
            .replace("-", " ")
        )

        name = " ".join(name.split())

        if name in columns:

            return columns[name]

    return None


# =========================================================
# NORMALIZE COLUMNS
# =========================================================

def normalize_columns(df):

    df = df.copy()

    # =====================================================
    # DEBUG - SHOW ORIGINAL COLUMNS
    # =====================================================

    print("\n========== ORIGINAL COLUMNS ==========")
    print(list(df.columns))
    print("======================================\n")

    # =====================================================
    # CLEAN COLUMN NAMES
    # =====================================================

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    # =====================================================
    # FIND COLUMNS
    # =====================================================

    date_column = find_column(
        df,
        COLUMN_MAPPING["date"]
    )

    description_column = find_column(
        df,
        COLUMN_MAPPING["description"]
    )

    debit_column = find_column(
        df,
        COLUMN_MAPPING["debit"]
    )

    credit_column = find_column(
        df,
        COLUMN_MAPPING["credit"]
    )

    balance_column = find_column(
        df,
        COLUMN_MAPPING["balance"]
    )

    amount_column = find_column(
        df,
        COLUMN_MAPPING["amount"]
    )

    type_column = find_column(
        df,
        COLUMN_MAPPING["type"]
    )

    # =====================================================
    # DEBUG - FOUND COLUMNS
    # =====================================================

    print("\n========== COLUMN DETECTION ==========")

    print("Date     :", date_column)
    print("Description :", description_column)
    print("Debit    :", debit_column)
    print("Credit   :", credit_column)
    print("Balance  :", balance_column)
    print("Amount   :", amount_column)
    print("Type     :", type_column)

    print("======================================\n")

    # =====================================================
    # RENAME
    # =====================================================

    rename_map = {}

    if date_column is not None:
        rename_map[date_column] = "date"

    if description_column is not None:
        rename_map[description_column] = "description"

    if debit_column is not None:
        rename_map[debit_column] = "debit"

    if credit_column is not None:
        rename_map[credit_column] = "credit"

    if balance_column is not None:
        rename_map[balance_column] = "balance"

    if amount_column is not None:
        rename_map[amount_column] = "amount"

    if type_column is not None:
        rename_map[type_column] = "type"

    df = df.rename(
        columns=rename_map
    )

    # =====================================================
    # AMOUNT + TYPE FORMAT
    # =====================================================

    if "amount" in df.columns:

        df["amount"] = df["amount"].apply(
            clean_money
        )

        # Only create if not already present

        if "debit" not in df.columns:
            df["debit"] = 0.0

        if "credit" not in df.columns:
            df["credit"] = 0.0

        if "type" in df.columns:

            for index, row in df.iterrows():

                transaction_type = str(
                    row.get("type", "")
                ).strip().lower()

                amount = clean_money(
                    row.get("amount", 0)
                )

                # Debit

                if transaction_type in [
                    "dr",
                    "debit",
                    "d",
                    "withdraw",
                    "withdrawal",
                    "paid",
                    "payment"
                ]:

                    df.at[
                        index,
                        "debit"
                    ] = amount

                # Credit

                elif transaction_type in [
                    "cr",
                    "credit",
                    "c",
                    "deposit",
                    "received",
                    "receipt"
                ]:

                    df.at[
                        index,
                        "credit"
                    ] = amount

        else:

            # =================================================
            # TRY SIGN BASED AMOUNT
            # =================================================

            for index, row in df.iterrows():

                amount = clean_money(
                    row.get("amount", 0)
                )

                if amount < 0:

                    df.at[
                        index,
                        "debit"
                    ] = abs(amount)

                else:

                    df.at[
                        index,
                        "credit"
                    ] = amount

    # =====================================================
    # CREATE DEBIT IF MISSING
    # =====================================================

    if "debit" not in df.columns:

        df["debit"] = 0.0

    # =====================================================
    # CREATE CREDIT IF MISSING
    # =====================================================

    if "credit" not in df.columns:

        df["credit"] = 0.0

    # =====================================================
    # CLEAN DEBIT
    # =====================================================

    df["debit"] = df["debit"].apply(
        clean_money
    )

    # =====================================================
    # CLEAN CREDIT
    # =====================================================

    df["credit"] = df["credit"].apply(
        clean_money
    )

    # =====================================================
    # DATE
    # =====================================================

    if "date" not in df.columns:

        df["date"] = ""

    df["date"] = (
        df["date"]
        .fillna("")
        .astype(str)
    )

    # =====================================================
    # DESCRIPTION
    # =====================================================

    if "description" not in df.columns:

        df["description"] = ""

    df["description"] = (
        df["description"]
        .fillna("")
        .astype(str)
    )

    # =====================================================
    # BALANCE
    # =====================================================

    has_real_balance = False

    if "balance" in df.columns:

        original_balance = df["balance"].copy()

        df["balance"] = df["balance"].apply(
            clean_money
        )

        # Check whether balance really contains values

        if not df.empty:

            has_real_balance = (
                df["balance"].abs().sum() > 0
            )

    # =====================================================
    # RUNNING BALANCE
    # =====================================================

    if not has_real_balance:

        print(
            "Statement does NOT contain real Balance."
        )

        print(
            "Calculating running balance..."
        )

        df["balance"] = (
            df["credit"] - df["debit"]
        ).cumsum()

    else:

        print(
            "Real bank Balance detected."
        )

    # =====================================================
    # FINAL NUMERIC CLEANUP
    # =====================================================

    df["debit"] = pd.to_numeric(
        df["debit"],
        errors="coerce"
    ).fillna(0.0)

    df["credit"] = pd.to_numeric(
        df["credit"],
        errors="coerce"
    ).fillna(0.0)

    df["balance"] = pd.to_numeric(
        df["balance"],
        errors="coerce"
    ).fillna(0.0)

    # =====================================================
    # FINAL COLUMN ORDER
    # =====================================================

    df = df[
        [
            "date",
            "description",
            "debit",
            "credit",
            "balance"
        ]
    ]

    # =====================================================
    # DEBUG
    # =====================================================

    print("\n========== NORMALIZED DATA ==========")

    print(
        df.head(10).to_string(index=False)
    )

    print(
        "\nColumns:",
        list(df.columns)
    )

    print(
        "\nTotal Debit:",
        df["debit"].sum()
    )

    print(
        "Total Credit:",
        df["credit"].sum()
    )

    print(
        "=====================================\n"
    )

    return df