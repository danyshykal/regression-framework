"""Login through the real UI. Invalid cases are data-driven from data/invalid_logins.json."""
import pytest
from playwright.sync_api import expect

from pages.tasks_page import TasksPage
from tests.conftest import load_data

pytestmark = pytest.mark.regression

INVALID_LOGINS = load_data("invalid_logins.json")


@pytest.mark.smoke
def test_TC_LOGIN_01_valid_login(login_page, page):
    login_page.login("demo", "Demo@123")
    expect(page).to_have_url("/tasks")
    expect(TasksPage(page).user_name).to_have_text("demo")


@pytest.mark.parametrize("case", INVALID_LOGINS, ids=[c["id"] for c in INVALID_LOGINS])
def test_invalid_login(login_page, page, case):
    login_page.login(case["username"], case["password"])
    expect(login_page.error).to_have_text("Invalid username or password")
    expect(page).to_have_url("/login")


def test_TC_LOGIN_06_logout_ends_the_session(login_page, page):
    login_page.login("demo", "Demo@123")
    TasksPage(page).logout()
    expect(page).to_have_url("/login")
    page.goto("/tasks")                                 # try to go back in
    expect(page).to_have_url("/login")


def test_TC_LOGIN_07_tasks_page_requires_login(page):
    page.goto("/tasks")
    expect(page).to_have_url("/login")
