import peewee as pw

db = pw.PostgresqlDatabase(None)

# Models
class Config(pw.Model):
    id = pw.AutoField()
    playlist_update_cron_expr = pw.CharField()
    testing_cron_expr = pw.CharField()

    class Meta:
        database = db

class User(pw.Model):
    id = pw.BigIntegerField(primary_key=True)
    username = pw.CharField()
    spotify_auth_token = pw.BlobField(null=True )
    encrypted_fernet_key = pw.BlobField(null=True)
    
    class Meta:
        database = db

class Guild(pw.Model):
    id = pw.BigIntegerField(primary_key=True)
    all_time_playlist_uri = pw.CharField(null=True)
    recent_playlist_uri = pw.CharField(null=True)
    buffer_playlist_uri = pw.CharField(null=True)
    
    user = pw.ForeignKeyField(User, backref="guilds")

    class Meta:
        database = db

class Channel(pw.Model):
    id = pw.BigIntegerField(primary_key=True)
    monitor = pw.BooleanField()
    notify = pw.BooleanField()
    test = pw.BooleanField()

    guild = pw.ForeignKeyField(Guild, backref="channels")

    class Meta:
        database = db