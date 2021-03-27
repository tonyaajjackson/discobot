from django.urls import path

from . import views

urlpatterns = [
    path('', views.add_bot, name="add_bot")
]