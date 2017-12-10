from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import Tournament, Contest, Team, Record
import hashlib


@method_decorator(login_required, name='dispatch')
class TournamentDetailContestantView(View):
  # 显示当前比赛信息
  @staticmethod
  def get(request, *args):

    # 判断当前用户类型
    if request.user.type != 'C' or not request.user.contestant_profile:
      return redirect('403')

    # 判断比赛存在性
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
    except:
      return redirect('404')

    # 构造回传数据
    data = dict()

    data['tournament_id'] = tournament_id
    data['description'] = tournament.description
    data['name'] = tournament.name
    data['organization'] = tournament.organizer.organization
    # teams = tournament.team_set.all()
    # contestants = list()
    # for _team in teams:
    #   members = _team.members.all()
    #   contestants.extend(members)
    # data['contestant_num'] = len(contestants)
    data['register_begin_time'] = tournament.register_begin_time
    data['register_end_time'] = tournament.register_end_time
    try:
      data['current_contest'] = Contest.objects.get(tournament=tournament, submit_begin_time__lte=timezone.now(),
                                                    release_time__gt=timezone.now())
    except:
      data['current_contest'] = None

    data['contests_coming'] = Contest.objects.filter(tournament=tournament,
                                                     submit_begin_time__gt=timezone.now()).order_by('submit_begin_time')
    data['contests_finished'] = Contest.objects.filter(tournament=tournament,
                                                       release_time__lte=timezone.now()).order_by('-submit_begin_time')

    if data['current_contest']:
      data['countdown'] = (data['current_contest'].submit_end_time - timezone.now()).days
      data['update_time'] = data['current_contest'].release_time
      data['leaderboard'] = TournamentDetailContestantView.get_leader_board(data['current_contest'])
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
  def get_leader_board(contest):
    leaderboard = contest.leaderboarditem_set.order_by('-score')
    leader_board = []
    rank = 1
    for record in leaderboard:
      team_info = dict()
      team_info['team_name'] = record.team.name
      team_info['leader'] = record.team.leader
      team_info['members'] = record.team.members.all()
      team_info['submit_num'] = record.submit_num
      team_info['score'] = record.score
      team_info['time'] = record.time
      team_info['tutor'] = record.team.tutor
      team_info['rank'] = rank
      rank += 1
      leader_board.append(team_info)

    return leader_board


class TournamentListView(View):
  # 显示比赛列表
  @staticmethod
  def get(request):
    tournaments_online = Tournament.objects \
      .filter(status=Tournament.STATUS_PUBLISHED) \
      .filter(register_end_time__lte=timezone.now(), overall_end_time__gt=timezone.now()) \
      .distinct()

    tournaments_registering = Tournament.objects \
      .filter(status=Tournament.STATUS_PUBLISHED) \
      .filter(register_begin_time__lte=timezone.now(), register_end_time__gt=timezone.now()) \
      .distinct()

    tournaments_offline = Tournament.objects \
      .filter(status=Tournament.STATUS_PUBLISHED)\
      .filter(overall_end_time__lte=timezone.now()) \
      .distinct()

    tournaments_coming = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED)\
      .filter(register_begin_time__lt=timezone.now())\
      .distinct()

    data = dict()
    data['tournaments_online'] = tournaments_online
    data['tournaments_registering'] = tournaments_registering
    data['tournaments_offline'] = tournaments_offline
    data['tournaments_coming'] = tournaments_coming

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
