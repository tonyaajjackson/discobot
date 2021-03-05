import os

from django.test import LiveServerTestCase

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from discobot.models import User

from .page_objects.login import LoginPage
from .page_objects.discord_login import DiscordLoginPage
from .page_objects.discord_oauth import DiscordOauthPage

DISCORD_TEST_ACCOUNT_USERNAME = os.environ['DISCORD_TEST_ACCOUNT_USERNAME']
DISCORD_TEST_ACCOUNT_EMAIL = os.environ['DISCORD_TEST_ACCOUNT_EMAIL']
DISCORD_TEST_ACCOUNT_PASSWORD = os.environ['DISCORD_TEST_ACCOUNT_PASSWORD']

# DEBUG
from django.test.utils import override_settings
from django.conf import settings


class DiscordLoginTestCase(LiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Chrome()

    def tearDown(self):
        self.driver.quit()

    @override_settings(DEBUG=True)
    def test_successful_login(self):
        wait = WebDriverWait(self.driver, 10)
        
        # User goes to Discobot login page and clicks "log in with discord" link
        login_page = LoginPage(self.driver)
        self.driver.get(self.live_server_url + login_page.url)
        login_page.find_login_with_discord_link().click()

        # User signs into discord
        discord_login_page = DiscordLoginPage(self.driver)
        wait.until(lambda driver: discord_login_page.find_email_input())
        discord_login_page.find_email_input().send_keys(DISCORD_TEST_ACCOUNT_EMAIL)
        discord_login_page.find_password_input().send_keys(DISCORD_TEST_ACCOUNT_PASSWORD)
        discord_login_page.find_submit_button().click()

        # User completes OAuth authorization
        discord_oauth_page = DiscordOauthPage(self.driver)
        wait.until(lambda driver: discord_oauth_page.find_authorize_button())
        discord_oauth_page.find_authorize_button().click()

        # User is redirected to discobot authorize page
        wait.until(lambda driver: "http://localhost" in driver.current_url)
        # Splice live server url back into link
        redirect_url = self.driver.current_url.replace("http://localhost:8000", self.live_server_url)
        self.driver.get(redirect_url)

        # User was created
        user = User.objects.get()
        assert user.username == DISCORD_TEST_ACCOUNT_USERNAME
