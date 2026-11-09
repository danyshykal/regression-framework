"""Completing, reopening and deleting tasks, including the browser's confirm dialog."""
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.regression


def test_TC_ACT_01_complete_a_task(tasks_page, seed):
    seed({"title": "Pay rent", "priority": "high"})
    tasks_page.open()
    tasks_page.row("Pay rent").toggle()
    row = tasks_page.row("Pay rent")
    expect(row.checkbox).to_be_checked()
    expect(row.root).to_have_class("done")
    expect(tasks_page.summary).to_have_text("0 open · 1 done")


def test_TC_ACT_02_reopen_a_completed_task(tasks_page, seed):
    seed({"title": "Pay rent", "priority": "high", "done": True})
    tasks_page.open()
    tasks_page.row("Pay rent").toggle()
    expect(tasks_page.row("Pay rent").checkbox).not_to_be_checked()


def test_TC_ACT_03_delete_after_confirming(tasks_page, seed):
    seed({"title": "Old task"}, {"title": "Keep me"})
    tasks_page.open()
    row = tasks_page.row("Old task")
    row.delete(confirm=True)
    assert row.last_dialog_message == "Delete this task?"
    expect(tasks_page.row("Old task").root).to_have_count(0)
    expect(tasks_page.row("Keep me").root).to_be_visible()


def test_TC_ACT_04_cancelling_delete_keeps_the_task(tasks_page, seed):
    seed({"title": "Important task"})
    tasks_page.open()
    tasks_page.row("Important task").delete(confirm=False)
    tasks_page.open()                                    # reload to be sure nothing changed on the server
    expect(tasks_page.row("Important task").root).to_be_visible()


def test_TC_ACT_05_completion_survives_reload(tasks_page, seed):
    seed({"title": "Read chapter 3"})
    tasks_page.open()
    tasks_page.row("Read chapter 3").toggle()
    tasks_page.page.reload()
    expect(tasks_page.row("Read chapter 3").checkbox).to_be_checked()


def test_TC_SUM_01_summary_counts_open_and_done(tasks_page, seed):
    seed({"title": "A"}, {"title": "B"}, {"title": "C", "done": True},
         {"title": "D", "done": True}, {"title": "E", "done": True})
    tasks_page.open()
    expect(tasks_page.summary).to_have_text("2 open · 3 done")
