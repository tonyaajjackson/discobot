import os

import string
import secrets

from urllib.parse import urlencode
import requests
import json

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect, reverse
from django.http import HttpResponse, HttpResponseForbidden

from .models import User, Profile
from django.contrib.auth.forms import UserCreationForm

discord_oauth_auth_url = "https://discord.com/api/oauth2/authorize?"
DISCORD_CLIENT_ID = os.environ['DISCORD_CLIENT_ID']
DISCORD_REDIRECT_URI = os.environ['DISCORD_REDIRECT_URI']

# Add bot querystring will not change after launch
add_bot_querystring = urlencode({
    "client_id": DISCORD_CLIENT_ID,
    "permissions": 10368, # View Audit Log, Send Message, Manage Message
    "redirect_uri": DISCORD_REDIRECT_URI,
    "scope": "bot"
})
add_bot_url = discord_oauth_auth_url + add_bot_querystring

SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
SPOTIFY_REDIRECT_URI = os.environ['SPOTIFY_REDIRECT_URI']

def add_bot(request):
    return render(request, "discobot/add_bot.html", { "add_bot_url": add_bot_url})

def profile_redirect(request):
    if profile_id := request.GET.get('profile_id', None):
        profile = get_object_or_404(Profile, id=profile_id)
    else:
        return redirect("add_bot")
    
    if profile.user_id is None:
        return redirect(reverse("create_user") + "?profile_id=" + profile_id)
    else:
        return redirect("manage_user", user_id=profile.user_id)

def create_user(request):
    if profile_id := request.GET.get('profile_id', None):
        profile = get_object_or_404(Profile, id=profile_id)

        if profile.user_id is not None:
            return redirect("manage_user", user_id=profile.user_id)
    elif request.user.id:
        return redirect('manage_user', user_id=request.user.id)
    else:
        return redirect("add_bot")

    if request.method == "GET":
        return render(
            request, "registration/create_user.html",
            {"form": UserCreationForm}
        )

    elif request.method == "POST":        
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            
            profile = Profile.objects.get(id=request.GET.get('profile_id'))
            profile.user_id = user
            profile.save()

            return redirect("manage_user", user.id)

@login_required
def manage_user(request, user_id):
    if user_id != request.user.id:
        return redirect("manage_user", user_id=request.user.id)
    
    profile = get_object_or_404(Profile, user_id=user_id)

    if profile.spotify_auth_token is None:
        return redirect("spotify_auth", user_id=user_id)

    return render(request, "discobot/manage_profile.html", context={"user_id": user_id, "profile_id": profile.id})

@login_required
def spotify_auth(request, user_id):
    profile = get_object_or_404(Profile, user_id=user_id)

    profile.spotify_state = secrets.token_urlsafe()
    profile.save()

    spotify_auth_queries = {
        'client_id': SPOTIFY_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'state': profile.spotify_state,
        'scope': 'playlist-modify-public' + ' ' + 'playlist-modify-private',
    }

    spotify_auth_url = 'https://accounts.spotify.com/authorize?' + urlencode(spotify_auth_queries)

    return render(request, "discobot/spotify_auth.html", context={"spotify_auth_url": spotify_auth_url})

@login_required
def spotify_redirect(request):
    if error:= request.GET.get('error'):
        return render(request,
            'discobot/spotify_auth_failed.html',
            {
                'message': error,
                'user_id': request.user.id
            }
        )
    elif spotify_auth_code:= request.GET.get('code'):
        state = request.GET.get('state')

        try:
            profile = Profile.objects.get(spotify_state=state)
        except Profile.DoesNotExist:
            return render(
                request,
                'discobot/spotify_auth_failed.html',
                {
                    'message': 'This Spotify authorization link has already been used.',
                    'user_id': request.user.id
                }
            )

        spotify_token_queries = {
            'grant_type': 'authorization_code',
            'code': spotify_auth_code,
            'redirect_uri': SPOTIFY_REDIRECT_URI,
            'client_id': SPOTIFY_CLIENT_ID,
            'client_secret': SPOTIFY_CLIENT_SECRET
        }

        token_response = requests.post(
            'https://accounts.spotify.com/api/token',
            spotify_token_queries
        )

        if token_response.status_code != 200:
            return render(
                request,
                'discobot/spotify_auth_failed.html',
                {
                    'message': 'Failed to get token using authorization code',
                    'user_id': request.user.id
                }
            )
        
        auth_token = json.loads(token_response.content.decode())

        return HttpResponse("Got a spotify redirect!<br>" + str(auth_token))

    else:
        return HttpResponseForbidden()