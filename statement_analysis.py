from datetime import datetime



def analyze_statement(db, username):

    # =========================================
    # GET USER TRANSACTIONS
    # =========================================

    transactions = list(
        db.transactions.find({
            "username": username
        })
    )

    now = datetime.now()

    current_month = now.strftime("%B")
    current_year = now.year

    monthly_transactions = []

    # =========================================
    # FILTER CURRENT MONTH
    # =========================================

    for transaction in transactions:

        date_value = transaction.get("date", "")

        if not date_value:
            continue

        date_text = str(date_value).strip()

        transaction_date = None

        for date_format in [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d-%b-%Y",
            "%d-%b-%y"
        ]:

            try:

                transaction_date = datetime.strptime(
                    date_text,
                    date_format
                )

                break

            except ValueError:
                continue

        if transaction_date is None:
            continue

        if (
            transaction_date.month == now.month
            and transaction_date.year == now.year
        ):

            monthly_transactions.append(
                transaction
            )

    # =========================================
    # TOTAL CREDIT / DEBIT
    # =========================================

    total_credit = 0.0
    total_debit = 0.0

    for transaction in monthly_transactions:

        try:
            credit = float(
                transaction.get("credit", 0) or 0
            )
        except (ValueError, TypeError):
            credit = 0.0

        try:
            debit = float(
                transaction.get("debit", 0) or 0
            )
        except (ValueError, TypeError):
            debit = 0.0

        total_credit += credit
        total_debit += debit

    # =========================================
    # CATEGORY TOTALS
    # =========================================

    category_totals = {

        "FOOD": 0.0,
        "SHOPPING": 0.0,
        "FUEL": 0.0,
        "MEDICAL": 0.0,
        "ENTERTAINMENT": 0.0,
        "TRAVEL": 0.0,
        "SALARY": 0.0,
        "BANK_TRANSFER": 0.0,
        "OTHERS": 0.0
    }

    # =========================================
    # CATEGORY EXPENSES
    # =========================================

    for transaction in monthly_transactions:

        try:

            debit = float(
                transaction.get("debit", 0) or 0
            )

        except (ValueError, TypeError):

            debit = 0.0

        category = str(
            transaction.get(
                "category",
                "OTHERS"
            )
        ).upper().strip()

        if debit > 0:

            if category in category_totals:

                category_totals[category] += debit

            else:

                category_totals["OTHERS"] += debit

    # =========================================
    # NET CHANGE
    # =========================================

    statement_balance_change = (
        total_credit - total_debit
    )

    # =========================================
    # CLEAN TRANSACTIONS
    # =========================================

    clean_transactions = []

    for transaction in monthly_transactions:

        clean_transaction = {

            "date": str(
                transaction.get("date", "")
            ),

            "description": str(
                transaction.get(
                    "description",
                    ""
                )
            ),

            "debit": float(
                transaction.get(
                    "debit",
                    0
                ) or 0
            ),

            "credit": float(
                transaction.get(
                    "credit",
                    0
                ) or 0
            ),

            "balance": float(
                transaction.get(
                    "balance",
                    0
                ) or 0
            ),

            "category": str(
                transaction.get(
                    "category",
                    "OTHERS"
                )
            ).upper().strip()
        }

        clean_transactions.append(
            clean_transaction
        )

    # =========================================
    # DEBUG
    # =========================================

    print()
    print("========== STATEMENT ANALYSIS ==========")

    print(
        "Username:",
        username
    )

    print(
        "Current Month:",
        current_month
    )

    print(
        "Current Year:",
        current_year
    )

    print(
        "Total Transactions:",
        len(transactions)
    )

    print(
        "Monthly Transactions:",
        len(monthly_transactions)
    )

    print(
        "Total Credit:",
        total_credit
    )

    print(
        "Total Debit:",
        total_debit
    )

    print(
        "Balance Change:",
        statement_balance_change
    )

    print(
        "Category Totals:",
        category_totals
    )

    print(
        "========================================"
    )

    # =========================================
    # RETURN
    # =========================================

    return {

        "month": current_month,

        "year": current_year,

        "total_credit": total_credit,

        "total_debit": total_debit,

        "statement_balance_change":
            statement_balance_change,

        "category_totals":
            category_totals,

        "transaction_count":
            len(clean_transactions),

        "transactions":
            clean_transactions
    }