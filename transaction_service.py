from bson import ObjectId


def normalize_columns(df):

    df = df.copy()

    new_columns = []

    for column in df.columns:
        column = str(column).strip().lower()
        new_columns.append(column)

    df.columns = new_columns

    return df


def safe_float(value):

    if value is None:
        return 0.0

    if isinstance(value, float):
        return value

    if isinstance(value, int):
        return float(value)

    value = str(value).strip()

    if value in ["", "-", "none", "None", "nan"]:
        return 0.0

    value = value.replace(",", "")

    value = (
        value
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .strip()
    )

    try:
        return float(value)

    except Exception:
        return 0.0


def clean_string(value):

    if value is None:
        return ""

    if isinstance(value, ObjectId):
        return str(value)

    return str(value).strip()


# =================================================
# PROCESS TRANSACTIONS
# =================================================

def process_transactions(df, opening_balance=0):

    # =================================================
    # NORMALIZE COLUMNS
    # =================================================

    df = normalize_columns(df)

    print()
    print("========== TRANSACTION PROCESSOR ==========")
    print("Columns:", list(df.columns))

    transactions = []

    # =================================================
    # OPENING BALANCE
    # =================================================

    running_balance = safe_float(opening_balance)

    # =================================================
    # PROCESS ROWS
    # =================================================

    for _, row in df.iterrows():

        # ---------------------------------------------
        # DATE
        # ---------------------------------------------

        date_value = clean_string(
            row.get("date", "")
        )

        # ---------------------------------------------
        # DESCRIPTION
        # ---------------------------------------------

        description = clean_string(
            row.get("description", "")
        )

        # ---------------------------------------------
        # DEBIT
        # ---------------------------------------------

        debit = safe_float(
            row.get("debit", 0)
        )

        # ---------------------------------------------
        # CREDIT
        # ---------------------------------------------

        credit = safe_float(
            row.get("credit", 0)
        )

        # ---------------------------------------------
        # BALANCE
        # ---------------------------------------------

        raw_balance = row.get(
            "balance",
            None
        )

        if (
            raw_balance is not None
            and str(raw_balance).strip()
            not in ["", "-", "None", "nan"]
        ):

            balance = safe_float(raw_balance)

            running_balance = balance

        else:

            running_balance = (
                running_balance
                + credit
                - debit
            )

            balance = running_balance

        # ---------------------------------------------
        # CATEGORY
        # ---------------------------------------------

        try:

            category = detect_category(
                description
            )

        except Exception:

            category = "OTHER"

        category = clean_string(category)

        if not category:
            category = "OTHER"

        # ---------------------------------------------
        # TRANSACTION
        # ---------------------------------------------

        transaction = {

            "date": date_value,

            "description": description,

            "debit": float(debit),

            "credit": float(credit),

            "balance": float(balance),

            "category": category
        }

        transactions.append(transaction)

    # =================================================
    # DEBUG
    # =================================================

    print()

    print(
        "Transactions:",
        len(transactions)
    )

    print(
        "Total Debit:",
        sum(
            t["debit"]
            for t in transactions
        )
    )

    print(
        "Total Credit:",
        sum(
            t["credit"]
            for t in transactions
        )
    )

    print(
        "============================================"
    )

    return transactions


# =========================================================
# SAVE TRANSACTIONS TO MONGODB
# =========================================================

def save_transactions(
    db,
    username,
    transactions
):

    if not transactions:

        print(
            "No transactions to save."
        )

        return 0

    documents = []

    for transaction in transactions:

        document = {

            "username": username,

            "date": transaction.get(
                "date",
                ""
            ),

            "description": transaction.get(
                "description",
                ""
            ),

            "debit": safe_float(
                transaction.get(
                    "debit",
                    0
                )
            ),

            "credit": safe_float(
                transaction.get(
                    "credit",
                    0
                )
            ),

            "balance": safe_float(
                transaction.get(
                    "balance",
                    0
                )
            ),

            "category": clean_string(
                transaction.get(
                    "category",
                    "OTHER"
                )
            )
        }

        documents.append(
            document
        )

    if not documents:

        return 0

    result = db.transactions.insert_many(
        documents
    )

    print(
        "Transactions saved:",
        len(result.inserted_ids)
    )

    return len(
        result.inserted_ids
    )