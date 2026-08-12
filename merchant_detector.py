MERCHANT_CATEGORIES = {

    "FOOD": [
        "SWIGGY", "ZOMATO", "DOMINOS", "PIZZA", "KFC",
        "MCDONALD", "BURGER KING", "SUBWAY", "A2B",
        "SARAVANA", "HOTEL", "RESTAURANT", "CAFE",
        "STARBUCKS", "TEA", "COFFEE"
    ],

    "SHOPPING": [
        "AMAZON", "FLIPKART", "MYNTRA", "AJIO",
        "MEESHO", "SHOPPING", "DMART", "RELIANCE",
        "TRENDS", "JIOMART", "MALL"
    ],

    "FUEL": [
        "INDIAN OIL", "IOCL", "HPCL", "BPCL",
        "PETROL", "DIESEL", "FUEL", "SHELL"
    ],

    "MEDICAL": [
        "APOLLO", "MEDPLUS", "PHARMACY",
        "HOSPITAL", "CLINIC", "MEDICAL"
    ],

    "ENTERTAINMENT": [
        "NETFLIX", "SPOTIFY", "HOTSTAR",
        "PRIME VIDEO", "AMAZON PRIME",
        "SONYLIV", "YOUTUBE"
    ],

    "TRAVEL": [
        "OLA", "UBER", "IRCTC",
        "REDBUS", "MAKEMYTRIP",
        "GOIBIBO", "AIR INDIA"
    ],

    "SALARY": [
        "SALARY",
        "PAYROLL",
        "SAL CREDIT",
        "SALARY CREDIT"
    ],

    "BANK_TRANSFER": [
        "UPI",
        "NEFT",
        "IMPS",
        "RTGS",
        "TRANSFER",
        "FUND TRANSFER"
    ],

    "ATM": [
        "ATM",
        "CASH WD",
        "CASH WITHDRAWAL"
    ],

    "BILL_PAYMENT": [
        "ELECTRICITY",
        "WATER",
        "GAS",
        "MOBILE",
        "RECHARGE",
        "AIRTEL",
        "JIO",
        "BSNL",
        "VODAFONE"
    ],

    "INSURANCE": [
        "LIC",
        "INSURANCE",
        "POLICY"
    ]
}


def detect_category(description):

    description = str(description).upper()

    for category, keywords in MERCHANT_CATEGORIES.items():

        for keyword in keywords:

            if keyword in description:
                return category

    return "OTHERS"