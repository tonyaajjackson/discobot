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
from spotify_custom import PostgreCacheHandler, SpotifyCustom

import psycopg2
import peewee as pw
from models import Channel, Config, Guild, User, db

# Environment Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s")


# Set up secrets
secrets = validate_secrets()

# Set up database connection
logging.info("Trying to connect to " + secrets['db_string'])
db.init(
    database=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["POSTGRES_HOSTNAME"],
    port=os.environ["POSTGRES_PORT"]
)

try:
    db.get_tables()
except psycopg2.OperationalError:
    logging.fatal("Could not connect to database", exc_info=True)
    sys.exit()

logging.info("Successfully connected to database.")

# Print cron configuration to debug
logging.info("Current datetime is: " + str(datetime.now()))
logging.info("Playlist update is scheduled to run: " + cron_descriptor.get_description(Config.get().playlist_update_cron_expr))
logging.info("Next playlist update scheduled for: " + str(croniter(Config.get().playlist_update_cron_expr).get_next(datetime)))
logging.info("Monitoring test is scheduled to run: " + cron_descriptor.get_description(Config.get().testing_cron_expr))
logging.info("Next playlist update scheduled for: " + str(croniter(Config.get().testing_cron_expr).get_next(datetime)))

spotipy_scope = (
    'playlist-modify-public' + ' ' +
    'playlist-modify-private'
)

# Set up discord connection
discord_client = discord.Client()
spotify_link_regex = re.compile(r"https:\/\/open.spotify.com\/([^\n ]+)\/([A-Za-z0-9]{22})")

# ====== Discord Events ======
@discord_client.event
async def on_ready():
    logging.info(f'{discord_client.user} is connected')

    # Find the test user that owns a guild with a testing channel
    test_user = (User
        .select(User)
        .join(Guild, pw.JOIN.LEFT_OUTER)
        .join(Channel, pw.JOIN.LEFT_OUTER)
        .where(Channel.test == True)
        .execute()
    )[0]

    cache_handler = PostgreCacheHandler(
        user=test_user,
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
        guild = Guild.get(Guild.id == message.guild.id)
    except Guild.DoesNotExist:
        logging.error("Received message from guild_id: " + str(message.guild.id) + " but no corresponding guild was found in guilds. Ignoring message.")
        return

    if message.author == discord_client.user and message.content[0:6] != "!debug": return
    monitoring_channel_ids = [channel.id for channel in guild.channels.select(Channel.id).where(Channel.monitor == True)]
    if message.channel.id not in monitoring_channel_ids: return

    cache_handler = PostgreCacheHandler(
        user=guild.user,
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
                sp.add_if_unique_tracks(guild.all_time_playlist_uri, [link_id])
                sp.add_if_unique_tracks(guild.buffer_playlist_uri, [link_id])

            if link_type == "album":
                try:
                    album_track_ids = [item['id'] for item in sp.album_tracks(link_id)['items']]
                except spotipy.exceptions.SpotifyException:
                    logging.exception("Error in getting album tracks", exc_info=True)
                    break

                sp.add_if_unique_tracks(guild.all_time_playlist_uri, album_track_ids)
                sp.add_if_unique_tracks(guild.buffer_playlist_uri, album_track_ids)

            if link_type == "artist":
                try:
                    top_song_ids = [item['id'] for item in sp.artist_top_tracks(link_id)['tracks']]
                except spotipy.exceptions.SpotifyException:
                    logging.exception("Error in getting artist tracks", exc_info=True)
                    break

                sp.add_if_unique_tracks(guild.all_time_playlist_uri, top_song_ids)
                sp.add_if_unique_tracks(guild.buffer_playlist_uri, top_song_ids)

@discord_client.event
async def on_guild_join(guild):
    # Get user that added bot to guild
    entries = await guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add).flatten()
    bot_add_entry = [entry for entry in entries if entry.target == discord_client.user][0]
    discord_user = bot_add_entry.user

    User.get_or_create(id=discord_user.id)

    logging.info("Adding new guild: " + str(guild.id) + " - " + str(guild.name))
    new_guild = Guild(
        id=guild.id,
        user=guild.owner_id
    )
    new_guild.save(force_insert=True)

    
    print("breakpoint")

@discord_client.event
async def on_guild_remove(guild):
    logging.info("Removed from guild: " + str(guild.id))
    logging.info("Deleting channels for guild: " + str(guild.id))
    Channel.delete().where(Channel.guild_id == guild.id).execute()
    logging.info("Deleting guild: " + str(guild.id))
    Guild.delete_by_id(guild.id)


# ===== Scheduled =====
@aiocron.crontab(Config.get().playlist_update_cron_expr)
async def load_recent_playlist():
    for guild in Guild.select():
        logging.info("Updating guild with id: " + str(guild.id))
        logging.info("Attempting to get Spotify Auth token for user: " + str(guild.user.id))
        cache_handler = PostgreCacheHandler(
            user = guild.user,
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
        
        sp.wipe_playlist(guild.recent_playlist_uri)
        sp.copy_all_playlist_tracks(
            guild.buffer_playlist_uri,
            guild.recent_playlist_uri
        )
        sp.wipe_playlist(guild.buffer_playlist_uri)

        notify_channel_ids = [channel.id for channel in guild.channels.select(Channel.id).where(Channel.notify == True)]

        for notify_channel_id in notify_channel_ids:
            if not (channel := discord_client.get_channel(notify_channel_id)):
                logging.error("Cannot find Discord channel with id: " + 
                    str(notify_channel_id) +
                    " - check that discord bot has been added to server."
                    " Follow Discord OAuth process described in readme to add bot to server.")
                break

            # Message chat
            await channel.send("Check out all the songs shared recently!\n" +
                "https://open.spotify.com/playlist/" + 
                guild.recent_playlist_uri[len("spotify:playlist:"):]
            )
            
            await channel.send("You can also find all songs ever shared here:\n" + 
                "https://open.spotify.com/playlist/" + 
                guild.all_time_playlist_uri[len("spotify:playlist:"):]
            )


@aiocron.crontab(Config.get().testing_cron_expr)
async def monitor_connection():
    debug_guilds = Guild.select().join(Channel).where(Channel.test == True)

    test_links = {
        "track" :   "https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC",
        "album" :   "https://open.spotify.com/album/6N9PS4QXF1D0OWPk0Sxtb4",
        "artist":   "https://open.spotify.com/artist/0gxyHStUsqpMadRV0Di1Qt"
    }

    for guild in debug_guilds:
        logging.info("Beginning connection test of guild: " + str(guild.id))

        logging.info("Attempting to get Spotify Auth token for user: " + str(guild.user.id))
        cache_handler = PostgreCacheHandler(
            user=guild.user,
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
            sp.wipe_playlist(guild.all_time_playlist_uri)
            sp.wipe_playlist(guild.recent_playlist_uri)
            sp.wipe_playlist(guild.buffer_playlist_uri)

            await asyncio.sleep(5)

            # Confirm successful all-time playlist wipe
            try:
                if playlist_tracks := sp.playlist_tracks(guild.all_time_playlist_uri)['items']:
                    logging.error("Failed to clear playlist id: " + 
                        guild.all_time_playlist_uri +
                        ". The following songs remain on the playlist:\n" +
                        str(playlist_tracks)
                    )
                    continue

            except spotipy.SpotifyException:
                logging.error("Exception raised when attempting to clear playlist id: "+
                    guild.all_time_playlist_uri,
                    exc_info=True
                )
                continue
            
            channel = discord_client.get_channel(
                Channel.select(Channel.id).where(
                    (Channel.test == True) &
                    (Channel.guild == guild)
                )[0].id
            )

            if not channel:
                logging.error("Cannot find Discord channel with id: " + 
                    str(channel.id) +
                    " - check that discord bot has been added to server."
                    " Follow Discord OAuth process described in readme to add bot to server.")
                continue

            # Message channel
            await channel.send("!debug " + test_link)

            await asyncio.sleep(5)

            # Confirm songs were successfully added
            try:
                if not(playlist_tracks := sp.playlist_tracks(guild.all_time_playlist_uri)['items']):
                    logging.error("Failed to add songs from uri: " +
                        guild.all_time_playlist_uri +
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
                    guild.all_time_playlist_uri,
                    exc_info=True
                )


# Start Discord bot
discord_client.run(secrets['DISCORD_TOKEN'])
