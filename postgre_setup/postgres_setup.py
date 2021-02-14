import argparse
import json
import os
import sys

import peewee as pw


# CLI Arg parsing
parser = argparse.ArgumentParser(
    usage="%(prog)s [OPTION] [VALUE]"
)
parser.add_argument(
    "--path",
    help="Path to the folder from which to load files",
    action="store",
    required=True
)

args = parser.parse_args()


# Peewee PostgreSQL connection setup
db = pw.PostgresqlDatabase(os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["POSTGRES_HOSTNAME"],
    port=os.environ["POSTGRES_PORT"]
)


# Models
class Config(pw.Model):
    id = pw.AutoField()
    playlist_update_cron_expr = pw.CharField()
    testing_cron_expr = pw.CharField()

    class Meta:
        database = db
        table_name = "discobot_config"

class User(pw.Model):
    id = pw.AutoField()
    # id will need to become pw.BigIntegerField(primary_key=True) when Discord user_id is implemented
    username = pw.CharField()
    spotify_auth_token = pw.BlobField(null=True )
    encrypted_fernet_key = pw.BlobField(null=True)
    
    class Meta:
        database = db
        table_name = "discobot_user"

class Guild(pw.Model):
    id = pw.BigIntegerField(primary_key=True)
    all_time_playlist_uri = pw.CharField()
    recent_playlist_uri = pw.CharField()
    buffer_playlist_uri = pw.CharField()
    
    user = pw.ForeignKeyField(User, backref="guilds")

    class Meta:
        database = db
        table_name = "discobot_guild"

class Channel(pw.Model):
    id = pw.BigIntegerField(primary_key=True)
    monitor = pw.BooleanField()
    notify = pw.BooleanField()
    test = pw.BooleanField()

    guild = pw.ForeignKeyField(Guild, backref="channels")

    class Meta:
        database = db
        table_name = "discobot_channel"


# Data for insertion into SQL database
tables = [
        Config,
        User,
        Guild,
        Channel
]

data = {}
for table in tables:
    table_name = table.__name__.lower()
    with open(os.path.join(args.path, table_name + ".json")) as f:
        data[table_name] = json.loads(f.read())


# # Wipe old data
db.connect()
if db.get_tables():
    response = input(
        "Database at " + os.environ["POSTGRES_HOSTNAME"] +
        " is not blank! Are you sure you want to wipe all data and load config files? [y/N]\n"
    )
    if response.lower() != 'y':
        sys.exit()

    if "prod" in os.environ["POSTGRES_HOSTNAME"]:
        response = input(
            "You're attempting to overwrite the prod database!\n" +
            "There is no way to recover this data after deletion\n" +
            "Please type \"overwrite-prod\" to proceed with overwriting production database\n"
        )
        if response.lower() != "overwrite-prod":
            sys.exit()
    
    db.drop_tables(tables)
    

# Load new data
db.create_tables(tables)
Config(**data['config']).save()

for user in data['user']:
    User(**user).save()

for guild in data['guild']:
    Guild(**guild).save(force_insert=True)
    # Force insert as primary key is coming from json and not autogenerated
    # http://docs.peewee-orm.com/en/latest/peewee/models.html#id4

for channel in data['channel']:
    Channel(**channel).save(force_insert=True)


# Verify data loaded correctly
config_db = [ config for config in Config.select().dicts() ][0]
for key in data['config']:
    assert config_db[key] == data['config'][key]

tables_db = [
    User,
    Guild,
    Channel
]

# User, Guild, and Channels can all be checked together as they're all
# lists of dictionaries
db_test = {}
for table in tables_db:
    table_name = table.__name__.lower()
    db_test[table_name] = [ val for val in table.select().dicts() ]

    for (index, item) in enumerate(data[table_name]):
        for key in item:
            # Compare everything as a string. Type checking is enforced
            # by peewee's types so the only check is that the data
            # arrived at the database
            assert str(db_test[table_name][index][key]) == str(item[key])
