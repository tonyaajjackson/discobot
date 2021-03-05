class DiscordLoginPage(object):
    def __init__(self, driver):
        self.driver = driver
        self.url = "https://discord.com/login"

    def find_email_input(self):
        return self.driver.find_element_by_xpath("//input[@name='email']")

    def find_password_input(self):
        return self.driver.find_element_by_xpath("//input[@name='password']")

    def find_submit_button(self):
        return self.driver.find_element_by_xpath("//button[@type='submit']")