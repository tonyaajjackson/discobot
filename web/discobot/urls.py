from django.urls import path

from . import views

urlpatterns = [
    path('', views.login, name='login'),
    path('authorize/discord', views.authorize_discord, name="authorize_discord"),
    path('add_bot', views.add_bot, name="add_bot")
]