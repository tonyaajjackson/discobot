import os
from urllib.parse import urlencode

from django.shortcuts import render
from django.http import HttpResponse

DISCORD_OAUTH_URL = "https://discord.com/api/oauth2/authorize?"
discord_params = {
    "client_id": os.environ['DISCORD_CLIENT_ID'],
    "redirect_uri": os.environ['DISCORD_REDIRECT_URI'],
    "response_type": "code",
    "scope": "identify"
}

login_url = DISCORD_OAUTH_URL + urlencode(discord_params)

def index(request):
    return render(request, "discobot/login.html", {"login_url": login_url})