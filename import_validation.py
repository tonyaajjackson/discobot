import json
from types import SimpleNamespace
import sys
from croniter import croniter
import re
import validators

spotify_playlist_regex = re.compile(r"spotify:playlist:[A-Za-z0-9]{22}$")

def validate_config(config_path):
    with open(config_path) as f:
        config = json.load(f, object_hook=lambda d:SimpleNamespace(**d))
        # Lambda above makes JSON load as object, not dictionary.
        # Source: https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object

    try: 
        assert type(config.guilds) == list, \
            "config.guilds is not a list"

        assert type(config.playlist_update_cron_expr) == str, \
            "config.playlist_update_cron_expr is not a string"
        
        assert croniter.is_valid(config.playlist_update_cron_expr), \
            "config.playlist_update_cron_expr is not a valid cron expression"
        
        assert type(config.monitoring_cron_expr) == str, \
            "config.monitoring_cron_expr is not a string"
        
        assert croniter.is_valid(config.monitoring_cron_expr), \
            "config.monitoring_cron_expr is not a valid cron expression"

    except AttributeError as e:
        raise type(e)("Config.json is missing property " + get_missing_property(e))

    for (num, guild) in enumerate(config.guilds):
        try:
            assert type(guild._id) == int, \
                "_id of guild #" + str(num) + " is not an integer"

            assert type(guild.channel_id) == int, \
                "channel_id of guild #" + str(num) + " is not an integer"
            
            playlists = {
                "all_time_playlist_uri": guild.all_time_playlist_uri,
                "recent_playlist_uri": guild.recent_playlist_uri,
                "buffer_playlist_uri": guild.buffer_playlist_uri
            }

            for (name, playlist) in playlists.items():
                assert type(playlist) == str, \
                    name + " of guild #" + str(num) + " is not a string"

                assert spotify_playlist_regex.findall(playlist) != [], \
                    name + " of guild #" + str(num) + " is not a valid spotify playlist uri"
            
            assert type(guild.is_connection_testing_guild) == bool, \
                "is_connection_testing_guild of guild #" + str(num) + " is not a boolean"
            
        except AttributeError as e:
            raise type(e)("Guild entry #" + str(num) + " in config.json is missing property " + get_missing_property(e))

    return config

def validate_secrets(secrets_path):
    with open("secrets.json") as f:
        secrets = json.load(f, object_hook=lambda d:SimpleNamespace(**d))

    try:
        assert type(secrets.discord.token) == str, \
            "discord.token is not a string"
        
        assert type(secrets.spotipy.client_id) == str, \
            "spotipy.client_id is not a string"
        
        assert type(secrets.spotipy.secret) == str, \
            "spotipy.secret is not a string"
        
        assert type(secrets.spotipy.redirect_uri) == str, \
            "spotipy.redirect_uri is not a string"

        assert validators.url(secrets.spotipy.redirect_uri), \
            "spotipy.redirect_uri is not a valid URL"

    except AttributeError as e:
        raise type(e)("Secrets.json is missing property " + get_missing_property(e))

    return secrets

def get_missing_property(e):
    # Pick out which property is missing
    split_point = str(e).rfind("'", 0, len(str(e)) - 1 ) + 1
    missing_prop = str(e)[split_point:len(str(e)) - 1]
    return missing_prop