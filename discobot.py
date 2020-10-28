#!/usr/bin/python3

# Dependencies
import os
import sys
import re
import json
from types import SimpleNamespace

import discord

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import aiocron
import asyncio

import logging

# Environment Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s")

with open("config.json") as f:
    config = json.load(f, object_hook=lambda d:SimpleNamespace(**d))
    # Lambda above makes JSON load as object, not dictionary.
    # Source: https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object

with open("secrets.json") as f:
    secrets = json.load(f, object_hook=lambda d:SimpleNamespace(**d))

# Initialize Spotify connection
spotipy_scope = (
    'playlist-modify-public' + ' ' +
    'playlist-modify-private'
)

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=secrets.spotipy.client_id,
        client_secret=secrets.spotipy.secret,
        redirect_uri=secrets.spotipy.redirect_uri,
        scope=spotipy_scope,
        open_browser=False
    )
)

# Set up discord connection
discord_client = discord.Client()
spotify_link_regex = re.compile(r"https:\/\/open.spotify.com\/([^\n ]+)\/([^\n ]+)\?")

# Discord functions
@discord_client.event
async def on_ready():
    logging.info(f'{discord_client.user} is connected')

    # Test Spotify connection and trigger Spotify OAuth setup if not already authorized
    try:
        sp.track("4uLU6hMCjMI75M1A2tKUQC")['artists'][0]['name'] == 'Rick Astley'
    except spotipy.SpotifyOauthError:
        logging.exception("Error in establishing OAuth connection to Spotify. "
            "Chatbot will now begin shutdown. "
            "Try deleting the .cache file to re-trigger the OAuth authentication process.")
        sys.exit()
    
    logging.info("Successfully connected to Spotify with OAuth")


@discord_client.event
async def on_message(message):
    try:
        guild_info = [guild for guild in config.guilds if guild._id == message.guild.id][0]
    except IndexError:
        logging.error("Received message from guild_id: " + str(message.guild.id) + " but no corresponding guild was found in guilds. Ignoring message.")
        return

    if message.author == discord_client.user: return
    if message.channel.id != guild_info.channel_id: return

    if links :=spotify_link_regex.findall(message.content):
        for link in links:
            link_type = link[0]
            link_id = link[1]

            if link_type == "track":
                add_if_unique_tracks(guild_info.all_time_playlist_uri, [link_id])
                add_if_unique_tracks(guild_info.buffer_playlist_uri, [link_id])

            if link_type == "album":
                try:
                    album_track_ids = [item['id'] for item in sp.album_tracks(link_id)['items']]
                except spotipy.exceptions.SpotifyException:
                    logging.exception("Error in getting album tracks", exc_info=True)
                    break

                add_if_unique_tracks(guild_info.all_time_playlist_uri, album_track_ids)
                add_if_unique_tracks(guild_info.buffer_playlist_uri, album_track_ids)

            if link_type == "artist":
                try:
                    top_song_ids = [item['id'] for item in sp.artist_top_tracks(link_id)['tracks']]
                except spotipy.exceptions.SpotifyException:
                    logging.exception("Error in getting artist tracks", exc_info=True)
                    break

                add_if_unique_tracks(guild_info.all_time_playlist_uri, top_song_ids)
                add_if_unique_tracks(guild_info.buffer_playlist_uri, top_song_ids)


# Spotify functions
def add_if_unique_tracks(playlist_uri, track_ids):
    assert type(playlist_uri) == str
    assert type(track_ids) == list

    try:
        playlist = sp.playlist_items(playlist_uri)
    except spotipy.exceptions.SpotifyException:
        logging.exception("Error in getting tracks from playlist ID: " + playlist_uri, exc_info=True)
        return

    playlist_track_ids = set(item['track']['id'] for item in playlist['items'])
    unique_track_ids = set(id for id in track_ids if id not in playlist_track_ids)
    if unique_track_ids:
        try:
            sp.playlist_add_items(playlist_uri, list(unique_track_ids))
        except spotipy.exceptions.SpotifyException:
            logging.exception("Error in adding tracks to playlist ID: " + playlist_uri, exc_info=True)
            return


def wipe_playlist(playlist_uri):
    try:
        while track_ids := [item['track']['id'] for item in sp.playlist_tracks(playlist_uri)['items']]:
            sp.playlist_remove_all_occurrences_of_items(playlist_uri, track_ids)
    except spotipy.exceptions.SpotifyException:
        logging.exception("Error in wiping playlist: " + playlist_uri, exc_info=True)
        return

def copy_all_playlist_tracks(source_id, dest_id):
    offset = 0
    try:
        while track_ids := [item['track']['id'] for item in sp.playlist_tracks(source_id, offset=offset)['items']]:
            sp.playlist_add_items(dest_id, track_ids)
            offset += 100
    except spotipy.exceptions.SpotifyException:
        logging.exception("Error in copying tracks from playlist: " + source_id + " to playlist: " + dest_id, exc_info=True)
        return

@aiocron.crontab(config.playlist_update_datetime)
async def load_recent_playlist():
    for guild_info in config.guilds:
        wipe_playlist(guild_info.recent_playlist_uri)
        copy_all_playlist_tracks(
            guild_info.buffer_playlist_uri,
            guild_info.recent_playlist_uri
        )
        wipe_playlist(guild_info.buffer_playlist_uri)

        if not (channel := discord_client.get_channel(guild_info.channel_id)):
            logging.error("Cannot find Discord channel with id: " + 
                str(guild_info.channel_id) +
                " - check that discord bot has been added to server."
                " Follow Discord OAuth process described in readme to add bot to server.")
            break

        # Message chat
        await channel.send("Check out all the songs shared recently!\n" +
            "https://open.spotify.com/playlist/" + 
            guild_info.recent_playlist_uri
        )
        
        await channel.send("You can also find all songs ever shared here:\n" + 
            "https://open.spotify.com/playlist/" + 
            guild_info.all_time_playlist_uri
        )


# Start Discord bot
discord_client.run(secrets.discord.token)
