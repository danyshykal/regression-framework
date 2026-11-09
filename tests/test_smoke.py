"""Smoke tests: is the build alive and does the core journey work? Run first, fail fast."""
import pytest
from playwright.sync_api import expect

from pages.tasks_page import TasksPage

pytestmark = [pytest.mark.smoke, pytest.mark.regression]


def test_TC_SMK_01_app_loads_with_release_label(login_page, release):
    expect(login_page.form).to_be_visible()
    expect(login_page.release_label).to_have_text(f"Task Manager v{release}")


def test_TC_SMK_02_core_journey_login_and_add_task(login_page, page):
    """End to end through the real UI, no shortcuts: log in, add a task, see it."""
    page.request.post("/api/login", data={"username": "demo", "password": "Demo@123"})
    page.request.post("/api/reset")          # start from an empty task list
    page.context.clear_cookies()             # log out again, so the login below is a real UI login
    login_page.open()
    login_page.login("demo", "Demo@123")
    tasks = TasksPage(page)
    tasks.add_task("Buy groceries", "low")
    expect(tasks.row("Buy groceries").root).to_be_visible()
