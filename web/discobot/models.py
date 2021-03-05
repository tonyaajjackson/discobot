from django.db import models

class Config(models.Model):
    id = models.AutoField(primary_key=True)
    playlist_update_cron_expr = models.CharField(max_length=255)
    testing_cron_expr = models.CharField(max_length=255)

class User(models.Model):
    id = models.AutoField(primary_key=True)
    # id will need to become models.BigIntegerField(primary_key=True) when Discord user_id is implemented
    username = models.CharField(max_length=255)
    spotify_auth_token = models.BinaryField(null=True )
    encrypted_fernet_key = models.BinaryField(null=True)
    

class Guild(models.Model):
    id = models.BigIntegerField(primary_key=True)
    all_time_playlist_uri = models.CharField(max_length=255)
    recent_playlist_uri = models.CharField(max_length=255)
    buffer_playlist_uri = models.CharField(max_length=255)
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)

class Channel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    monitor = models.BooleanField()
    notify = models.BooleanField()
    test = models.BooleanField()

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)