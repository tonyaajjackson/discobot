class SpotifyLoginPage(object):
    url = 'https://accounts.spotify.com/en/login'

    def find_username_input(self, driver):
        return driver.find_element_by_id('login-username')

    def find_password_input(self, driver):
        return driver.find_element_by_id('login-password')

    def find_submit_button(self, driver):
        return driver.find_element_by_id('login-button')