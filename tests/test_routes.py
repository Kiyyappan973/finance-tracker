import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


def test_dashboard_redirects_when_not_logged_in():
    client = app.test_client()
    response = client.get('/dashboard')
    assert response.status_code == 302  # 302 means "redirect"


def test_home_page_loads_successfully():
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200  # 200 means "success"