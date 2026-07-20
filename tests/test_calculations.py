import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculations import calculate_months_needed


def test_calculate_months_needed_basic():
    result = calculate_months_needed(target_amount=500000, monthly_saving=7000, annual_rate=7)
    assert result == 60


def test_calculate_months_needed_higher_saving_means_fewer_months():
    months_low_saving = calculate_months_needed(500000, 5000, 7)
    months_high_saving = calculate_months_needed(500000, 10000, 7)
    assert months_high_saving < months_low_saving