from pages.base_page import BasePage


class LoginPage(BasePage):
    path = "/login"

    def login(self, username: str, password: str):
        self.tid("username").fill(username)
        self.tid("password").fill(password)
        self.tid("login-button").click()

    @property
    def error(self):
        return self.tid("login-error")

    @property
    def form(self):
        return self.tid("login-form")
