"""Filter tabs (server side) and live search (client-side JavaScript)."""
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.regression

MIXED_TASKS = (
    {"title": "Write FYP report", "priority": "high"},
    {"title": "Book dentist", "priority": "low", "done": True},
    {"title": "Review pull request", "priority": "medium"},
    {"title": "Renew road tax", "priority": "high", "done": True},
)


@pytest.fixture
def mixed(tasks_page, seed):
    seed(*MIXED_TASKS)
    tasks_page.open()
    return tasks_page


def test_TC_FLT_01_open_filter(mixed):
    mixed.show("open")
    assert mixed.visible_titles() == ["Write FYP report", "Review pull request"]


def test_TC_FLT_02_done_filter(mixed):
    mixed.show("done")
    assert mixed.visible_titles() == ["Book dentist", "Renew road tax"]


def test_TC_FLT_03_all_filter(mixed):
    mixed.show("open")
    mixed.show("all")
    expect(mixed.rows).to_have_count(4)
    expect(mixed.tid("filter-all")).to_have_attribute("aria-current", "page")


def test_TC_SRC_01_search_filters_the_list(mixed):
    mixed.search("re")
    assert mixed.visible_titles() == ["Write FYP report", "Review pull request", "Renew road tax"]


def test_TC_SRC_02_search_is_case_insensitive(mixed):
    mixed.search("REPORT")
    assert mixed.visible_titles() == ["Write FYP report"]


def test_TC_SRC_03_no_matches_message(mixed):
    mixed.search("xyz")
    expect(mixed.visible_rows).to_have_count(0)
    expect(mixed.no_matches).to_be_visible()


def test_TC_SRC_04_clearing_search_shows_everything(mixed):
    mixed.search("dentist")
    expect(mixed.visible_rows).to_have_count(1)
    mixed.search("")
    expect(mixed.visible_rows).to_have_count(4)
    expect(mixed.no_matches).to_be_hidden()
