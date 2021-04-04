class AddBotPage(object):
    def find_login_link(self, driver):
        return driver.find_element_by_id('login-link')