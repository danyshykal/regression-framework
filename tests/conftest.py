"""
Framework fixtures. pytest-playwright already provides: playwright, browser, context, page.
This file adds: the app server, fast API login, test-data seeding, release handling,
and a failure screenshot embedded in the HTML report.
"""
import base64
import json
import threading
from pathlib import Path

import pytest
from werkzeug.serving import make_server

from app.task_app import RELEASES, USERS, create_app
from pages.login_page import LoginPage
from pages.tasks_page import TasksPage

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_data(filename):
    """Read a JSON test-data file from data/. Used for data-driven tests."""
    return json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))


# ---------- options ----------

def pytest_addoption(parser):
    parser.addoption("--release", default="2.2", choices=sorted(RELEASES),
                     help="Which release of the Task Manager to test (default: 2.2, the latest)")


def _version(text):
    return tuple(int(part) for part in text.split("."))


@pytest.fixture(scope="session")
def release(request):
    return request.config.getoption("--release")


@pytest.fixture(autouse=True)
def _skip_features_not_in_release(request, release):
    """@pytest.mark.since("2.1") = feature only exists from release 2.1 onwards."""
    marker = request.node.get_closest_marker("since")
    if marker and _version(release) < _version(marker.args[0]):
        pytest.skip(f"feature added in release {marker.args[0]}, testing {release}")


# ---------- the app under test ----------

@pytest.fixture(scope="session")
def base_url(release):
    """
    Start the app once per test session (once per worker when running in parallel).
    Overrides pytest-base-url's fixture, so page.goto("/tasks") just works.
    """
    server = make_server("127.0.0.1", 0, create_app(release), threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


# ---------- fast login: once per session, through the API ----------

@pytest.fixture(scope="session")
def auth_cookies(playwright, base_url):
    """
    Log each demo user in ONCE via the API and keep their session cookies.
    Tests that aren't about login reuse these instead of typing into the login form every time,
    which keeps the suite fast. Login itself is still tested through the real UI in test_login.py.
    """
    cookies = {}
    for username, password in USERS.items():
        request_context = playwright.request.new_context(base_url=base_url)
        response = request_context.post("/api/login", data={"username": username, "password": password})
        assert response.ok, f"API login failed for {username}"
        cookies[username] = request_context.storage_state()["cookies"]
        request_context.dispose()
    return cookies


@pytest.fixture
def logged_in_page(page, context, auth_cookies):
    """A browser page already logged in as 'demo', with an empty task list."""
    context.add_cookies(auth_cookies["demo"])
    page.request.post("/api/reset")      # page.request shares the browser's cookies
    return page


@pytest.fixture
def seed(logged_in_page):
    """
    Create tasks through the API: much faster than through the form, and keeps each test
    focused on the one thing it checks.   seed({"title": "Pay rent", "priority": "high"})
    """
    def _seed(*tasks):
        for task in tasks:
            response = logged_in_page.request.post("/api/tasks", data=task)
            assert response.status == 201, f"Seeding failed: {response.text()}"
    return _seed


@pytest.fixture
def tasks_page(logged_in_page) -> TasksPage:
    return TasksPage(logged_in_page)


@pytest.fixture
def login_page(page) -> LoginPage:
    return LoginPage(page).open()


# ---------- failure evidence in the HTML report ----------

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """When a test fails, screenshot the page and attach it (plus the URL) to the HTML report."""
    outcome = yield
    report = outcome.get_result()
    page = item.funcargs.get("page")
    if report.when == "call" and report.failed and page is not None and not page.is_closed():
        try:
            import pytest_html
            png = base64.b64encode(page.screenshot(full_page=True)).decode()
            extras = getattr(report, "extras", [])
            extras.append(pytest_html.extras.png(png, name="Screenshot at failure"))
            extras.append(pytest_html.extras.url(page.url, name="Page URL"))
            report.extras = extras
        except Exception as error:          # evidence must never break the run itself
            report.sections.append(("screenshot", f"Could not capture screenshot: {error}"))
