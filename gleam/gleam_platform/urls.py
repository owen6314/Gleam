from django.conf.urls import url
from django.contrib import admin
from .views import *
import gleam.settings as settings
from .image_manage import serve_image

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
  url(r'^profile/organizer/([1-9][0-9]*)/', ProfileOrganizerView.as_view(), name='profile-organizer'),
  url(r'^profile/contestant/([1-9][0-9]*)/', ProfileContestantView.as_view(), name='profile-contestant'),
  url(r'^create-contest', CreateTournamentView.as_view(), name='create-contest'),
  url(r'^tournament-detail/organizer/([1-9][0-9]*)/', TournamentDetailOrganizerView.as_view(),
      name='tournament-detail-organizer'),
  url(r'^tournament-detail/contestant/([1-9][0-9]*)/', TournamentDetailContestantView.as_view(),
      name='tournament-detail-contestant'),
  url(r'^tournament-list', TournamentListView.as_view(), name='tournament-list'),
  url(r'^edit-tournament/([1-9][0-9]*)/', EditTournamentView.as_view(), name='edit-tournament'),
  url(r'^permission-denied-403', PermissionDeniedView.as_view(), name='403'),
  url(r'^not-found-404', NotFoundView.as_view(), name='404'),
  url(r'^register/([1-9][0-9]*)/', RegisterView.as_view(), name='register'),
  url(r'^quit/([1-9][0-9]*)/', QuitTeamView.as_view(), name='quit'),
  url(r'^{}(?P<path>.*)$'.format(settings.MEDIA_URL[1:]), serve_image, name='serve_image'),
  url(r'^profile-edit/organizer', ProfileEditOrganizerView.as_view(), name='profile-edit-organizer'),
  url(r'^profile-edit/contestant', ProfileEditContestantView.as_view(), name='profile-edit-contestant'),
  url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', activate,
      name='activate'),
  url(r'^contest-leaderboard/organizer/([1-9][0-9]*)/$', ContestLeaderboardOrganizerView.as_view(),
      name='contest-leaderboard-organizer'),
  url(r'^confirmation-email-send/([1-9][0-9]*)/$', SendConfirmationEmailView.as_view(), name='confirmation-email-send'),
]
