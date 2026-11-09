from playwright.sync_api import Locator, Page


class BasePage:
    """Shared by every page object."""

    path = "/"

    def __init__(self, page: Page):
        self.page = page

    def open(self, **query):
        params = "&".join(f"{k}={v}" for k, v in query.items() if v)
        self.page.goto(self.path + (f"?{params}" if params else ""))
        return self

    def tid(self, test_id: str) -> Locator:
        """Find an element by its data-testid attribute: the most stable kind of locator."""
        return self.page.get_by_test_id(test_id)

    @property
    def release_label(self) -> Locator:
        return self.tid("release")
