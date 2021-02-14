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
            "POSTGRES_HOSTNAME",
            "POSTGRES_PORT",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_DB"
        ]

        for var in environment_variables:
            secrets[var] = os.environ[var]

    except KeyError:
        raise KeyError("Environment is missing variable " + var)

    # Make Postgre connection string
    secrets['db_string'] = "postgresql://" + \
        os.environ["POSTGRES_USER"] + \
        ":" + \
        os.environ["POSTGRES_PASSWORD"] + \
        "@" + \
        os.environ["POSTGRES_HOSTNAME"] + \
        ":" + \
        os.environ["POSTGRES_PORT"] + \
        "/" + \
        os.environ["POSTGRES_DB"]

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
