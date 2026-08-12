import pdfplumber


def detect_bank(filepath):

    with pdfplumber.open(filepath) as pdf:

        text = ""

        for page in pdf.pages[:2]:
            page_text = page.extract_text()

            if page_text:
                text += page_text.upper()

    if "INDIAN OVERSEAS BANK" in text:
        return "IOB"

    elif "STATE BANK OF INDIA" in text:
        return "SBI"

    elif "HDFC BANK" in text:
        return "HDFC"

    elif "ICICI BANK" in text:
        return "ICICI"

    elif "AXIS BANK" in text:
        return "AXIS"

    elif "CANARA BANK" in text:
        return "CANARA"

    elif "UNION BANK" in text:
        return "UNION"

    elif "BANK OF BARODA" in text:
        return "BOB"

    elif "PUNJAB NATIONAL BANK" in text:
        return "PNB"

    else:
        return "UNKNOWN"