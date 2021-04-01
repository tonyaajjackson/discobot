import peewee as pw

db = pw.PostgresqlDatabase(None)

# Models
class Config(pw.Model):
    id = pw.AutoField()
    playlist_update_cron_expr = pw.CharField()
    testing_cron_expr = pw.CharField()

    class Meta:
        database = db
        table_name = "discobot_config"

class User(pw.Model):
    # Stand-in for the Django Users table so that the foreign key
    # relationship works
    class Meta:
        database = db
        table_name = "auth_user"

class Profile(pw.Model):
    id = pw.BigIntegerField(primary_key=True)
    username = pw.CharField()
    spotify_auth_token = pw.BlobField(null=True )
    encrypted_fernet_key = pw.BlobField(null=True)

    user_id = pw.ForeignKeyField(User, backref="profile", null=True)
    
    class Meta:
        database = db
        table_name = "discobot_profile"

class Guild(pw.Model):
    id = pw.BigIntegerField(primary_key=True)
    all_time_playlist_uri = pw.CharField(null=True)
    recent_playlist_uri = pw.CharField(null=True)
    buffer_playlist_uri = pw.CharField(null=True)
    
    profile = pw.ForeignKeyField(Profile, backref="guilds")

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