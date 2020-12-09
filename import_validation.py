import json
from types import SimpleNamespace
import sys
from croniter import croniter
import re
import validators

spotify_playlist_regex = re.compile(r"spotify:playlist:[A-Za-z0-9]{22}$")

def validate_config(config_path):
    with open(config_path) as f:
        config = json.load(f)

    try: 
        assert type(config['playlist_update_cron_expr']) == str, \
            "config['playlist_update_cron_expr'] is not a string"
        
        assert croniter.is_valid(config['playlist_update_cron_expr']), \
            "config['playlist_update_cron_expr'] is not a valid cron expression"
        
        assert type(config['testing_cron_expr']) == str, \
            "config['testing_cron_expr'] is not a string"
        
        assert croniter.is_valid(config['testing_cron_expr']), \
            "config['testing_cron_expr'] is not a valid cron expression"

    except AttributeError as e:
        raise type(e)("Config['json'] is missing property " + get_missing_property(e))

    return config

def validate_guilds(guilds_path):
    with open(guilds_path) as f:
        guilds = json.load(f)

    assert type(guilds) == list, \
            "guilds is not a list"

    for (num, guild) in enumerate(guilds):
        try:
            assert type(guild['_id']) == int, \
                "_id of guild #" + str(num) + " is not an integer"

            assert type(guild['monitoring_channel_ids']) == list

            for channel_id in guild['monitoring_channel_ids']:
                assert type(channel_id) == int, \
                    "channel_id of guild #" + str(num) + ", value: " + str(channel_id) + " is not an integer"
            
            assert type(guild['notify_channel_id']) == int

            playlists = {
                "all_time_playlist_uri": guild['all_time_playlist_uri'],
                "recent_playlist_uri": guild['recent_playlist_uri'],
                "buffer_playlist_uri": guild['buffer_playlist_uri']
            }

            for (name, playlist) in playlists.items():
                assert type(playlist) == str, \
                    name + " of guild #" + str(num) + " is not a string"

                assert spotify_playlist_regex.findall(playlist) != [], \
                    name + " of guild #" + str(num) + " is not a valid spotify playlist uri"
            
            assert type(guild['is_connection_testing_guild']) == bool, \
                "is_connection_testing_guild of guild #" + str(num) + " is not a boolean"

            if guild['is_connection_testing_guild']:
                assert type(guild['testing_channel_id']) == int
            else:
                assert guild['testing_channel_id'] is None
            
        except AttributeError as e:
            raise type(e)("Guild entry #" + str(num) + " in config['json'] is missing property " + get_missing_property(e))
    
    return guilds

def validate_secrets(secrets_path):
    with open(secrets_path) as f:
        secrets = json.load(f)

    try:
        assert type(secrets['discord']['token']) == str, \
            "discord.token is not a string"
        
        assert type(secrets['spotipy']['client_id']) == str, \
            "spotipy.client_id is not a string"
        
        assert type(secrets['spotipy']['secret']) == str, \
            "spotipy.secret is not a string"
        
        assert type(secrets['spotipy']['redirect_uri']) == str, \
            "spotipy.redirect_uri is not a string"

        assert validators.url(secrets['spotipy']['redirect_uri']), \
            "spotipy.redirect_uri is not a valid URL"

    except AttributeError as e:
        raise type(e)("Secrets['json'] is missing property " + get_missing_property(e))

    return secrets

def get_missing_property(e):
    # Pick out which property is missing
    split_point = str(e).rfind("'", 0, len(str(e)) - 1 ) + 1
    missing_prop = str(e)[split_point:len(str(e)) - 1]
    return missing_prop