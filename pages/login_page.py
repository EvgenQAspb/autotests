LOGIN_URL = "https://the-internet.herokuapp.com/login"


class LoginPage:
    def __init__(self, page):
        self.page = page
        self.username = page.locator("#username")
        self.password = page.locator("#password")
        self.submit_button = page.locator("button[type='submit']")
        self.flash_success = page.locator(".flash.success")
        self.flash_error = page.locator(".flash.error")

    def open(self):
        self.page.goto(LOGIN_URL)

    def fill_username(self, value):
        self.username.fill(value)

    def fill_password(self, value):
        self.password.fill(value)

    def submit(self):
        self.submit_button.click()

    def login(self, username, password):
        self.fill_username(username)
        self.fill_password(password)
        self.submit()

    def get_flash_text(self):
        return self.flash_success.inner_text().strip()

    def get_error_text(self):
        return self.flash_error.inner_text().strip()
