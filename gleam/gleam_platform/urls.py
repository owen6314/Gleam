from django.conf.urls import url
from .common_views import LogoutView, IndexView, PermissionDeniedView, NotFoundView
from .organizer_account_views import SignupOrganizerView, LoginOrganizerView, HomeOrganizerView, ProfileOrganizerView, \
  ProfileEditOrganizerView, AccountEditOrganizerView
from .contestant_account_views import SignupContestantView, LoginContestantView, HomeContestantView, \
  ProfileContestantView, ProfileEditContestantView, activate, SendConfirmationEmailView, AccountEditContestantView
from .organizer_tournament_views import CreateTournamentView, TournamentDetailOrganizerView, EditTournamentView, \
  ContestLeaderboardOrganizerView
from .contestant_tournament_views import TournamentDetailContestantView, TournamentListView, RegisterView,\
  QuitTeamView, KickContestantView, TransferLeaderView, EditTeamNameView
import gleam.settings as settings
from .image_manage import serve_image

urlpatterns = [
  # Commmon Views
  url(r'^logout', LogoutView.as_view(), name='logout'),
  url(r'^index', IndexView.as_view(), name='index'),
  url(r'^permission-denied-403', PermissionDeniedView.as_view(), name='403'),
  url(r'^not-found-404', NotFoundView.as_view(), name='404'),

  # Organizer Account Views
  url(r'^signup/organizer', SignupOrganizerView.as_view(), name='signup-organizer'),
  url(r'^login/organizer', LoginOrganizerView.as_view(), name='login-organizer'),
  url(r'^home/organizer', HomeOrganizerView.as_view(), name='home-organizer'),
  url(r'^profile/organizer/([1-9][0-9]*)/', ProfileOrganizerView.as_view(), name='profile-organizer'),
  url(r'^profile-edit/organizer', ProfileEditOrganizerView.as_view(), name='profile-edit-organizer'),
  url(r'^organizer/account-edit', AccountEditOrganizerView.as_view(), name='organizer-account-edit'),

  # Contestant Account Views
  url(r'^signup/contestant', SignupContestantView.as_view(), name='signup-contestant'),
  url(r'^login/contestant', LoginContestantView.as_view(), name='login-contestant'),
  url(r'^home/contestant', HomeContestantView.as_view(), name='home-contestant'),
  url(r'^profile/contestant/([1-9][0-9]*)/', ProfileContestantView.as_view(), name='profile-contestant'),
  url(r'^profile-edit/contestant', ProfileEditContestantView.as_view(), name='profile-edit-contestant'),
  url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', activate,
      name='activate'),
  url(r'^confirmation-email-send/([1-9][0-9]*)/$', SendConfirmationEmailView.as_view(), name='confirmation-email-send'),
  url(r'^contestant/account-edit', AccountEditContestantView.as_view(), name='contestant-account-edit'),

  # Organizer Tournament Views
  url(r'^create-contest', CreateTournamentView.as_view(), name='create-contest'),
  url(r'^tournament-detail/organizer/([1-9][0-9]*)/', TournamentDetailOrganizerView.as_view(),
      name='tournament-detail-organizer'),
  url(r'^edit-tournament/([1-9][0-9]*)/', EditTournamentView.as_view(), name='edit-tournament'),
  url(r'^contest-leaderboard/organizer/([1-9][0-9]*)/$', ContestLeaderboardOrganizerView.as_view(),
      name='contest-leaderboard-organizer'),

  # Contestant Tournament Views
  url(r'^tournament-detail/contestant/([1-9][0-9]*)/', TournamentDetailContestantView.as_view(),
      name='tournament-detail-contestant'),
  url(r'^tournament-list', TournamentListView.as_view(), name='tournament-list'),
  url(r'^register/([1-9][0-9]*)/', RegisterView.as_view(), name='register'),
  url(r'^quit/([1-9][0-9]*)/', QuitTeamView.as_view(), name='quit'),
  url(r'^kick/([1-9][0-9]*)/([1-9][0-9]*)/([1-9][0-9]*)/', KickContestantView.as_view(), name='kick'),
  url(r'^transfer/([1-9][0-9]*)/([1-9][0-9]*)/([1-9][0-9]*)/', TransferLeaderView.as_view(), name='transfer'),
  url(r'^edit-team-name/([1-9][0-9]*)/', EditTeamNameView.as_view(), name='edit-team-name'),

  # Image Manage Urls
  url(r'^{}(?P<path>.*)$'.format(settings.MEDIA_URL[1:]), serve_image, name='serve_image'),

  # Default View 404
  url(r'^', NotFoundView.as_view(), name='default'),

]
