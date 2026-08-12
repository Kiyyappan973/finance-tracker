import pdfplumber
import pandas as pd


class PDFEngine:

    def __init__(self, filepath):

        self.filepath = filepath

        self.tables = []

        self.text = ""

    # =====================================================
    # EXTRACT TABLES
    # =====================================================

    def extract_tables(self):

        self.tables = []

        with pdfplumber.open(self.filepath) as pdf:

            for page_number, page in enumerate(pdf.pages, start=1):

                tables = page.extract_tables()

                if not tables:
                    continue

                for table in tables:

                    if not table:
                        continue

                    self.tables.append(table)

        return self.tables

    # =====================================================
    # EXTRACT TEXT
    # =====================================================

    def extract_text(self):

        self.text = ""

        with pdfplumber.open(self.filepath) as pdf:

            for page in pdf.pages:

                txt = page.extract_text()

                if txt:

                    self.text += txt + "\n"

        return self.text

    # =====================================================
    # CHECK DATE
    # =====================================================

    def is_date(self, value):

        if value is None:
            return False

        value = str(value).strip()

        try:

            pd.to_datetime(
                value,
                format="%d/%m/%Y"
            )

            return True

        except Exception:

            return False

    # =====================================================
    # BUILD DATAFRAME
    # =====================================================

    def build_dataframe(self):

        if not self.tables:

            self.extract_tables()

        transaction_rows = []

        print()
        print("========== PDF ENGINE ==========")

        # -------------------------------------------------
        # PROCESS EACH TABLE
        # -------------------------------------------------

        for table_index, table in enumerate(self.tables):

            if not table:
                continue

            print(
                f"Processing table {table_index + 1}"
            )

            # ---------------------------------------------
            # Find transaction rows
            # ---------------------------------------------

            for row in table:

                if not row:
                    continue

                # Make sure row has 7 columns
                row = list(row)

                if len(row) < 7:
                    continue

                # Only transaction rows start with date
                first_column = row[0]

                if not self.is_date(first_column):
                    continue

                # -----------------------------------------
                # SBI FORMAT
                #
                # 0 = Date
                # 1 = Value Date
                # 2 = Description
                # 3 = Reference
                # 4 = Debit
                # 5 = Credit
                # 6 = Balance
                # -----------------------------------------

                date_value = row[0]

                description = row[2]

                debit = row[4]

                credit = row[5]

                balance = row[6]

                transaction_rows.append(
                    [
                        date_value,
                        description,
                        debit,
                        credit,
                        balance
                    ]
                )

        # =================================================
        # NO TRANSACTIONS
        # =================================================

        if not transaction_rows:

            print(
                "No transaction rows detected."
            )

            print(
                "================================"
            )

            return pd.DataFrame(
                columns=[
                    "date",
                    "description",
                    "debit",
                    "credit",
                    "balance"
                ]
            )

        # =================================================
        # CREATE DATAFRAME
        # =================================================

        df = pd.DataFrame(
            transaction_rows,
            columns=[
                "date",
                "description",
                "debit",
                "credit",
                "balance"
            ]
        )

        # =================================================
        # CLEAN DATE
        # =================================================

        df["date"] = pd.to_datetime(
            df["date"],
            format="%d/%m/%Y",
            errors="coerce"
        )

        df["date"] = df["date"].dt.strftime(
            "%Y-%m-%d"
        )

        # =================================================
        # CLEAN DESCRIPTION
        # =================================================

        df["description"] = (
            df["description"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        # =================================================
        # CLEAN MONEY
        # =================================================

        def clean_money(value):

            if value is None:
                return 0.0

            value = str(value).strip()

            if value in ["", "-", "None", "nan"]:
                return 0.0

            # Remove commas
            value = value.replace(",", "")

            # Remove currency symbols
            value = (
                value
                .replace("₹", "")
                .replace("$", "")
                .replace("Rs.", "")
                .replace("Rs", "")
                .strip()
            )

            try:

                return float(value)

            except Exception:

                return 0.0

        df["debit"] = df["debit"].apply(
            clean_money
        )

        df["credit"] = df["credit"].apply(
            clean_money
        )

        df["balance"] = df["balance"].apply(
            clean_money
        )

        # =================================================
        # REMOVE INVALID ROWS
        # =================================================

        df = df[
            df["date"].notna()
        ]

        # =================================================
        # RESET INDEX
        # =================================================

        df = df.reset_index(
            drop=True
        )

        # =================================================
        # DEBUG
        # =================================================

        print()
        print("========== NORMALIZED PDF ==========")

        print(df.head(10).to_string())

        print()

        print(
            "Columns:",
            list(df.columns)
        )

        print()

        print(
            "Transactions:",
            len(df)
        )

        print(
            "Total Debit:",
            df["debit"].sum()
        )

        print(
            "Total Credit:",
            df["credit"].sum()
        )

        print(
            "Closing Balance:",
            df["balance"].iloc[-1]
            if len(df) > 0
            else 0
        )

        print(
            "===================================="
        )

        return df