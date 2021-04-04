class SpotifyOauthPage(object):
    url = 'https://accounts.spotify.com/en/authorize'

    def find_accept_button(self, driver):
        return driver.find_element_by_id('auth-accept')

    def find_cancel_button(self, driver):
        return driver.find_element_by_id('auth-cancel')