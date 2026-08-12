import os


def detect_file_type(filepath):
    """
    Detect uploaded file type.
    Returns:
        pdf
        csv
        excel
        json
        xml
        ofx
        txt
        unknown
    """

    extension = os.path.splitext(filepath)[1].lower()

    if extension == ".pdf":
        return "pdf"

    elif extension == ".csv":
        return "csv"

    elif extension in [".xlsx", ".xls"]:
        return "excel"

    elif extension == ".json":
        return "json"

    elif extension == ".xml":
        return "xml"

    elif extension == ".ofx":
        return "ofx"

    elif extension == ".txt":
        return "txt"

    return "unknown"