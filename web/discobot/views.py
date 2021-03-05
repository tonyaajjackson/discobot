import os

from urllib.parse import urlencode
import requests

from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse

from .models import User

discord_oauth_auth_url = "https://discord.com/api/oauth2/authorize?"
DISCORD_CLIENT_ID = os.environ['DISCORD_CLIENT_ID']
DISCORD_CLIENT_SECRET = os.environ['DISCORD_CLIENT_SECRET']
DISCORD_REDIRECT_URI = os.environ['DISCORD_REDIRECT_URI']
scope = "identify"

# auth_querystring will never change after first run
auth_querystring = urlencode({
    "client_id": DISCORD_CLIENT_ID,
    "redirect_uri": DISCORD_REDIRECT_URI,
    "response_type": "code",
    "scope": scope
})
auth_url = discord_oauth_auth_url + auth_querystring

def login(request):
    return render(request, "discobot/login.html", {"auth_url": auth_url})

def authorize_discord(request):
    if code := request.GET['code']:
        token_data = {
            "client_id": DISCORD_CLIENT_ID,
            "client_secret": DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": DISCORD_REDIRECT_URI,
            "scope": scope
        }
        token_response = requests.post("https://discord.com/api/oauth2/token", data=token_data)
        token = token_response.json()
        user_response = requests.get(
            "https://discord.com/api/users/@me?",
            headers={
                "Authorization": "Bearer " + token['access_token']
            }
        )
        discord_user = user_response.json()
        try:
            user = User.objects.get(id=discord_user['id'])
            return redirect(reverse('home'))    
        except User.DoesNotExist:
            user = User(id=int(discord_user['id']), username=discord_user['username'])
            user.save()
        return redirect(reverse('home'))
    else:
        return redirect(reverse('login'))

def home(request):
    return HttpResponse("You're at the home page")