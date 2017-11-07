from django.conf.urls import url
from django.contrib import admin
from .views import *

urlpatterns = [
    url(r'^create_contest$', CreateContest.as_view(), name='create_contest'),
    url(r'^contest/([1-9][0-9]*)/$', ContestDetail.as_view(), name='contest'),
    url(r'^$', home, name='home'),
]
