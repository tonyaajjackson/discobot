import os

from lxml import etree
from io import BytesIO

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client, TestCase
from django.shortcuts import reverse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait

from discobot.models import Guild, Profile, User

from .page_objects import \
    AddBotPage, LoginPage, ManageUserPage, SpotifyAuthPage, \
    SpotifyLoginPage, SpotifyOauthPage, SpotifyRedirectPage

DJANGO_URL = os.environ['DJANGO_URL']

class CreateUserTestCase(TestCase):
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

    def test_valid_profile(self):
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

    def test_getting_create_user_with_no_profile(self):
        client = Client()
        response = client.get(
            reverse('create_user'),
        )

        self.assertRedirects(response, reverse('add_bot'))

    def test_getting_create_user_when_logged_in(self):
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
        client.login(**credentials)

        response = client.get(
            reverse('create_user'),
        )

        self.assertRedirects(
            response,
            reverse('manage_user', kwargs={'user_id': existing_user.id}),
            target_status_code=302
        )
        ## Expect manage_user page to subsequently redirect to spotify_auth 
        ## page as no spotify auth token has been set

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


class ManageProfileTestCase(TestCase):
    def test_getting_manage_profile_page(self):
        # Setup
        user_credentials = {
            "username":"existing_user",
            "password":"asdfasdfasdf"
        }
        user = User.objects.create_user(**user_credentials)
        user.save()

        profile = Profile(
            id=1,
            username='test',
            user=user
            )
        profile.save()

        guild_1 = Guild(id=1, profile=profile)
        guild_2 = Guild(id=2, profile=profile)
        guild_1.save()
        guild_2.save()

        other_user_credentials = {
            "username":"other_user",
            "password":"asdfasdfasdf"
        }
        other_user = User.objects.create_user(**other_user_credentials)
        other_user.save()

        other_profile = Profile(
            id=2,
            username='test',
            user=other_user
            )
        other_profile.save()

        other_user_guild = Guild(id=3, profile=other_profile)
        other_user_guild.save()
        
        # Test
        client = Client()

        # Not logged in
        response = client.get(
            reverse("manage_user", kwargs={"user_id": user.id})
        )

        self.assertRedirects(
            response,
            reverse('login') + "?next=" + reverse("manage_user", kwargs={"user_id":user.id})
        )

        # Logged in but no spotify token
        client.login(**user_credentials)
        response = client.get(
            reverse("manage_user", kwargs={"user_id": user.id})
        )
        self.assertRedirects(
            response,
            reverse('spotify_auth', kwargs={'user_id': user.id})
        )

        # Logged in and with token
        profile.spotify_auth_token=b"fakespotifytoken"
        profile.save()
        response = client.get(
            reverse("manage_user", kwargs={"user_id": user.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.request['PATH_INFO'],
            reverse("manage_user", kwargs={"user_id":user.id})
        )
        assert str(guild_1.id) in response.content.decode()
        assert str(guild_2.id) in response.content.decode()
        assert str(other_user_guild.id) not in response.content.decode()

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


class SpotifyAuthTestCase(TestCase):
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

    def test_get_spotify_redirect_directly(self):
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
        client.login(**credentials)

        response = client.get(reverse('spotify_redirect'))

        self.assertEqual(response.status_code, 403) # Forbidden

    def test_get_spotify_with_error_code(self):
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
        client.login(**credentials)

        error_reason = 'fake-error-reason'
        response = client.get(
            reverse('spotify_redirect'),
            {'error': error_reason})

        assert error_reason in response.content.decode()

    def test_get_spotify_with_invalid_state(self):
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
        client.login(**credentials)

        invalid_state = 'invalid-state'
        response = client.get(
            reverse('spotify_redirect'),
            {
                'state': invalid_state,
                'code': 'fake-spotify-code'
            }
        )

        assert 'This Spotify authorization link has already been used.' in response.content.decode()


class SeleniumSpotifyOauthTestCase(StaticLiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()

    def tearDown(self):
        self.driver.quit()
    
    def test_accepting_spotify_auth(self):
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

        self.driver.get(self.live_server_url)
        add_bot_page = AddBotPage()
        add_bot_page.find_login_link(self.driver).click()

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

        # Accept Spotify OAuth authorization
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

        manage_user_page = ManageUserPage()
        wait.until(lambda driver: manage_user_page.url_regex.match(driver.current_url))

        profile.refresh_from_db()
        assert profile.spotify_auth_token is not None
        assert profile.encrypted_fernet_key is not None
        assert profile.spotify_state is None

    def test_denying_spotify_auth(self):
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

        self.driver.get(self.live_server_url)
        add_bot_page = AddBotPage()
        add_bot_page.find_login_link(self.driver).click()

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

        spotify_login_page.find_username_input(self.driver).send_keys(os.environ['SPOTIFY_TEST_ACCOUNT_DENY_AUTH_EMAIL'])
        spotify_login_page.find_password_input(self.driver).send_keys(os.environ['SPOTIFY_TEST_ACCOUNT_DENY_AUTH_PASSWORD'])
        spotify_login_page.find_submit_button(self.driver).click()   

        # Deny Spotify OAuth authorization
        spotify_oauth_page = SpotifyOauthPage()
        wait.until(lambda driver: spotify_oauth_page.url in driver.current_url)
        try:
            spotify_oauth_page.find_cancel_button(self.driver).click()
        except WebDriverException as e:
            ## Selenium throws exception when spotify redirects to DJANGO_URL
            ## because nothing is accepting connections at that URL, so Firefox
            ## shows an "Unable to connect" page. Arriving at DJANGO_URL is
            ## expected, so it's safe to suppress this particular exception.
            if 'Reached error page: about:neterror' not in e.msg:
                raise e
        
        # Swap hardcoded spotify redirect URL for test server URL
        wait.until(lambda driver: DJANGO_URL in driver.current_url)
        test_url = self.driver.current_url.replace(DJANGO_URL, self.live_server_url)
        self.driver.get(test_url)

        spotify_redirect_page = SpotifyRedirectPage()
        wait.until(lambda driver: spotify_redirect_page.url in driver.current_url)

        assert 'Error' in self.driver.page_source


class ManageGuildTestCase(TestCase):
    def test_get_invalid_guild(self):
        # Setup
        user_credentials = {
            "username":"existing_user",
            "password":"asdfasdfasdf"
        }
        user = User.objects.create_user(**user_credentials)
        user.save()

        profile = Profile(
            id=1,
            username='test',
            user=user
            )
        profile.save()

        client = Client()
        client.login(**user_credentials)

        response = client.get(reverse('manage_guild', kwargs={'guild_id': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_manage_guild(self):
        # Setup
        user_credentials = {
            "username":"existing_user",
            "password":"asdfasdfasdf"
        }
        user = User.objects.create_user(**user_credentials)
        user.save()

        profile = Profile(
            id=1,
            username='test',
            user=user
            )
        profile.save()

        old_uris = {
            'all_time_playlist_uri': 'old_all_time_playlist_uri',
            'recent_playlist_uri':'old_recent_playlist_uri',
            'buffer_playlist_uri':'old_buffer_playlist_uri',
        }

        guild = Guild(
            id=1, 
            profile=profile,
            **old_uris
        )
        guild.save()

        client = Client()
        client.login(**user_credentials)

        old_response = client.get(reverse('manage_guild', kwargs={'guild_id': guild.id}))

        assert str(guild.id) in old_response.content.decode()
        
        old_tree = etree.parse(BytesIO(old_response.content), etree.HTMLParser())

        for (key, val) in old_uris.items():
            assert old_tree.xpath(
                "//input[@id='id_" + key + "' and @value='" + val + "']"
            ) != []

        new_uris = {
            'all_time_playlist_uri': 'new_all_time_playlist_uri',
            'recent_playlist_uri':'new_recent_playlist_uri',
            'buffer_playlist_uri':'new_buffer_playlist_uri',
        }

        redirect = client.post(
            reverse('update_guild', kwargs={'guild_id': guild.id}),
            data=new_uris
        )

        self.assertRedirects(
            redirect,
            reverse('manage_guild', kwargs={'guild_id': guild.id})
        )
        
        new_response = client.get(reverse('manage_guild', kwargs={'guild_id': guild.id}))
        
        new_tree = etree.parse(BytesIO(new_response.content), etree.HTMLParser())

        for (key, val) in new_uris.items():
            assert new_tree.xpath(
                "//input[@id='id_" + key + "' and @value='" + val + "']"
            ) != []

    def test_get_update_guild(self):
        # Setup
        user_credentials = {
            "username":"existing_user",
            "password":"asdfasdfasdf"
        }
        user = User.objects.create_user(**user_credentials)
        user.save()

        profile = Profile(
            id=1,
            username='test',
            user=user
            )
        profile.save()

        client = Client()
        client.login(**user_credentials)

        response = client.get(reverse('update_guild', kwargs={'guild_id': 1}))

        self.assertEqual(response.status_code, 403) # Forbidden