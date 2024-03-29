from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from .models import Tournament, Contest, Team, Record, Contestant
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
    if tournament.image:
      data['image'] = tournament.image.image
    else:
      data['image'] = None
    data['description'] = tournament.description
    data['name'] = tournament.name
    data['max_team_member_num'] = tournament.max_team_member_num
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
      data['team']['id'] = team.id
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

    if len(args) == 2:
      data['msg'] = args[1]
    return render(request, 'tournament/tournament_detail_contestant.html', data)

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
    tournaments = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED)
    now = timezone.now()
    tournaments_coming = tournaments.filter(register_begin_time__gte=now)
    tournaments_registering = tournaments.filter(register_begin_time__lte=now, register_end_time__gt=now)
    tournaments_online = tournaments.filter(register_end_time__lte=now, overall_end_time__gt=now)
    tournaments_offline = tournaments.filter(overall_end_time__lte=now)
    data = dict()
    data['tournaments_online'] = tournaments_online
    data['tournaments_registering'] = tournaments_registering
    data['tournaments_offline'] = tournaments_offline
    data['tournaments_coming'] = tournaments_coming

    return render(request, 'tournament/tournament_list.html', data)


@method_decorator(login_required, name='dispatch')
class RegisterView(View):
  @staticmethod
  def post(request, *args):
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      contestant = request.user.contestant_profile
    except:
      return redirect('index')
    target_team = None
    if 'unique_id' in request.POST.keys() and request.POST['unique_id']:
      try:
        target_team = Team.objects.get(unique_id=request.POST['unique_id'])
      except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, '不存在的队伍码，请与队长再次确认')
        return redirect('tournament-detail-contestant', tournament.id)

    type, msg = RegisterView.register(tournament, contestant, target_team)
    messages.add_message(request, type, msg)
    return redirect('tournament-detail-contestant', tournament.id)

  @staticmethod
  def register(tournament, contestant, target_team):
    md5 = hashlib.md5()
    now = timezone.now()
    if now < tournament.register_begin_time or now > tournament.register_end_time:
      return messages.ERROR, '目前已不在报名时间内'
    team = Team.objects.filter(tournament=tournament).filter(members=contestant)
    if team:
      return messages.ERROR, '您已经参加了一只队伍，如要变更请先退队'
    if target_team:
      if tournament.max_team_member_num != 0 and target_team.members.count() >= tournament.max_team_member_num:
        return messages.ERROR, '该队伍人已满，请与队长联系'
      target_team.members.add(contestant)
      now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
      md5.update((target_team.name + now).encode('utf-8'))
      while Team.objects.filter(unique_id=md5.hexdigest()):
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        md5.update((target_team.name + now).encode('utf-8'))
      target_team.unique_id = md5.hexdigest()
      target_team.save()
      return messages.SUCCESS, '加队成功'
    else:
      team_name = contestant.nick_name + '_' + tournament.name
      now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
      md5.update((team_name + now).encode('utf-8'))
      while Team.objects.filter(unique_id=md5.hexdigest()):
        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        md5.update((target_team.name + now).encode('utf-8'))
      if tournament.contest_set.count() != 0:
        contest = tournament.contest_set.order_by('submit_begin_time').first()
      else:
        contest = None
      team = Team(name=team_name, tournament=tournament, unique_id=md5.hexdigest(), leader=contestant)
      team.save()
      if contest:
        team.contests.add(contest)
      team.members.add(contestant)
      team.save()
      tournament.team_count += 1
      tournament.save()
      return messages.SUCCESS, '组队成功'


@method_decorator(login_required, name='dispatch')
class QuitTeamView(View):
  @staticmethod
  def get(request, *args):
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      contestant = request.user.contestant_profile
    except:
      return redirect('index')
    type, msg = QuitTeamView.quit(tournament, contestant)
    messages.add_message(request, type, msg)
    return redirect('tournament-detail-contestant', tournament_id)

  @staticmethod
  def quit(tournament, contestant):
    team = Team.objects.filter(tournament=tournament).filter(members=contestant)
    if not team:
      return messages.ERROR, '您还没有在任何一只队伍里'
    team = team[0]
    if team.members.count() == 1:
      team.delete()
      return messages.SUCCESS, '退队成功'
    if team.leader == contestant:
      return messages.ERROR, '请先移交队长再进行退队'
    team.members.remove(contestant)
    team.save()
    return messages.SUCCESS, '退队成功'


@method_decorator(login_required, name='dispatch')
class KickContestantView(View):
  @staticmethod
  def get(request, *args):
    tournament_id = int(args[0])
    team_id = int(args[1])
    contestant_id = int(args[2])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      team = Team.objects.get(pk=team_id)
      contestant = Contestant.objects.get(pk=contestant_id)
      user = request.user.contestant_profile
    except ObjectDoesNotExist:
      return redirect('index')
    type, msg = KickContestantView.kick(tournament, team, user, contestant)
    messages.add_message(request, type, msg)
    return redirect('tournament-detail-contestant', tournament_id)

  @staticmethod
  def kick(tournament, team, user, contestant):
    if timezone.now() < tournament.register_begin_time or timezone.now() > tournament.register_end_time:
      return messages.ERROR, '注册时间已过，不能踢出成员，有需要请联系主办方'
    if user != team.leader:
      return messages.ERROR, '您不是队长，无权踢出成员'
    if contestant not in team.members.all():
      return messages.ERROR, '您指定的人不在队伍里面'
    if contestant == user:
      return messages.ERROR, '您不能直接踢出自己'
    team.members.remove(contestant)
    team.save()
    return messages.SUCCESS, '踢出成员成功'


@method_decorator(login_required, name='dispatch')
class TransferLeaderView(View):
  @staticmethod
  def get(request, *args):
    tournament_id = int(args[0])
    team_id = int(args[1])
    contestand_id = int(args[2])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      team = Team.objects.get(pk=team_id)
      contestant = Contestant.objects.get(pk=contestand_id)
      user = request.user.contestant_profile
    except ObjectDoesNotExist:
      return redirect('index')
    type, msg = TransferLeaderView.transfer(tournament, team, user, contestant)
    messages.add_message(request, type, msg)
    return redirect('tournament-detail-contestant', tournament_id)

  @staticmethod
  def transfer(tournament, team, user, contestant):
    if user != team.leader:
      return messages.ERROR, '您不是队长，无法移交队长'
    if contestant not in team.members.all():
      return messages.ERROR, '您指定的人不在队伍里面'
    if user == contestant:
      return messages.ERROR, '您已经是队长，无法移交队长'
    team.leader = contestant
    team.save()
    return messages.SUCCESS, '移交队长成功'


@method_decorator(login_required, name='dispatch')
class EditTeamNameView(View):
  @staticmethod
  def get(request, *args):
    team_name = request.GET.get('team_name')
    team_id = int(args[0])
    try:
      team = Team.objects.get(pk=team_id)
      user = request.user.contestant_profile
    except ObjectDoesNotExist:
      return redirect('index')
    if user != team.leader:
      messages.add_message(request, messages.ERROR, '您不是队长，无法修改队名')
      name_dict = {'team_name': team.name}
      return JsonResponse(name_dict)
    if team_name:
      team.name = team_name
      team.save()
    name_dict = {'team_name': team.name}
    return JsonResponse(name_dict)
