import json
from types import SimpleNamespace

def validate_config(config_path):
    with open(config_path) as f:
        config = json.load(f, object_hook=lambda d:SimpleNamespace(**d))
        # Lambda above makes JSON load as object, not dictionary.
        # Source: https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object
    
    return config

def validate_secrets(secrets_path):
    with open("secrets.json") as f:
        secrets = json.load(f, object_hook=lambda d:SimpleNamespace(**d))

    return secrets