from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.sites.shortcuts import get_current_site
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib import messages

from django.utils import timezone
from .forms import ContestForm, UserSignupForm, UserLoginForm, ProfileOrganizerForm, ProfileContestantForm, \
  PromotionForm, TournamentForm
from .models import Tournament, Contest, Organizer, Contestant, User, Team, Record, Image, LeaderBoardItem
import datetime
import hashlib
import csv
import uuid
import os
import json


@method_decorator(login_required, name='dispatch')
class TournamentDetailContestantView(View):
  # 显示当前比赛信息
  @staticmethod
  def get(request, *args):

    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
    except:
      # 错误tournament id
      return redirect('permission-denied-403')

    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'C':
      return redirect('permission-denied-403')

    data = dict()

    data['tournament_id'] = tournament_id

    data['description'] = tournament.description

    data['name'] = tournament.name

    data['organization'] = tournament.organizer.organization

    teams = tournament.team_set.all()
    contestants = list()
    for _team in teams:
      members = _team.members.all()
      contestants.extend(members)
    data['contestant_num'] = len(contestants)

    data['register_begin_time'] = tournament.register_begin_time

    data['register_end_time'] = tournament.register_end_time

    try:
      data['current_contest'] = Contest.objects.filter(tournament=tournament, submit_begin_time__lte=timezone.now(),
                                                       submit_end_time__gte=timezone.now())[0]
    except:
      data['current_contest'] = None

    data['contests_coming'] = Contest.objects.filter(tournament=tournament,
                                                     submit_begin_time__gt=timezone.now()).order_by('submit_begin_time')
    data['contests_finished'] = Contest.objects.filter(tournament=tournament,
                                                       submit_end_time__lt=timezone.now()).order_by('-submit_end_time')

    if data['current_contest']:
      data['countdown'] = (data['current_contest'].submit_end_time - timezone.now()).days
      data['update_time'] = data['current_contest'].release_time
      data['leaderboard'] = TournamentDetailContestantView.get_leaderboard(data['current_contest'])
    else:
      data['countdown'] = 'N/A'
      data['update_time'] = ''
      data['leaderboard'] = []

    data['team'] = None
    try:
      team = Team.objects.get(tournament=tournament, members=request.user.contestant_profile)
    except:
      team = None

    if team:
      data['team_status'] = 1
      data['team'] = dict()
      data['team']['team_name'] = team.name
      all_members = team.members.all()
      data['team']['leader'] = team.leader
      data['team']['members'] = team.members.all()
      data['team']['tutor'] = team.tutor
      data['team']['submit_num'] = len(Record.objects.filter(contest=data['current_contest'], team=team))
      if request.user.contestant_profile == team.leader:
        data['team']['unique_id'] = team.unique_id
      else:
        data['team']['unique_id'] = '0'
    else:
      data['team_status'] = 0

    return render(request, 'tournament_detail_contestant.html', data)

  @staticmethod
  # Emmm, maybe now we can use contest.leaderboarditem_set.filter('-score') to do that
  # cache the result may need some other tools like redis
  def get_leaderboard(contest):
    leaderboard = contest.leaderboarditem_set.order_by('-score')
    ret = []
    rank = 1
    for record in leaderboard:
      team_info = dict()
      team_info['team_name'] = record.team.name
      team_info['members'] = record.team.members.all()
      team_info['submit_num'] = record.submit_num
      team_info['score'] = record.score
      team_info['time'] = record.time
      team_info['tutor'] = record.team.tutor
      team_info['rank'] = rank
      rank += 1
      ret.append(team_info)

    return ret


class TournamentListView(View):
  # 显示比赛列表
  @staticmethod
  def get(request):
    all_contests = Contest.objects.all()

    all_tournaments = Tournament.objects.all()

    tournaments_online = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED) \
      .filter(register_end_time__lt=timezone.now(), contest__submit_end_time__gte=timezone.now()).distinct()

    tournaments_registering = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED,
                                                        register_end_time__gte=timezone.now()).distinct()

    tournaments_offline = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED,
                                                    contest__submit_end_time__gte=timezone.now()).distinct()

    data = dict()
    data['tournaments_online'] = tournaments_online
    data['tournaments_registering'] = tournaments_registering
    data['tournaments_offline'] = tournaments_offline

    return render(request, 'tournament_list.html', data)


@method_decorator(login_required, name='dispatch')
class RegisterView(View):
  @staticmethod
  def post(request, *args):
    tournament_id = int(args[0])
    md5 = hashlib.md5()
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      contestant = request.user.contestant_profile
    except:
      # Invalid infomation
      return redirect('index')
    team = Team.objects.filter(tournament=tournament).filter(members=contestant)
    target_team = None
    if 'unique_id' in request.POST.keys() and request.POST['unique_id']:
      try:
        target_team = Team.objects.get(unique_id=request.POST['unique_id'])
      except ObjectDoesNotExist:
        target_team = None
      if not target_team:
        # invalid unique_id
        return redirect('tournament-detail-contestant', tournament_id)
      if target_team.members.count() >= tournament.max_team_member_num:
        # too many members
        return redirect('tournament-detail-contestant', tournament_id)
    if not team:
      if not target_team:
        team_name = contestant.nick_name + '_' + tournament.name
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        md5.update((team_name + now).encode('utf-8'))
        while Team.objects.filter(unique_id=md5.hexdigest()):
          now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
          md5.update((target_team.name + now).encode('utf-8'))
        contest = tournament.contest_set.order_by('submit_begin_time').first()
        team = Team(name=team_name, tournament=tournament, unique_id=md5.hexdigest(), leader=contestant)
        team.save()
        team.contests.add(contest)
        team.members.add(contestant)
        team.save()
        return redirect('tournament-detail-contestant', tournament_id)
      else:
        target_team.members.add(contestant)
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        md5.update((target_team.name + now).encode('utf-8'))
        while Team.objects.filter(unique_id=md5.hexdigest()):
          now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
          md5.update((target_team.name + now).encode('utf-8'))
        target_team.unique_id = md5.hexdigest()
        target_team.save()
        return redirect('tournament-detail-contestant', tournament_id)
    else:
      if target_team:
        team = team[0]
        if target_team.members.count() + team.members.count() >= tournament.max_team_member_num:
          # too many members
          return redirect('contest-detail')
        for member in team.members:
          target_team.members.add(member)
        team.delete()
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        md5.update((target_team.name + now).encode('utf-8'))
        while Team.objects.filter(unique_id=md5.hexdigest()):
          now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
          md5.update((target_team.name + now).encode('utf-8'))
        target_team.unique_id = md5.hexdigest()
        target_team.save()
        return redirect('tournament-detail-contestant', tournament_id)


@method_decorator(login_required, name='dispatch')
class QuitTeamView(View):
  @staticmethod
  def get(request, *args):
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      contestant = request.user.contestant_profile
    except:
      # Invalid infomation
      return redirect('tournament-detail-contestant', tournament_id)
    team = Team.objects.filter(tournament=tournament).filter(members=contestant)
    if not team:
      # No team
      return redirect('tournament-detail-contestant', tournament_id)
    team = team[0]
    if team.members.count() == 1:
      team.delete()
    else:
      # todo : fix it
      team.members.remove(contestant)
      if team.leader == contestant:
        team.leader = team.members.first()
    return redirect('tournament-detail-contestant', tournament_id)
