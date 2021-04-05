from django import forms

from .models import Guild, Channel

class GuildForm(forms.ModelForm):
    class Meta:
        model = Guild
        fields = [
            'all_time_playlist_uri',
            'recent_playlist_uri',
            'buffer_playlist_uri'
        ]