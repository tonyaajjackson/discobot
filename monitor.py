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
        
        if link_type == "track":
            add_if_unique_tracks(SPOTIFY_ALL_TIME_PLAYLIST_ID, [link_id])
        



# Spotify
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_CLIENT_URI = os.getenv('SPOTIPY_CLIENT_URI')

SPOTIFY_ALL_TIME_PLAYLIST_ID = os.getenv('SPOTIFY_ALL_TIME_PLAYLIST_ID')
SPOTIFY_WEEKLY_PLAYLIST_ID = os.getenv('SPOTIFY_WEEKLY_PLAYLIST_ID')

spotipy_scope = 'playlist-read-collaborative playlist-modify-public'

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=spotipy_scope))

def add_if_unique_tracks(playlist_id, track_ids):
    assert type(playlist_id) == str
    assert type(track_ids) == list

    playlist = sp.playlist_items(playlist_id)
    playlist_track_ids = set(item['track']['id'] for item in playlist['items'])
    unique_track_ids = set(id for id in track_ids if id not in playlist_track_ids)
    sp.playlist_add_items(playlist_id, list(unique_track_ids))
    

# Start discord bot
client.run(DISCORD_TOKEN)
