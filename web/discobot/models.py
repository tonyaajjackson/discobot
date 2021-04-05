from django.db import models
from django.contrib.auth.models import User

class Config(models.Model):
    id = models.AutoField(primary_key=True)
    playlist_update_cron_expr = models.CharField(max_length=255)
    testing_cron_expr = models.CharField(max_length=255)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    id = models.BigIntegerField(primary_key=True)
    username = models.CharField(max_length=255)
    spotify_auth_token = models.BinaryField(null=True)
    encrypted_fernet_key = models.BinaryField(null=True)
    spotify_state = models.CharField(max_length=255, null=True)
    

class Guild(models.Model):
    id = models.BigIntegerField(primary_key=True)
    all_time_playlist_uri = models.CharField(max_length=255)
    recent_playlist_uri = models.CharField(max_length=255)
    buffer_playlist_uri = models.CharField(max_length=255)
    
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

class Channel(models.Model):
    id = models.BigIntegerField(primary_key=True)
    monitor = models.BooleanField()
    notify = models.BooleanField()
    test = models.BooleanField()

    guild = models.ForeignKey(Guild, on_delete=models.CASCADE)