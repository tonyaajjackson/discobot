import argparse
import json
import os

import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


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


# SQLAlchemy Classes
Base = declarative_base()
class Config(Base):
    __tablename__ = "config"

    id = sq.Column(sq.Integer, primary_key=True)
    playlist_update_cron_expr = sq.Column(sq.String)
    testing_cron_expr = sq.Column(sq.String)

class User(Base):
    __tablename__ = "users"

    id = sq.Column(sq.BigInteger, primary_key=True)
    username = sq.Column(sq.String)
    spotify_auth_token = sq.Column(sq.LargeBinary)
    encrypted_fernet_key = sq.Column(sq.LargeBinary)

    guilds = relationship("Guild", back_populates="user", cascade="all")

    def __repr__(self):
        return str(self.id) + ": " + self.username

class Guild(Base):
    __tablename__ = "guilds"

    id = sq.Column(sq.BigInteger, primary_key=True)
    all_time_playlist_uri = sq.Column(sq.String)
    recent_playlist_uri = sq.Column(sq.String)
    buffer_playlist_uri = sq.Column(sq.String)
    
    user_id = sq.Column(sq.BigInteger, sq.ForeignKey('users.id'))
    user = relationship("User", back_populates="guilds", cascade="all")

    channels = relationship("Channel", back_populates="guild", cascade="all")

    def __repr__(self):
        return "Discord Guild ID: " + str(self.guild_id)


class Channel(Base):
    __tablename__ = "channels"

    id = sq.Column(sq.BigInteger, primary_key=True)
    monitor = sq.Column(sq.Boolean)
    notify = sq.Column(sq.Boolean)
    test = sq.Column(sq.Boolean)

    guild_id = sq.Column(sq.BigInteger, sq.ForeignKey("guilds.id"))
    guild = relationship("Guild", back_populates="channels", cascade="all")



# Data for insertion into SQL database
tables = [
    'config',
    'users',
    'guilds',
    'channels'
]

data = {}
for table in tables:
    with open(os.path.join(args.path, table + ".json")) as f:
        data[table] = json.loads(f.read())


# PostgreSQL connection
db_string = "postgresql://" + \
            os.environ["POSTGRES_USER"] + \
            ":" + \
            os.environ["POSTGRES_PASSWORD"] + \
            "@" + \
            os.environ["POSTGRES_HOSTNAME"] + \
            ":" + \
            os.environ["POSTGRES_PORT"] + \
            "/" + \
            os.environ["POSTGRES_DB"]

engine = sq.create_engine(db_string)


# Wipe old data
if engine.table_names():
    response = input(
        "Database at " + db_string +
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
    
    Base.metadata.drop_all(engine)

# Load new data
Base.metadata.create_all(engine)

session = sessionmaker(bind=engine)()
session.add(Config(**data['config']))
session.commit()

for user in data['users']:
    session.add(User(**user))
    session.commit()

for guild in data['guilds']:
    session.add(Guild(**guild))
    session.commit()

for channel in data['channels']:
    session.add(Channel(**channel))
    session.commit()