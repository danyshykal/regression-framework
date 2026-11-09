"""Two users at once, each in their own browser context (like two separate browsers)."""
import pytest
from playwright.sync_api import expect

from pages.tasks_page import TasksPage

pytestmark = pytest.mark.regression


def test_TC_USR_01_users_only_see_their_own_tasks(browser, base_url, tasks_page, seed, auth_cookies):
    seed({"title": "Demo's private task"})

    alex_context = browser.new_context(base_url=base_url)     # a second, completely separate session
    alex_context.add_cookies(auth_cookies["alex"])
    alex_page = alex_context.new_page()
    alex_page.request.post("/api/reset")
    alex = TasksPage(alex_page).open()
    try:
        expect(alex.user_name).to_have_text("alex")
        expect(alex.row("Demo's private task").root).to_have_count(0)
        expect(alex.empty_state).to_be_visible()
    finally:
        alex_context.close()

    tasks_page.open()                                           # demo still sees it
    expect(tasks_page.row("Demo's private task").root).to_be_visible()
