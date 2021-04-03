import os

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, TestCase
from django.shortcuts import reverse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait

from discobot.models import Profile, User

from .page_objects import LoginPage, SpotifyAuthPage, SpotifyLoginPage, SpotifyOauthPage, SpotifyRedirectPage

DJANGO_URL = os.environ['DJANGO_URL']

class AccountsTestCase(TestCase):
    def test_profile_with_no_query_string_id(self):
        client = Client()
        response = client.get(reverse('profile_redirect'))

        self.assertRedirects(response, reverse('add_bot'))

    def test_profile_does_not_exist(self):
        client = Client()
        response = client.get(
            reverse('profile_redirect'),
            {'profile_id': 1}
        )

        self.assertEqual(response.status_code, 404)

    def test_creating_user_account(self):
        profile_id = 1
        profile = Profile(id=profile_id, username='test')
        profile.save()

        client = Client()
        create_user_page = client.get(
            reverse('profile_redirect'),
            {'profile_id': profile_id},
            follow=True
        )

        self.assertEqual(create_user_page.status_code, 200)

        manage_user_page = client.post(
            create_user_page.redirect_chain[-1][0],
            {
                'username': 'test',
                'password1': 'asdfasdfasdf',
                'password2': 'asdfasdfasdf'
            },
            follow=True
        )
        
        self.assertEqual(manage_user_page.status_code, 200)

        ## Even though Django resets the database between tests, the
        ## user id still increments, so get the most recent user object
        ## and use it to check that user object was created successfully
        user = User.objects.last()
        self.assertEqual(user.profile.id, profile.id)

        self.assertEqual(
            manage_user_page.request['PATH_INFO'],
            reverse('spotify_auth', kwargs={"user_id":user.id})
        )

    def test_create_user_account_but_profile_already_bound_to_user(self):
        existing_user = User.objects.create_user(
            username="existing_user",
            password="asdfasdfasdf"
        )
        existing_user.save()
        
        profile_id = 1
        profile = Profile(
            id=profile_id,
            username='test',
            user=existing_user
            )
        profile.save()

        client = Client()
        response = client.get(
            reverse('profile_redirect'),
            {'profile_id': profile_id},
            follow=True
        )

        self.assertRedirects(response, reverse('login') + "?next=" + reverse("manage_user", kwargs={"user_id":existing_user.id}))

    def test_posting_to_create_user_when_profile_already_bound_to_user(self):
        existing_user = User.objects.create_user(
            username="existing_user",
            password="asdfasdfasdf"
        )
        existing_user.save()
        
        profile_id = 1
        profile = Profile(
            id=profile_id,
            username='test',
            user=existing_user
            )
        profile.save()

        client = Client()
        response = client.post(
            reverse('create_user') + "?profile_id=" + str(profile_id),
            {
                'username': 'test',
                'password1': 'asdfasdfasdf',
                'password2': 'asdfasdfasdf'
            },
            follow=True
        )

        self.assertRedirects(response, reverse('login') + "?next=" + reverse("manage_user", kwargs={"user_id":existing_user.id}))

    def test_getting_manage_profile_page(self):
        # Setup
        credentials = {
            "username":"existing_user",
            "password":"asdfasdfasdf"
        }
        existing_user = User.objects.create_user(**credentials)
        existing_user.save()

        profile_id = 1
        profile = Profile(
            id=profile_id,
            username='test',
            user=existing_user
            )
        profile.save()
        
        client = Client()

        # Not logged in
        response = client.get(
            reverse("manage_user", kwargs={"user_id": existing_user.id})
        )

        self.assertRedirects(response, reverse('login') + "?next=" + reverse("manage_user", kwargs={"user_id":existing_user.id}))

        # Logged in but no spotify token
        client.login(**credentials)
        response = client.get(
            reverse("manage_user", kwargs={"user_id": existing_user.id})
        )
        self.assertRedirects(response, reverse('spotify_auth', kwargs={'user_id': existing_user.id}))

        # Logged in and with token
        profile.spotify_auth_token=b"fakespotifytoken"
        profile.save()
        response = client.get(
            reverse("manage_user", kwargs={"user_id": existing_user.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], reverse("manage_user", kwargs={"user_id":existing_user.id}))

    def test_getting_manage_profile_page_as_different_user(self):
        # Setup
        existing_user_credentials = {
            "username":"existing_user",
            "password":"asdfasdfasdf"
        }
        existing_user = User.objects.create_user(**existing_user_credentials)
        existing_user.save()

        profile_id = 1
        profile = Profile(
            id=profile_id,
            username='existing_user',
            user=existing_user
            )
        profile.save()

        new_user_credentials = {
            "username":"new_user",
            "password":"asdfasdfasdf"
        }
        new_user = User.objects.create_user(**new_user_credentials)
        new_user.save()

        profile_id = 2
        profile = Profile(
            id=profile_id,
            username='new_user',
            user=new_user
            )
        profile.save()

        client = Client()

        # Logged in but no spotify token
        client.login(**new_user_credentials)

        response = client.get(
            reverse("manage_user", kwargs={"user_id": existing_user.id}),
            follow=True
        )

        self.assertTupleEqual(
            response.redirect_chain[0],
            (reverse("manage_user", kwargs={"user_id":new_user.id}), 302)
        )
        self.assertRedirects(response, reverse('spotify_auth', kwargs={"user_id":new_user.id}))

        # logged in and with spotify token
        profile.spotify_auth_token = b"faketoken"
        profile.save()
        response = client.get(
            reverse("manage_user", kwargs={"user_id": existing_user.id}),
            follow=True
        )
        self.assertRedirects(response, reverse('manage_user', kwargs={"user_id":new_user.id}))

    def test_spotify_auth_with_invalid_user_id(self):
        # Setup
        credentials = {
            "username":"existing_user",
            "password":"asdfasdfasdf"
        }
        existing_user = User.objects.create_user(**credentials)
        existing_user.save()

        profile_id = 1
        profile = Profile(
            id=profile_id,
            username='test',
            user=existing_user
            )
        profile.save()
        
        client = Client()

        invalid_user_id = 9999

        # Not logged in
        response = client.get(
            reverse('spotify_auth', kwargs={"user_id": invalid_user_id})
        )

        self.assertRedirects(
            response,
            reverse('login') + "?next=" + reverse('spotify_auth', kwargs={"user_id":invalid_user_id})
        )

        # Logged in
        client.login(**credentials)
        response = client.get(
            reverse('spotify_auth', kwargs={"user_id": invalid_user_id})
        )
        self.assertEqual(response.status_code, 404)


class SeleniumAccountsTestCase(StaticLiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()

    def tearDown(self):
        self.driver.quit()
    
    def test_adding_spotify_auth(self):
        # Setup
        credentials = {
            "username":"existing_user",
            "password":"asdfasdfasdf"
        }
        existing_user = User.objects.create_user(**credentials)
        existing_user.save()

        profile_id = 1
        profile = Profile(
            id=profile_id,
            username='test',
            user=existing_user
            )
        profile.save()

        wait = WebDriverWait(self.driver, 5)

        self.driver.get(self.live_server_url + reverse('spotify_auth', kwargs={'user_id': existing_user.id}))

        login_page = LoginPage()
        wait.until(lambda driver: login_page.url in driver.current_url)

        login_page.find_username_input(self.driver).send_keys(credentials['username'])
        login_page.find_password_input(self.driver).send_keys(credentials['password'])
        login_page.find_submit_button(self.driver).click()

        spotify_auth_page = SpotifyAuthPage()
        wait.until(lambda driver: spotify_auth_page.url in driver.current_url)

        spotify_auth_page.find_spotify_auth_link(self.driver).click()

        spotify_login_page = SpotifyLoginPage()
        wait.until(lambda driver: spotify_login_page.url in driver.current_url)

        spotify_login_page.find_username_input(self.driver).send_keys(os.environ['SPOTIFY_TEST_ACCOUNT_EMAIL'])
        spotify_login_page.find_password_input(self.driver).send_keys(os.environ['SPOTIFY_TEST_ACCOUNT_PASSWORD'])
        spotify_login_page.find_submit_button(self.driver).click()

        try:
            # Spotify account has already authorized discobot
            wait.until(lambda driver: DJANGO_URL in driver.current_url)
        except TimeoutException:
            # Spotify account has not yet authorized discobot
            spotify_oauth_page = SpotifyOauthPage()
            wait.until(lambda driver: spotify_oauth_page.url in driver.current_url)
            spotify_oauth_page.find_accept_button(self.driver).click()
            wait.until(lambda driver: DJANGO_URL in driver.current_url)

        # Swap hardcoded spotify redirect URL for test server URL
        test_url = self.driver.current_url.replace(DJANGO_URL, self.live_server_url)
        self.driver.get(test_url)

        spotify_redirect_page = SpotifyRedirectPage()
        wait.until(lambda driver: spotify_redirect_page.url in driver.current_url)

        assert 'Got a spotify redirect' in self.driver.page_source