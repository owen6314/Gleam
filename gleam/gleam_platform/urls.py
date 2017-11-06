from django.conf.urls import url
from django.contrib import admin
from .views import *

urlpatterns = [
    url(r'^$', home, name='home'),
    url(r'^create_contest$', create_contest, name='create_contest'),
    url(r'^contest/([1-9][0-9]*)/$', contest, name='pic'),
]
