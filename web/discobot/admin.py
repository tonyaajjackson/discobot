from django.contrib import admin

from .models import Config, Channel, Guild, Profile

admin.site.register(Config)
admin.site.register(Channel)
admin.site.register(Guild)
admin.site.register(Profile)