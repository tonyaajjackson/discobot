#!/usr/bin/python3

# Dependencies
import os
import re

import discord
from dotenv import load_dotenv

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import aiocron
import asyncio

import logging

# Environment Setup
logging.basicConfig(
    filename='discobot.log',
    level=logging.INFO,
    format="%(asctime)s %(message)s")

try:
    load_dotenv()

    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

    SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
    SPOTIPY_CLIENT_URI = os.getenv('SPOTIPY_CLIENT_URI')
    SPOTIFY_ALL_TIME_PLAYLIST_ID = os.getenv('SPOTIFY_ALL_TIME_PLAYLIST_ID')
    SPOTIFY_WEEKLY_PLAYLIST_ID = os.getenv('SPOTIFY_WEEKLY_PLAYLIST_ID')
    SPOTIFY_BUFFER_PLAYLIST_ID = os.getenv('SPOTIFY_BUFFER_PLAYLIST_ID')

    # Initialize Spotify connection
    spotipy_scope = 'playlist-read-collaborative playlist-modify-public'

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            scope=spotipy_scope,
            open_browser=False
        )
    )

    # Set up discord connection
    discord_client = discord.Client()
    spotify_link_regex = re.compile(r"https:\/\/open.spotify.com\/(.+)\/(.+)\?")

    # Discord functions
    @discord_client.event
    async def on_ready():
        print(f'{discord_client.user} is connected')

    @discord_client.event
    async def on_message(message):
        if message.author == discord_client.user: return
        if message.channel.id != DISCORD_CHANNEL_ID: return

        if link :=spotify_link_regex.search(message.content):
                link_type = link.group(1)
                link_id = link.group(2)

                if link_type == "track":
                    add_if_unique_tracks(SPOTIFY_ALL_TIME_PLAYLIST_ID, [link_id])
                    add_if_unique_tracks(SPOTIFY_BUFFER_PLAYLIST_ID, [link_id])

                if link_type == "album":
                    album_track_ids = [item['id'] for item in sp.album_tracks(link_id)['items']]
                    add_if_unique_tracks(SPOTIFY_ALL_TIME_PLAYLIST_ID, album_track_ids)
                    add_if_unique_tracks(SPOTIFY_BUFFER_PLAYLIST_ID, album_track_ids)

                if link_type == "artist":
                    top_song_ids = [item['id'] for item in sp.artist_top_tracks(link_id)['tracks']]
                    add_if_unique_tracks(SPOTIFY_ALL_TIME_PLAYLIST_ID, top_song_ids)
                    add_if_unique_tracks(SPOTIFY_BUFFER_PLAYLIST_ID, top_song_ids)


    # Spotify functions
    def add_if_unique_tracks(playlist_id, track_ids):
        assert type(playlist_id) == str
        assert type(track_ids) == list

        playlist = sp.playlist_items(playlist_id)
        playlist_track_ids = set(item['track']['id'] for item in playlist['items'])
        unique_track_ids = set(id for id in track_ids if id not in playlist_track_ids)
        if unique_track_ids:
            sp.playlist_add_items(playlist_id, list(unique_track_ids))


    def wipe_playlist(playlist_id):
        while track_ids := [item['track']['id'] for item in sp.playlist_tracks(playlist_id)['items']]:
            sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)

    def copy_all_playlist_tracks(source_id, dest_id):
        offset = 0
        while track_ids := [item['track']['id'] for item in sp.playlist_tracks(source_id, offset=offset)['items']]:
            sp.playlist_add_items(dest_id, track_ids)
            offset += 100

    @aiocron.crontab('0 0 * * 6')
    async def load_weekly_playlist():
        wipe_playlist(SPOTIFY_WEEKLY_PLAYLIST_ID)
        copy_all_playlist_tracks(
            SPOTIFY_BUFFER_PLAYLIST_ID,
            SPOTIFY_WEEKLY_PLAYLIST_ID
        )
        wipe_playlist(SPOTIFY_BUFFER_PLAYLIST_ID)
        channel = discord_client.get_channel(DISCORD_CHANNEL_ID)
        
        # Message chat
        await channel.send("Check out all the songs shared this week!\n" +
            "https://open.spotify.com/playlist/" + 
            SPOTIFY_WEEKLY_PLAYLIST_ID
        )
        
        await channel.send("You can also find all songs ever shared here:\n" + 
            "https://open.spotify.com/playlist/" + 
            SPOTIFY_ALL_TIME_PLAYLIST_ID
        )


    # Start Discord bot
    discord_client.run(DISCORD_TOKEN)

except Exception as e:
    logging.exception("Exception occurred", exc_info=True)
    raise
