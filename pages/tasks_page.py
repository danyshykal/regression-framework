from playwright.sync_api import Locator, Page

from pages.base_page import BasePage


class TaskRow:
    """
    A component object: one row in the task list.
    Page objects model whole pages; component objects model a repeated piece inside one,
    so tests can say  tasks_page.row("Pay rent").complete()  instead of hunting for checkboxes.
    """

    def __init__(self, page: Page, root: Locator):
        self.page = page
        self.root = root
        self.last_dialog_message = None

    @property
    def title(self) -> Locator:
        return self.root.get_by_test_id("task-title")

    @property
    def priority(self) -> Locator:
        return self.root.get_by_test_id("task-priority")

    @property
    def due(self) -> Locator:
        return self.root.get_by_test_id("task-due")

    @property
    def checkbox(self) -> Locator:
        return self.root.get_by_test_id("task-toggle")

    def toggle(self):
        """Tick or untick the checkbox. The page reloads when the change is saved."""
        with self.page.expect_navigation():
            self.checkbox.click()

    def delete(self, confirm: bool = True):
        """Click Delete and answer the browser's confirm dialog with OK (confirm=True) or Cancel."""
        def answer(dialog):
            self.last_dialog_message = dialog.message
            dialog.accept() if confirm else dialog.dismiss()

        self.page.once("dialog", answer)
        self.root.get_by_test_id("task-delete").click()
        self.page.wait_for_load_state()


class TasksPage(BasePage):
    path = "/tasks"

    # ----- actions -----

    def add_task(self, title: str, priority: str = "medium", due: str = ""):
        self.tid("title-input").fill(title)
        self.tid("priority-select").select_option(priority)
        self.tid("due-input").fill(due)
        self.tid("add-task").click()

    def show(self, view: str):
        """Click the All / Open / Done filter tab."""
        self.tid(f"filter-{view}").click()

    def sort_by_priority(self):
        self.tid("sort-priority").click()

    def search(self, text: str):
        self.tid("search").fill(text)

    def logout(self):
        self.tid("logout").click()

    # ----- reading the page -----

    def row(self, title: str) -> TaskRow:
        """The row whose title is exactly this text."""
        locator = self.tid("task-row").filter(
            has=self.page.get_by_test_id("task-title").get_by_text(title, exact=True))
        return TaskRow(self.page, locator)

    @property
    def rows(self) -> Locator:
        return self.tid("task-row")

    @property
    def visible_rows(self) -> Locator:
        return self.page.locator("[data-testid=task-row]:visible")

    def visible_titles(self) -> list[str]:
        return self.visible_rows.get_by_test_id("task-title").all_inner_texts()

    @property
    def summary(self) -> Locator:
        return self.tid("summary")

    @property
    def form_error(self) -> Locator:
        return self.tid("form-error")

    @property
    def title_input(self) -> Locator:
        return self.tid("title-input")

    @property
    def user_name(self) -> Locator:
        return self.tid("user-name")

    @property
    def empty_state(self) -> Locator:
        return self.tid("empty-state")

    @property
    def no_matches(self) -> Locator:
        return self.tid("no-matches")
