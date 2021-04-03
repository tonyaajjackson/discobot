class LoginPage(object):
    url = '/accounts/login'

    def find_username_input(self, driver):
        return driver.find_element_by_id('id_username')

    def find_password_input(self, driver):
        return driver.find_element_by_id('id_password')

    def find_submit_button(self, driver):
        return driver.find_element_by_xpath("//input[@value='Login']")