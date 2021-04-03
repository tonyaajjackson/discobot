class SpotifyAuthPage(object):
    url = '/spotify_auth/'

    def find_spotify_auth_link(self, driver):
        return driver.find_element_by_id('id_spotify_auth_url')