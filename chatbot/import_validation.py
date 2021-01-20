import json
import validators
import sys
import os
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def validate_secrets():
    secrets = {}

    # Environment variables
    try:
        environment_variables = [
            "DISCORD_TOKEN",
            "SPOTIFY_CLIENT_ID",
            "SPOTIFY_CLIENT_SECRET",
            "SPOTIFY_REDIRECT_URI",
            "MONGO_HOSTNAME",
            "MONGO_PORT",
            "MONGO_INITDB_ROOT_USERNAME",
            "MONGO_INITDB_ROOT_PASSWORD"
        ]

        for var in environment_variables:
            secrets[var] = os.environ[var]
        
        secrets['MONGO_PORT'] = int(secrets['MONGO_PORT'])

    except KeyError(e):
        raise type(e)("Environment is missing variable " + var)

    assert type(secrets['DISCORD_TOKEN']) == str, \
        "DISCORD_TOKEN is not a string"
    
    assert type(secrets['SPOTIFY_CLIENT_ID']) == str, \
        "SPOTIFY_CLIENT_ID is not a string"
    
    assert type(secrets['SPOTIFY_CLIENT_SECRET']) == str, \
        "SPOTIFY_CLIENT_SECRET is not a string"
    
    assert type(secrets['SPOTIFY_REDIRECT_URI']) == str, \
        "SPOTIFY_REDIRECT_URI is not a string"

    assert validators.url(secrets['SPOTIFY_REDIRECT_URI']), \
        "SPOTIFY_REDIRECT_URI is not a valid URL"

    assert type(secrets['MONGO_HOSTNAME']) == str, \
        "MONGO_HOSTNAME is not a string"

    assert type(secrets['MONGO_PORT']) == int, \
        "MONGO_PORT is not an integer"
    
    assert type(secrets['MONGO_INITDB_ROOT_USERNAME']) == str, \
        "MONGO_INITDB_ROOT_USERNAME is not a string"
    
    assert type(secrets['MONGO_INITDB_ROOT_PASSWORD']) == str, \
        "MONGO_INITDB_ROOT_PASSWORD is not a string"
        
    # RSA keys
    secrets['RSA_PRIVATE_KEY'] = serialization.load_pem_private_key(
        os.environb[b"RSA_PRIVATE_KEY"],
        password=None,
        backend=default_backend()
    )

    secrets['RSA_PUBLIC_KEY'] = serialization.load_pem_public_key(
        os.environb[b"RSA_PUBLIC_KEY"],
        backend=default_backend()
    )

    return secrets

def get_missing_property(e):
    # Pick out which property is missing
    split_point = str(e).rfind("'", 0, len(str(e)) - 1 ) + 1
    missing_prop = str(e)[split_point:len(str(e)) - 1]
    return missing_prop