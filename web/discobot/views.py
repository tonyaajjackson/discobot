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

# Add bot querystring will not change after launch
add_bot_querystring = urlencode({
    "client_id": DISCORD_CLIENT_ID,
    "permissions": 10240, # Send Message, Manage Message
    "redirect_uri": DISCORD_REDIRECT_URI,
    "scope": "bot"
})
add_bot_url = discord_oauth_auth_url + add_bot_querystring

def add_bot(request):
    return render(request, "discobot/add_bot.html", { "add_bot_url": add_bot_url})