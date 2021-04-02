from django.test import Client, TestCase
from django.shortcuts import reverse

from discobot.models import Profile, User

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
            reverse('manage_user', kwargs={"user_id":user.id})
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

        self.assertRedirects(response, reverse('manage_user', kwargs={"user_id":existing_user.id}))

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

        self.assertRedirects(response, reverse('manage_user', kwargs={"user_id":existing_user.id}))
