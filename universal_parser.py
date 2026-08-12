import pandas as pd

COLUMN_ALIASES = {

    "date": [
        "date",
        "txn date",
        "transaction date",
        "value date",
        "posting date",
        "tran date"
    ],

    "description": [
        "description",
        "narration",
        "remarks",
        "particulars",
        "details"
    ],

    "debit": [
        "debit",
        "withdrawal",
        "withdraw",
        "dr amount",
        "debit amount"
    ],

    "credit": [
        "credit",
        "deposit",
        "cr amount",
        "credit amount"
    ],

    "balance": [
        "balance",
        "closing balance",
        "available balance",
        "avail balance"
    ],

    "amount": [
        "amount",
        "transaction amount"
    ],

    "type": [
        "type",
        "dr/cr",
        "transaction type"
    ]
}


def normalize_column_name(name):
    return str(name).strip().lower()


def map_columns(df):

    rename_map = {}

    for column in df.columns:

        clean = normalize_column_name(column)

        for standard, aliases in COLUMN_ALIASES.items():

            if clean in aliases:

                rename_map[column] = standard

    df = df.rename(columns=rename_map)

    return df
def normalize_dataframe(df):

    df = map_columns(df)

    # Standard columns
    standard_columns = [
        "date",
        "description",
        "debit",
        "credit",
        "balance",
        "amount",
        "type"
    ]

    for column in standard_columns:

        if column not in df.columns:

            df[column] = ""

    return df