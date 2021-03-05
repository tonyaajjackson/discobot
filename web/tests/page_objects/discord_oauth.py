class DiscordOauthPage(object):
    def __init__(self, driver):
        self.driver = driver
        self.url = "https://discord.com/oauth2/authorize"

    def find_authorize_button(self):
        return self.driver.find_element_by_xpath("//div[text()='Authorize']")

    def find_cancel_button(self):
        return self.driver.find_element_by_xpath("//div[text()='Cancel']")