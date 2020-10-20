#!/usr/bin/python3

# Dependencies
import os
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
    filename='discobot.log',
    level=logging.INFO,
    format="%(asctime)s %(message)s")

try:
    with open("config.json") as f:
        config = json.load(f, object_hook=lambda d:SimpleNamespace(**d))
        # Lambda above makes JSON load as object, not dictionary.
        # Source: https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object

    # Initialize Spotify connection
    spotipy_scope = (
        'playlist-modify-public' + ' ' +
        'playlist-modify-private'
    )

    sp = spotipy.Spotify(
        auth_manager=SpotifyOAuth(
            client_id=config.spotipy.client_id,
            client_secret=config.spotipy.secret,
            redirect_uri=config.spotipy.redirect_uri,
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
        print(f'{discord_client.user} is connected')

    @discord_client.event
    async def on_message(message):
        if message.author == discord_client.user: return
        if message.channel.id != config.discord.channel_id: return

        if links :=spotify_link_regex.findall(message.content):
            for link in links:
                link_type = link[0]
                link_id = link[1]

                if link_type == "track":
                    add_if_unique_tracks(config.spotipy.all_time_playlist_id, [link_id])
                    add_if_unique_tracks(config.spotipy.buffer_playlist_id, [link_id])

                if link_type == "album":
                    try:
                        album_track_ids = [item['id'] for item in sp.album_tracks(link_id)['items']]
                    except spotipy.exceptions.SpotifyException:
                        logging.exception("Error in getting album tracks", exc_info=True)
                        break

                    add_if_unique_tracks(config.spotipy.all_time_playlist_id, album_track_ids)
                    add_if_unique_tracks(config.spotipy.buffer_playlist_id, album_track_ids)

                if link_type == "artist":
                    try:
                        top_song_ids = [item['id'] for item in sp.artist_top_tracks(link_id)['tracks']]
                    except spotipy.exceptions.SpotifyException:
                        logging.exception("Error in getting artist tracks", exc_info=True)
                        break

                    add_if_unique_tracks(config.spotipy.all_time_playlist_id, top_song_ids)
                    add_if_unique_tracks(config.spotipy.buffer_playlist_id, top_song_ids)


    # Spotify functions
    def add_if_unique_tracks(playlist_id, track_ids):
        assert type(playlist_id) == str
        assert type(track_ids) == list

        try:
            playlist = sp.playlist_items(playlist_id)
        except spotipy.exceptions.SpotifyException:
            logging.exception("Error in getting tracks from playlist ID: " + playlist_id, exc_info=True)
            return

        playlist_track_ids = set(item['track']['id'] for item in playlist['items'])
        unique_track_ids = set(id for id in track_ids if id not in playlist_track_ids)
        if unique_track_ids:
            try:
                sp.playlist_add_items(playlist_id, list(unique_track_ids))
            except spotipy.exceptions.SpotifyException:
                logging.exception("Error in adding tracks to playlist ID: " + playlist_id, exc_info=True)
                return


    def wipe_playlist(playlist_id):
        try:
            while track_ids := [item['track']['id'] for item in sp.playlist_tracks(playlist_id)['items']]:
                sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)
        except spotipy.exceptions.SpotifyException:
            logging.exception("Error in wiping playlist: " + playlist_id, exc_info=True)
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

    @aiocron.crontab('0 2 * * 6') # 6pm PST, 7pm PDT
    async def load_weekly_playlist():
        wipe_playlist(config.spotipy.weekly_playlist_id)
        copy_all_playlist_tracks(
            config.spotipy.buffer_playlist_id,
            config.spotipy.weekly_playlist_id
        )
        wipe_playlist(config.spotipy.buffer_playlist_id)
        
        if not (channel := discord_client.get_channel(config.discord.channel_id)):
            raise Exception("Cannot find Discord channel with id: " + config.discord.channel_id)

        # Message chat
        await channel.send("Check out all the songs shared this week!\n" +
            "https://open.spotify.com/playlist/" + 
            config.spotipy.weekly_playlist_id
        )
        
        await channel.send("You can also find all songs ever shared here:\n" + 
            "https://open.spotify.com/playlist/" + 
            config.spotipy.all_time_playlist_id
        )


    # Start Discord bot
    discord_client.run(config.discord.token)

except Exception:
    logging.exception("Exception occurred", exc_info=True)
    raise
