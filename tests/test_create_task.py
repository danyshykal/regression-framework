"""Creating tasks through the form. Invalid inputs are data-driven from data/invalid_tasks.json."""
from datetime import date, timedelta

import pytest
from playwright.sync_api import expect

from tests.conftest import load_data

pytestmark = pytest.mark.regression

INVALID_TASKS = load_data("invalid_tasks.json")


def days_from_today(offset):
    return "" if offset is None else (date.today() + timedelta(days=offset)).isoformat()


@pytest.mark.smoke
def test_TC_CRT_01_add_task(tasks_page):
    due = days_from_today(7)
    tasks_page.open()
    tasks_page.add_task("Prepare interview notes", "high", due)
    row = tasks_page.row("Prepare interview notes")
    expect(row.priority).to_have_text("high")
    expect(row.due).to_have_text(due)
    expect(tasks_page.summary).to_have_text("1 open · 0 done")


@pytest.mark.parametrize("case", INVALID_TASKS, ids=[c["id"] for c in INVALID_TASKS])
def test_invalid_task_rejected(tasks_page, case):
    title = "A" * case["title_length"] if "title_length" in case else case["title"]
    tasks_page.open()
    tasks_page.add_task(title, "medium", days_from_today(case["due_offset_days"]))
    expect(tasks_page.form_error).to_have_text(case["error"])
    expect(tasks_page.rows).to_have_count(0)            # nothing was saved


def test_TC_CRT_03_title_of_exactly_100_characters_accepted(tasks_page):
    """Boundary value: 100 is allowed, 101 is not (TC_CRT_02c)."""
    title = "B" * 100
    tasks_page.open()
    tasks_page.add_task(title)
    expect(tasks_page.row(title).root).to_be_visible()


def test_TC_CRT_04_due_date_today_accepted(tasks_page):
    """Boundary value: today is allowed, yesterday is not (TC_CRT_02d)."""
    today = days_from_today(0)
    tasks_page.open()
    tasks_page.add_task("Due today", "medium", today)
    expect(tasks_page.row("Due today").due).to_have_text(today)


def test_TC_CRT_05_form_keeps_values_after_error(tasks_page):
    """Usability: after an error the user shouldn't have to retype everything."""
    title = "C" * 101
    tasks_page.open()
    tasks_page.add_task(title, "high")
    expect(tasks_page.form_error).to_be_visible()
    expect(tasks_page.title_input).to_have_value(title)
    expect(tasks_page.tid("priority-select")).to_have_value("high")
