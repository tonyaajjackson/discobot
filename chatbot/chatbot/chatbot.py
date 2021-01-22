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

from import_validation import validate_secrets
from spotify_custom import MongoCacheHandler, SpotifyCustom

import pymongo

# Environment Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s")


# Set up secrets
secrets = validate_secrets()

# Set up MongoDB connection
logging.info("Trying to connect to mongodb at: " + secrets['MONGO_HOSTNAME'] +
    " on port " + str(secrets['MONGO_PORT']))
client = pymongo.MongoClient(
    host=secrets['MONGO_HOSTNAME'],
    port=secrets['MONGO_PORT'],
    username=secrets['MONGO_INITDB_ROOT_USERNAME'],
    password=secrets['MONGO_INITDB_ROOT_PASSWORD']
)

try:
    client.server_info()
except pymongo.errors.ServerSelectionTimeoutError:
    logging.fatal("Could not connect to mongodb.", exc_info=True)
    sys.exit()

logging.info("Successfully connected to mongodb.")
config = client.discobot.config
guilds = client.discobot.guilds


# Print cron configuration to debug
logging.info("Current datetime is: " + str(datetime.now()))
logging.info("Playlist update is scheduled to run: " + cron_descriptor.get_description(config.find_one()["playlist_update_cron_expr"]))
logging.info("Next playlist update scheduled for: " + str(croniter(config.find_one()["playlist_update_cron_expr"]).get_next(datetime)))
logging.info("Monitoring test is scheduled to run: " + cron_descriptor.get_description(config.find_one()["testing_cron_expr"]))
logging.info("Next playlist update scheduled for: " + str(croniter(config.find_one()["testing_cron_expr"]).get_next(datetime)))

spotipy_scope = (
    'playlist-modify-public' + ' ' +
    'playlist-modify-private'
)

# Set up discord connection
discord_client = discord.Client()
spotify_link_regex = re.compile(r"https:\/\/open.spotify.com\/([^\n ]+)\/([A-Za-z0-9]{22})")

# Discord functions
@discord_client.event
async def on_ready():
    logging.info(f'{discord_client.user} is connected')

    # Get a testing guild for testing the connection to Spotify
    testing_guild = guilds.find_one({"is_connection_testing_guild": True})

    cache_handler = MongoCacheHandler(
        client=client,
        username=testing_guild['username'],
        private_key=secrets['RSA_PRIVATE_KEY'],
        public_key=secrets['RSA_PUBLIC_KEY']
    )

    sp = SpotifyCustom(
        auth_manager=SpotifyOAuth(
            client_id=secrets['SPOTIFY_CLIENT_ID'],
            client_secret=secrets['SPOTIFY_CLIENT_SECRET'],
            redirect_uri=secrets['SPOTIFY_REDIRECT_URI'],
            scope=spotipy_scope,
            open_browser=False,
            cache_handler=cache_handler
        )
    )

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
        guild_info = guilds.find_one({"guild_id": message.guild.id})
        # guild_info = [guild for guild in config.find_one()["guilds"] if guild._id == message.guild.id][0]
    except IndexError:
        logging.error("Received message from guild_id: " + str(message.guild.id) + " but no corresponding guild was found in guilds. Ignoring message.")
        return

    if message.author == discord_client.user and message.content[0:6] != "!debug": return
    if message.channel.id not in guild_info['monitoring_channel_ids']: return

    cache_handler = MongoCacheHandler(
        client=client,
        username=guild_info['username'],
        private_key=secrets['RSA_PRIVATE_KEY'],
        public_key=secrets['RSA_PUBLIC_KEY']
    )

    sp = SpotifyCustom(
        auth_manager=SpotifyOAuth(
            client_id=secrets['SPOTIFY_CLIENT_ID'],
            client_secret=secrets['SPOTIFY_CLIENT_SECRET'],
            redirect_uri=secrets['SPOTIFY_REDIRECT_URI'],
            scope=spotipy_scope,
            open_browser=False,
            cache_handler=cache_handler
        )
    )
    
    if links :=spotify_link_regex.findall(message.content):
        for link in links:
            link_type = link[0]
            link_id = link[1]

            if link_type == "track":
                sp.add_if_unique_tracks(guild_info['all_time_playlist_uri'], [link_id])
                sp.add_if_unique_tracks(guild_info['buffer_playlist_uri'], [link_id])

            if link_type == "album":
                try:
                    album_track_ids = [item['id'] for item in sp.album_tracks(link_id)['items']]
                except spotipy.exceptions.SpotifyException:
                    logging.exception("Error in getting album tracks", exc_info=True)
                    break

                sp.add_if_unique_tracks(guild_info['all_time_playlist_uri'], album_track_ids)
                sp.add_if_unique_tracks(guild_info['buffer_playlist_uri'], album_track_ids)

            if link_type == "artist":
                try:
                    top_song_ids = [item['id'] for item in sp.artist_top_tracks(link_id)['tracks']]
                except spotipy.exceptions.SpotifyException:
                    logging.exception("Error in getting artist tracks", exc_info=True)
                    break

                sp.add_if_unique_tracks(guild_info['all_time_playlist_uri'], top_song_ids)
                sp.add_if_unique_tracks(guild_info['buffer_playlist_uri'], top_song_ids)


@aiocron.crontab(config.find_one()["playlist_update_cron_expr"])
async def load_recent_playlist():
    for guild_info in guilds.find():
        logging.info("Updating guild with id: " + str(guild_info["guild_id"]))
        logging.info("Attempting to get Spotify Auth token for user: " + guild_info["username"])
        cache_handler = MongoCacheHandler(
            client=client,
            username=guild_info['username'],
            private_key=secrets['RSA_PRIVATE_KEY'],
            public_key=secrets['RSA_PUBLIC_KEY']
        )

        sp = SpotifyCustom(
            auth_manager=SpotifyOAuth(
                client_id=secrets['SPOTIFY_CLIENT_ID'],
                client_secret=secrets['SPOTIFY_CLIENT_SECRET'],
                redirect_uri=secrets['SPOTIFY_REDIRECT_URI'],
                scope=spotipy_scope,
                open_browser=False,
                cache_handler=cache_handler
            )
        )
        
        sp.wipe_playlist(guild_info['recent_playlist_uri'])
        sp.copy_all_playlist_tracks(
            guild_info['buffer_playlist_uri'],
            guild_info['recent_playlist_uri']
        )
        sp.wipe_playlist(guild_info['buffer_playlist_uri'])

        if not (channel := discord_client.get_channel(guild_info['notify_channel_id'])):
            logging.error("Cannot find Discord channel with id: " + 
                str(guild_info['notify_channel_id']) +
                " - check that discord bot has been added to server."
                " Follow Discord OAuth process described in readme to add bot to server.")
            break

        # Message chat
        await channel.send("Check out all the songs shared recently!\n" +
            "https://open.spotify.com/playlist/" + 
            guild_info['recent_playlist_uri'][len("spotify:playlist:"):]
        )
        
        await channel.send("You can also find all songs ever shared here:\n" + 
            "https://open.spotify.com/playlist/" + 
            guild_info['all_time_playlist_uri'][len("spotify:playlist:"):]
        )


@aiocron.crontab(config.find_one()["testing_cron_expr"])
async def monitor_connection():
    debug_guilds = guilds.find({"is_connection_testing_guild": True})

    test_links = {
        "track" :   "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",
        "album" :   "https://open.spotify.com/album/6N9PS4QXF1D0OWPk0Sxtb4",
        "artist":   "https://open.spotify.com/artist/0gxyHStUsqpMadRV0Di1Qt"
    }

    for guild_info in debug_guilds:
        logging.info("Beginning connection test of guild: " + str(guild_info['guild_id']))

        logging.info("Attempting to get Spotify Auth token for user: " + guild_info["username"])
        cache_handler = MongoCacheHandler(
            client=client,
            username=guild_info['username'],
            private_key=secrets['RSA_PRIVATE_KEY'],
            public_key=secrets['RSA_PUBLIC_KEY']
        )

        sp = SpotifyCustom(
            auth_manager=SpotifyOAuth(
                client_id=secrets['SPOTIFY_CLIENT_ID'],
                client_secret=secrets['SPOTIFY_CLIENT_SECRET'],
                redirect_uri=secrets['SPOTIFY_REDIRECT_URI'],
                scope=spotipy_scope,
                open_browser=False,
                cache_handler=cache_handler
            )
        )
        for (link_type, test_link) in test_links.items():
            sp.wipe_playlist(guild_info['all_time_playlist_uri'])
            sp.wipe_playlist(guild_info['recent_playlist_uri'])
            sp.wipe_playlist(guild_info['buffer_playlist_uri'])

            await asyncio.sleep(5)

            # Confirm successful all-time playlist wipe
            try:
                if playlist_tracks := sp.playlist_tracks(guild_info['all_time_playlist_uri'])['items']:
                    logging.error("Failed to clear playlist id: " + 
                        guild_info['all_time_playlist_uri'] +
                        ". The following songs remain on the playlist:\n" +
                        str(playlist_tracks)
                    )
                    continue

            except spotipy.SpotifyException:
                logging.error("Exception raised when attempting to clear playlist id: "+
                    guild_info['all_time_playlist_uri'],
                    exc_info=True
                )
                continue
            
            if not (channel := discord_client.get_channel(guild_info['testing_channel_id'])):
                logging.error("Cannot find Discord channel with id: " + 
                    str(guild_info['testing_channel_id']) +
                    " - check that discord bot has been added to server."
                    " Follow Discord OAuth process described in readme to add bot to server.")
                continue

            # Message channel
            await channel.send("!debug " + test_link)

            await asyncio.sleep(5)

            # Confirm songs were successfully added
            try:
                if not(playlist_tracks := sp.playlist_tracks(guild_info['all_time_playlist_uri'])['items']):
                    logging.error("Failed to add songs from uri: " +
                        guild_info['all_time_playlist_uri'] +
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
                    guild_info['all_time_playlist_uri'],
                    exc_info=True
                )


# Start Discord bot
discord_client.run(secrets['DISCORD_TOKEN'])
