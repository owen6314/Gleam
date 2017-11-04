from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^create_contest$', views.create_contest, name='create_contest'),
    url(r'^contest/([1-9][0-9]*)/$', views.contest, name='pic')
]
