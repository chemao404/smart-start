from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.contrib import admin
from django.conf import settings

app_name = 'users'

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
]