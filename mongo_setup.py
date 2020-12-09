# OS/sys
import sys
from os import path

# Mongo
from pymongo import MongoClient
from pprint import pprint

# Discobot
from import_validation import validate_config, validate_guilds, validate_secrets

# Get config folder location from command line option
if len(sys.argv) > 2:
    if sys.argv[1] == "--path":
        config_folder = sys.argv[2]
else:
    config_folder = "./config/"

if not path.exists(config_folder):
    print("Invalid path: " + config_folder)
    sys.exit()

# Load files
config_path = path.join(config_folder, "config.json")
secrets_path = path.join(config_folder, "secrets.json")
guilds_path = path.join(config_folder, "guilds.json")

config = validate_config(config_path)
secrets = validate_secrets(secrets_path)
guilds = validate_guilds(guilds_path)


connection = MongoClient('mongo-discobot', 27017)

if config['database'] in connection.list_database_names():
    response = input(
        "Database " + str(config['database']) +
        " is not blank! Are you sure you want to wipe all data and load config files? [y/N]\n"
    )

    if response.lower() != 'y':
        sys.exit()

    if config['database'] == "prod":
        response = input(
            "You're attempting to overwrite the prod database!\n" +
            "There is no way to recover this data after deletion\n" +
            "Please type \"overwrite-prod\" to proceed with overwriting production database\n"
        )
        if response.lower() != "overwrite-prod":
            sys.exit()

    connection.drop_database(config['database'])


db = connection[config['database']]

config_id = db['config'].insert_one(config)
secrets_id = db['secrets'].insert_one(secrets)
guilds_id = db['guilds'].insert_many(guilds)