from django.conf.urls import url
from django.contrib import admin
from .views import *

urlpatterns = [
    # url(r'^signup/organizer', OrganizerSignup.as_view(), name='organizer_signup'),
    # url(r'^signup/contestant', ContestantSignup.as_view(), name='contestant_signup'),
    # url(r'^login', LoginView.as_view(), name='login'),
    # url(r'^logout', LogoutView.as_view(), name='logout'),
    # url(r'^user_detail', UserDetailView.as_view(), name='user_detail'),
    # url(r'^create_contest$', CreateContest.as_view(), name='create_contest'),
    # url(r'^contest/([1-9][0-9]*)/$', ContestDetail.as_view(), name='contest_detail'),
    # url(r'^$', HomeView.as_view(), name='home'),

    url(r'^signup/organizer', SignupOrganizerView.as_view(), name='signup-organizer'),
    url(r'^signup/contestant', SignupContestantView.as_view(), name='signup-contestant'),
    url(r'^login/organizer', LoginOrganizerView.as_view(), name='login-organizer'),
    url(r'^login/contestant', LoginContestantView.as_view(), name='login-contestant'),
    url(r'^logout', LogoutView.as_view(), name='logout'),
    url(r'^index', IndexView.as_view(), name='index'),
    url(r'^home/organizer', HomeOrganizerView.as_view(), name='home-organizer'),
    url(r'^home/contestant', HomeContestantView.as_view(), name='home-contestant'),
    url(r'^profile/organizer', ProfileOrganizerView.as_view(), name='profile-organizer'),
    url(r'^profile/contestant', ProfileContestantView.as_view(), name='profile-contestant'),
    url(r'^create-contest', CreateContestView.as_view(), name='create-contest'),
    url(r'^contest-detail/([1-9][0-9]*)/', TournamentDetailOrganizerView.as_view(), name='tournament-detail-organizer'),
    url(r'^tournament-list', TournamentListView.as_view(), name='tournament-list'),
    url(r'^bad-request-400', BadRequestView.as_view(), name='bad-request-400'),
    url(r'^register', RegisterView.as_view(), name='register'),
]
