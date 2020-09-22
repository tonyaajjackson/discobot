#!/usr/bin/python3

# Dependencies
import os
import re

import discord
from dotenv import load_dotenv

import spotipy
from spotipy.oauth2 import SpotifyOAuth


# ENVIRONMENT SETUP
load_dotenv()


# Discord
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_GUILD = os.getenv('DISCORD_GUILD')

link_regex = re.compile(r"https:\/\/open.spotify.com\/(.+)\/(.+)\?")

client = discord.Client()

@client.event
async def on_ready():
    print(f'{client.user} is connected')

@client.event 
async def on_message(message):
    if message.author == client.user: return

    # Extract Spotify link
    if link :=link_regex.search(message.content):
        link_type = link.group(1)
        link_id = link.group(2)

        all_time_playlist = sp.playlist_items(SPOTIFY_ALL_TIME_PLAYLIST_ID)
        weekly_playlist = sp.playlist_items(SPOTIFY_WEEKLY_PLAYLIST_ID)
        
        if link_type == "track":
            if link_id not in [item['track']['id'] for item in all_time_playlist['items']]:
                sp.playlist_add_items(SPOTIFY_ALL_TIME_PLAYLIST_ID, [link_id])

            if link_id not in [item['track']['id'] for item in weekly_playlist['items']]:
                sp.playlist_add_items(SPOTIFY_WEEKLY_PLAYLIST_ID, [link_id])
        



# Spotify
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_CLIENT_URI = os.getenv('SPOTIPY_CLIENT_URI')

SPOTIFY_ALL_TIME_PLAYLIST_ID = os.getenv('SPOTIFY_ALL_TIME_PLAYLIST_ID')
SPOTIFY_WEEKLY_PLAYLIST_ID = os.getenv('SPOTIFY_WEEKLY_PLAYLIST_ID')

spotipy_scope = 'playlist-read-collaborative playlist-modify-public'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=spotipy_scope))

# Start discord bot
client.run(DISCORD_TOKEN)
