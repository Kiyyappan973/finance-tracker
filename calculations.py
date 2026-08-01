import math


def calculate_months_needed(target_amount, monthly_saving, annual_rate):

    monthly_rate = (annual_rate / 100) / 12

    # No interest
    if monthly_rate == 0:
        return math.ceil(target_amount / monthly_saving)

    future_value = 0
    months = 0

    while future_value < target_amount:

        future_value = future_value * (1 + monthly_rate)

        future_value += monthly_saving

        months += 1

        if months > 1200:
            break

    return months