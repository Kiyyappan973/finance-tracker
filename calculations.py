import math


def calculate_months_needed(target_amount, monthly_saving, annual_rate):
    monthly_rate = (annual_rate / 100) / 12
    n_months = math.log((target_amount * monthly_rate / monthly_saving) + 1) / math.log(1 + monthly_rate)
    return round(n_months)