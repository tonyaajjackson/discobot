# OS/sys
import sys
from os import path
import argparse
import json

# Mongo
from pymongo import MongoClient
from pprint import pprint

# Discobot
from import_validation import validate_config, validate_guilds, validate_secrets

# Get config folder location from command line option
parser = argparse.ArgumentParser(
    usage="%(prog)s [OPTION] [VALUE]"
)
parser.add_argument(
    "--path", help="Path to the folder containing config.json, guilds,json, secrets.json",
    action="store"
)

args = parser.parse_args()

if not args.path is None:
    config_folder = args.path
else:
    config_folder = "./config/"

if not path.exists(config_folder):
    print("Invalid path: " + config_folder)
    sys.exit()

# Load files
config_path = path.join(config_folder, "config.json")
guilds_path = path.join(config_folder, "guilds.json")
secrets_path = path.join(config_folder, "secrets.json")
users_path = path.join(config_folder, "users.json")

config = validate_config(config_path)
guilds = validate_guilds(guilds_path)
secrets = validate_secrets(secrets_path)
# Skip import validation for users as loading from JSON is a temporary measure
with open(users_path) as f:
        users = json.load(f)

client = MongoClient(
    host=secrets['mongodb']['uri'],
    username=secrets['mongodb']['username'],
    password=secrets['mongodb']['password']
)

if 'discobot' in client.list_database_names():
    response = input(
        "Database at " + str(secrets['mongodb']['uri']) +
        " is not blank! Are you sure you want to wipe all data and load config files? [y/N]\n"
    )

    if response.lower() != 'y':
        sys.exit()

    if "prod" in secrets['mongodb']['uri']:
        response = input(
            "You're attempting to overwrite the prod database!\n" +
            "There is no way to recover this data after deletion\n" +
            "Please type \"overwrite-prod\" to proceed with overwriting production database\n"
        )
        if response.lower() != "overwrite-prod":
            sys.exit()

    client.drop_database('discobot')


db = client['discobot']

config_id = db['config'].insert_one(config)
guilds_id = db['guilds'].insert_many(guilds)
users_id = db['users'].insert_many(users)