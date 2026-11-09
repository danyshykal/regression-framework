"""Sort by priority: a new feature in release 2.1."""
import pytest

pytestmark = [pytest.mark.new_feature, pytest.mark.since("2.1")]


@pytest.fixture
def unsorted(tasks_page, seed):
    seed({"title": "Low one", "priority": "low"},
         {"title": "High one", "priority": "high"},
         {"title": "Medium one", "priority": "medium"},
         {"title": "High done", "priority": "high", "done": True})
    tasks_page.open()
    return tasks_page


def test_TC_SORT_01_sort_by_priority(unsorted):
    unsorted.sort_by_priority()
    assert unsorted.visible_titles() == ["High one", "High done", "Medium one", "Low one"]


def test_TC_SORT_02_sort_keeps_the_current_filter(unsorted):
    unsorted.show("open")
    unsorted.sort_by_priority()
    assert unsorted.visible_titles() == ["High one", "Medium one", "Low one"]
