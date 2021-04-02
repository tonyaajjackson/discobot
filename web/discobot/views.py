import os

from urllib.parse import urlencode
import requests

from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.http import HttpResponse

from .models import User, Profile

discord_oauth_auth_url = "https://discord.com/api/oauth2/authorize?"
DISCORD_CLIENT_ID = os.environ['DISCORD_CLIENT_ID']
DISCORD_CLIENT_SECRET = os.environ['DISCORD_CLIENT_SECRET']
DISCORD_REDIRECT_URI = os.environ['DISCORD_REDIRECT_URI']

# Add bot querystring will not change after launch
add_bot_querystring = urlencode({
    "client_id": DISCORD_CLIENT_ID,
    "permissions": 10368, # View Audit Log, Send Message, Manage Message
    "redirect_uri": DISCORD_REDIRECT_URI,
    "scope": "bot"
})
add_bot_url = discord_oauth_auth_url + add_bot_querystring

def add_bot(request):
    return render(request, "discobot/add_bot.html", { "add_bot_url": add_bot_url})

def profile_redirect(request):
    if profile_id := request.GET.get('profile_id', None):
        profile = get_object_or_404(Profile, id=profile_id)
    else:
        return redirect("add_bot")
    
    if profile.user_id is None:
        return redirect("create_user")
    else:
        return redirect("manage_user", user_id=profile.user_id)

def create_user(request):
    return HttpResponse("Create your account!")

def manage_user(request, user_id):
    return HttpResponse("Manage user account: " + str(user_id))