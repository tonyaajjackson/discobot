class LoginPage(object):
    def __init__(self, driver):
        self.driver = driver
        self.url = ""

    def find_login_with_discord_link(self):
        return self.driver.find_element_by_id("login-with-discord-link")