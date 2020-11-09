import json
from types import SimpleNamespace
import sys

def validate_config(config_path):
    with open(config_path) as f:
        config = json.load(f, object_hook=lambda d:SimpleNamespace(**d))
        # Lambda above makes JSON load as object, not dictionary.
        # Source: https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object

    assert type(config.guilds) == list

    for (num, guild) in enumerate(config.guilds):
        try:
            assert type(guild._id) == int
            assert type(guild.channel_id) == int
            assert type(guild.all_time_playlist_uri) == str
            assert type(guild.recent_playlist_uri) == str
            assert type(guild.buffer_playlist_uri) == str
            assert type(guild.is_connection_testing_guild) == bool
        except AttributeError as e:
            # Pick out which property is missing
            split_point = str(e).rfind("'", 0, len(str(e)) - 1 ) + 1
            missing_var = str(e)[split_point:len(str(e)) - 1]
            raise type(e)("Guild entry #" + str(num) + " in config.json is missing property " + missing_var)
    
    assert type(config.playlist_update_cron_expr) == str
    assert type(config.monitoring_cron_expr) == str

    return config

def validate_secrets(secrets_path):
    with open("secrets.json") as f:
        secrets = json.load(f, object_hook=lambda d:SimpleNamespace(**d))

    return secrets