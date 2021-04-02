from django.urls import path

from . import views

urlpatterns = [
    path('', views.add_bot, name="add_bot"),
    path('profile', views.profile_redirect, name="profile_redirect"),
    path('user', views.create_user, name="create_user"),
    path('user/<int:user_id>', views.manage_user, name="manage_user")
]