#!/usr/bin/python3

# Dependencies
import os
import sys
import re
import logging

import discord

import spotipy
from spotipy.oauth2 import SpotifyOAuth

import aiocron
import asyncio

from croniter import croniter
import cron_descriptor
from datetime import datetime

# Discobot modules
from import_validation import validate_config, validate_secrets

# Environment Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s")

config_path = "config.json"
secrets_path = "secrets.json"

try:
    config = validate_config(config_path)
except Exception as e:
    logging.exception(msg="Could not validate config.json:", exc_info=True)
    sys.exit()

# Print cron configuration to debug
logging.info("Current datetime is" + str(datetime.now()))
logging.info("Playlist update is scheduled to run: " + cron_descriptor.get_description(config.playlist_update_cron_expr))
logging.info("Next playlist update scheduled for: " + str(croniter(config.playlist_update_cron_expr).get_next(datetime)))
logging.info("Monitoring test is scheduled to run: " + cron_descriptor.get_description(config.testing_cron_expr))
logging.info("Next playlist update scheduled for: " + str(croniter(config.testing_cron_expr).get_next(datetime)))

try:
    secrets = validate_secrets(secrets_path)
except Exception as e:
    logging.exception(msg="Could not validate secrets.json:", exc_info=True)
    sys.exit()

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
spotify_link_regex = re.compile(r"https:\/\/open.spotify.com\/([^\n ]+)\/([A-Za-z0-9]{22})")

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

    if message.author == discord_client.user and message.content[0:6] != "!debug": return
    if message.channel.id not in guild_info.monitoring_channel_ids: return

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
        playlist_tracks = []
        offset = 0

        while playlist_temp := sp.playlist_items(playlist_uri, offset=offset)['items']:
            playlist_tracks += playlist_temp
            offset += 100
        
    except spotipy.exceptions.SpotifyException:
        logging.exception("Error in getting tracks from playlist ID: " + playlist_uri, exc_info=True)
        return

    playlist_track_ids = set(item['track']['id'] for item in playlist_tracks)
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

@aiocron.crontab(config.playlist_update_cron_expr)
async def load_recent_playlist():
    for guild_info in config.guilds:
        wipe_playlist(guild_info.recent_playlist_uri)
        copy_all_playlist_tracks(
            guild_info.buffer_playlist_uri,
            guild_info.recent_playlist_uri
        )
        wipe_playlist(guild_info.buffer_playlist_uri)

        if not (channel := discord_client.get_channel(guild_info.notify_channel_id)):
            logging.error("Cannot find Discord channel with id: " + 
                str(guild_info.notify_channel_id) +
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


@aiocron.crontab(config.testing_cron_expr)
async def monitor_connection():
    debug_guilds = [guild for guild in config.guilds if guild.is_connection_testing_guild]

    test_links = {
        "track" :   "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",
        "album" :   "https://open.spotify.com/album/6N9PS4QXF1D0OWPk0Sxtb4",
        "artist":   "https://open.spotify.com/artist/0gxyHStUsqpMadRV0Di1Qt"
    }

    for guild_info in debug_guilds:
        logging.info("Beginning connection test of guild: " + str(guild_info._id))
        for (link_type, test_link) in test_links.items():
            wipe_playlist(guild_info.all_time_playlist_uri)
            wipe_playlist(guild_info.recent_playlist_uri)
            wipe_playlist(guild_info.buffer_playlist_uri)

            await asyncio.sleep(5)

            # Confirm successful all-time playlist wipe
            try:
                if playlist_tracks := sp.playlist_tracks(guild_info.all_time_playlist_uri)['items']:
                    logging.error("Failed to clear playlist id: " + 
                        guild_info.all_time_playlist_uri +
                        ". The following songs remain on the playlist:\n" +
                        str(playlist_tracks)
                    )
                    continue

            except spotipy.SpotifyException:
                logging.error("Exception raised when attempting to clear playlist id: "+
                    guild_info.all_time_playlist_uri,
                    exc_info=True
                )
                continue
            
            if not (channel := discord_client.get_channel(guild_info.testing_channel_id)):
                logging.error("Cannot find Discord channel with id: " + 
                    str(guild_info.testing_channel_id) +
                    " - check that discord bot has been added to server."
                    " Follow Discord OAuth process described in readme to add bot to server.")
                continue

            # Message channel
            await channel.send("!debug " + test_link)

            await asyncio.sleep(5)

            # Confirm songs were successfully added
            try:
                if not(playlist_tracks := sp.playlist_tracks(guild_info.all_time_playlist_uri)['items']):
                    logging.error("Failed to add songs from uri: " +
                        guild_info.all_time_playlist_uri +
                        ". Playlist appears empty"
                    )
                    continue
                
                if link_type == "track":
                    if test_link != playlist_tracks[0]['track']['external_urls']['spotify']:
                        logging.error("Track id: " +
                            test_link +
                            "was not successfully added. Current playlist tracks: " +
                            str(playlist_tracks) 
                        )
                
                elif link_type == "album":
                    if test_link != playlist_tracks[0]['track']['album']['external_urls']['spotify']:
                        logging.error("Album id: " +
                            test_link +
                            "was not successfully added. Current playlist tracks: " +
                            str(playlist_tracks) 
                        )

                elif link_type == "artist":
                    if test_link != playlist_tracks[0]['track']['artists'][0]['external_urls']['spotify']:
                        logging.error("Artist id: " +
                            test_link +
                            "was not successfully added. Current playlist tracks: " +
                            str(playlist_tracks) 
                        )

                logging.info("Connection test successful for link: " + test_link)

            except spotipy.SpotifyException:
                logging.error("Exception raised when attempting to add uri: " +
                    test_link +
                    " to playlist id: " +
                    guild_info.all_time_playlist_uri,
                    exc_info=True
                )


# Start Discord bot
discord_client.run(secrets.discord.token)
