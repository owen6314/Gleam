from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

import django.utils.timezone as timezone
from .forms import *
from .models import *
import datetime
import hashlib
import csv
import uuid
import os


class SignupOrganizerView(View):
  # 测试用
  @staticmethod
  def get(request):
    def get(request):
      return render(request, 'contestant_signup.html')

  # 注册赛事方
  # email password
  @staticmethod
  def post(request):
    form = UserSignupForm(request.POST)
    if form.is_valid():
      user = form.save(commit=False)

      # 设置用户类型
      user.type = 'O'

      # 连接用户类型对应的用户信息表单
      profile = Organizer.objects.create()
      user.organizer_profile = profile
      user.save()

      # 注册完成后，直接登录
      login(request, user)

      return redirect('home-organizer')
    return redirect('index')


class SignupContestantView(View):
  # 测试用
  @staticmethod
  def get(request):
    return render(request, 'contestant_signup.html')

  # 注册参赛者
  # email password
  @staticmethod
  def post(request):
    form = UserSignupForm(request.POST)
    if form.is_valid():
      user = form.save(commit=False)

      # 设置用户类型
      user.type = 'C'

      # 连接用户类型对应的用户信息表单
      profile = Contestant.objects.create()
      user.contestant_profile = profile
      user.save()

      # 注册完成后，直接登录
      login(request, user)

      return redirect('home-contestant')

    # 跳转到index
    return redirect('index')


class LoginOrganizerView(View):
  # 测试用
  @staticmethod
  def get(request):
    return render(request, 'login.html')

  # 赛事方登录
  # email password
  @staticmethod
  def post(request):
    form = UserLoginForm(request.POST)
    if form.is_valid():
      email = form.cleaned_data['email']
      password = form.cleaned_data['password']
      # 验证密码 和 用户类型
      user = authenticate(username=email, password=password)
      if user is not None and user.type == 'O':
        login(request, user)
        # 跳转到主页
        return redirect('home-organizer')

    # 跳转到index
    return redirect('index')


class LoginContestantView(View):
  # 参赛方登录
  # email password
  @staticmethod
  def post(request):
    form = UserLoginForm(request.POST)
    if form.is_valid():
      email = form.cleaned_data['email']
      password = form.cleaned_data['password']
      # 验证密码 和 用户类型
      user = authenticate(username=email, password=password)
      if user is not None:  # and user.type == 'C':
        login(request, user)
        # 跳转到主页
        return redirect('home-contestant')

    # 跳转到index
    return redirect('index')


@method_decorator(login_required, name='dispatch')
class LogoutView(View):
  # 登出
  @staticmethod
  def get(request):
    auth.logout(request)
    return redirect('index')


class IndexView(View):
  # 渲染主页
  @staticmethod
  def get(request):
    return render(request, 'gleam.html')


@method_decorator(login_required, name='dispatch')
class HomeOrganizerView(View):
  # 显示赛事方主页
  @staticmethod
  def get(request):
    try:
      organizer = request.user.organizer_profile
    except:
      # 403 permission denied
      return redirect('index')

    # 该主办方创建的所有比赛，按比赛开始注册时间逆序排列
    tournaments = Tournament.objects.filter(organizer=organizer).order_by('-register_begin_time')

    data = dict()

    # 参加该主办方主办的所有比赛的所有队伍数
    data['total_team_num'] = 0
    for tournament in tournaments:
      data['total_team_num'] += len(tournament.team_set.all())

    # 已保存的比赛
    data['tournaments_saved'] = tournaments.filter(status=Tournament.STATUS_SAVED)

    # 已结束的比赛
    data['tournaments_finished'] = tournaments.filter(status=Tournament.STATUS_FINISHED)

    # 已结束的比赛数目
    data['tournament_finished_num'] = len(data['tournaments_finished'])

    # 即将开始的比赛
    data['tournaments_coming'] = tournaments \
      .filter(status=Tournament.STATUS_PUBLISHED).filter(register_begin_time__gte=datetime.datetime.now())

    # 即将开始的比赛数目
    data['tournament_coming_num'] = len(data['tournaments_ongoing'])

    # 正在进行的比赛
    data['tournaments_ongoing'] = tournaments. \
      filter(status=Tournament.STATUS_PUBLISHED).filter(register_begin_time__lte=datetime.datetime.now())

    # 正在进行的比赛数目
    data['tournament_ongoing_num'] = len(data['tournaments_ongoing'])

    return render(request, 'organizer_admin.html', data)


@method_decorator(login_required, name='dispatch')
class HomeContestantView(View):
  # 显示参赛者主页
  @staticmethod
  def get(request):
    try:
      contestant = request.user.contestant_profile
    except:
      # 403 permission denied
      return redirect('index')

    # 当前所有发布的锦标赛，按注册时间倒序排列
    tournaments = Tournament.objects \
      .filter(status__in=[Tournament.STATUS_PUBLISHED, Tournament.STATUS_FINISHED]) \
      .order_by('-register_begin_time')

    # TODO 这是啥？
    # teams = contestant.team_set.all()
    # my_contests = [team.contest for team in teams]

    return render(request, 'user_home.html')


class ProfileOrganizerView(View):
  # 显示赛事方信息
  @staticmethod
  def get(request):
    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'O':
      return redirect('bad-request-400')

    data = dict()
    user = request.user
    profile = user.organizer_profile
    data['email'] = user.email
    data['organization'] = profile.organization

    return render(request, 'organizer_info.html', data)

  # 更新赛事方信息
  @staticmethod
  def post(request):
    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'O':
      return redirect('bad-request-400')

    form = OrganizerDetailForm(request.POST)
    if form.is_valid():
      user = request.user
      profile = user.organizer_profile
      # user.email = form.cleaned_data['email']
      profile.organization = form.cleaned_data['organization']
      profile.save()

    return ProfileOrganizerView.get(request)


@method_decorator(login_required, name='dispatch')
class ProfileContestantView(View):
  # 显示参赛者信息
  @staticmethod
  def get(request):
    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'C':
      return redirect('bad-request-400')

    data = dict()
    user = request.user
    profile = user.contestant_profile
    data['email'] = user.email
    data['nick_name'] = profile.nick_name
    data['school'] = profile.school
    data['gender'] = profile.gender

    return render(request, 'user_admin.html', data)

  # 更新参赛者信息
  @staticmethod
  def post(request):
    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'C':
      return redirect('bad-request-400')
    form = ContestantDetailForm(request.POST)
    if form.is_valid():
      user = request.user
      profile = user.contestant_profile
      # user.email = form.cleaned_data['email']
      profile.nick_name = form.cleaned_data['nick_name']
      profile.school = form.cleaned_data['school']
      profile.gender = form.cleaned_data['gender']
      profile.save()

    return redirect('profile-contestant')


@method_decorator(login_required, name='dispatch')
class CreateTournamentView(View):
  # 渲染比赛创建页面
  @staticmethod
  def get(request):
    try:
      organizer = request.user.organizer_profile
    except:
      return render(request, 'page_403.html')
    return render(request, 'contest_creation.html')

  # 创建比赛
  @staticmethod
  def post(request):
    name = request.POST['name']
    description = request.POST['description']
    image = request.POST['image']
    register_begin_time = request.POST['register_begin_time']
    register_end_time = request.POST['register_end_time']
    organizer = request.user.organizer_profile
    # ToDo: max_team_member_num
    tournament = Tournament(name=name, description=description, image=image, register_begin_time=register_begin_time,
                            register_end_time=register_end_time, organizer=organizer, status=Tournament.STATUS_SAVED,
                            max_team_member_num=3)
    tournament.save()
    for i in range(100):
      if 'name_' + str(i) in request.POST.keys():
        contest = Contest(name=request.POST['name_'+str(i)], description=request.POST['description_']+str(i),
                          submit_begin_time=request.POST['submit_begin_time_'+str(i)],
                          submit_end_time=request.POST['submit_end_time_'+str(i)],
                          release_time=request.POST['release_time_'+str(i)],
                          tournament=tournament, team_count=0)
        contest.save()
      else:
        break
    return redirect('home-organizer')


@method_decorator(login_required, name='dispatch')
class TournamentDetailOrganizerView(View):
  # 显示当前比赛信息
  @staticmethod
  def get(request, *args):

    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
    except:
      # 错误tournament id
      return redirect('bad-request-400')

    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'O':
      return redirect('bad-request-400')

    # 如果比赛不是该主办方主办的
    if tournament.organizer != request.user:
      return redirect('bad-request-400')

    data = dict()

    data['name'] = tournament.name

    data['organization'] = request.user.organizer_profile.organization

    data['register_begin_time'] = tournament.register_begin_time

    data['register_end_time'] = tournament.register_end_time

    teams = tournament.team_set.all()
    contestants = list()
    for team in teams:
      members = team.members.all()
      contestants.extend(members)
    data['contestant_num'] = len(contestants)

    data['current_contest'] = Contest.objects.filter(tournament=tournament) \
      .filter(submit_begin_time__lte=datetime.datetime.now()).order_by('-submit_begin_time')[0]

    data['contests_coming'] = Contest.objects.filter(tournament=tournament) \
      .filter(submit_begin_time__gt=datetime.datetime.now()).order_by('submit_begin_time')

    data['contests_finished'] = Contest.objects \
      .filter(submit_end_time__lt=datetime.datetime.now()).order_by('-submit_end_time')

    data['countdown'] = data['current_contest'].submit_end_time - datetime.datetime.now()

    data['update_time'] = data['current_contest'].release_time

    data['leaderboard'] = TournamentDetailOrganizerView.get_leaderboard(data['current_contest'])

    return render(request, 'tournament_detail_organizer.html', data)

  @staticmethod
  def post(request):
    file = request.FILES['file']
    file_name = os.path.join('tmp', uuid.uuid4() + '.csv')
    with open(file_name, 'wb+') as dest:
      for chunk in file.chunks():
        dest.write(chunk)
    TournamentDetailOrganizerView.updataRecord(filename=file_name)
    return redirect('tournament-detail-organizer')

  @staticmethod
  def get_leaderboard(contest):
    records = Record.objects.filter(contest=contest)
    teams = dict()
    for record in records:
      team_id_str = str(record.team_id)
      if team_id_str not in teams:
        team_info = dict()
        team_info['team_name'] = record.team.name
        team_info['members'] = record.members.all()
        team_info['submit_num'] = 1
        team_info['score'] = record.score
        team_info['tutor'] = record.team.tutor
        teams[team_id_str] = team_info
      else:
        teams[team_id_str]['submit_num'] += 1
        if record.score > teams[team_id_str]['score']:
          teams[team_id_str]['score'] = record.score
    leaderboard = [x[1] for x in teams.items()]
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    if leaderboard:
      last_score = leaderboard[0]['score']
      rank = 1
      for team in leaderboard:
        if team['score'] > last_score:
          rank += 1
          last_score = team['score']
        team['rank'] = rank
    return leaderboard

  @staticmethod
  def updataRecord(filename, header=True, max_times=999):
    # hashcode, score, time
    with open(filename) as f:
      f_csv = csv.reader(f)
      if header:
        headers = next(f)
      for row in f_csv:
        unique_id = row[0]
        try:
          team = Team.objects.get(unique_id=unique_id)
        except ObjectDoesNotExist:
          # Invalid unique_id
          return -1
        try:
          time = datetime.strptime(row[2], "%Y/%m/%d %H:%M:%s").date()
        except ValueError:
          # Invalid time
          return -1
        pre_records = Record.objects.filter(team=team, time=time)
        if pre_records.count() > max_times:
          # too many record
          return -1
        contest = team.contests.order('-sumbit_begin_time')[0]
        record = Record(team=team, score=row[1], time=time, contest=contest)
        record.save()
        # team.score = row[1] if row[1] > team.score else team.score


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
      return redirect('bad-request-400')

    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'O':
      return redirect('bad-request-400')

    # 如果比赛不是该主办方主办的
    if tournament.organizer != request.user:
      return redirect('bad-request-400')

    data = dict()

    data['name'] = tournament.name

    data['organization'] = request.user.organizer_profile.organization

    teams = tournament.team_set.all()
    contestants = list()
    for team in teams:
      members = team.members.all()
      contestants.extend(members)
    data['contestant_num'] = len(contestants)

    data['register_begin_time'] = tournament.register_begin_time

    data['register_end_time'] = tournament.register_end_time

    data['current_contest'] = Contest.objects.filter(tournament=tournament) \
      .filter(submit_begin_time__lte=datetime.datetime.now()).order_by('-submit_begin_time')[0]

    data['contests_coming'] = Contest.objects.filter(tournament=tournament)\
      .filter(submit_begin_time__gt=datetime.datetime.now()).order_by('submit_begin_time')

    data['contests_finished'] = Contest.objects.filter(tournament=tournament) \
      .filter(submit_end_time__lt=datetime.datetime.now()).order_by('-submit_end_time')

    data['countdown'] = data['current_contest'].submit_end_time - datetime.datetime.now()

    data['update_time'] = data['current_contest'].release_time

    data['leaderboard'] = TournamentDetailOrganizerView.get_leaderboard(data['current_contest'])

    data['team'] = None
    try:
      team = Team.objects.get(tournament=tournament, membership__contestant=request.user)
    except:
      team = None

    if team:
      data['team']['name'] = team.name
      all_members = team.members.all()
      data['team']['leader'] = all_members[0]
      if len(all_members) > 1:
        data['team']['members'] = team.members.all()[1:]
      else:
        data['team']['members'] = []
      data['team']['tutor'] = team.tutor
      data['team']['submit_num'] = len(Record.objects.filter(contest=data['current_contest'], team=team))

    return render(request, 'tournament_detail_contestant.html', data)


  @staticmethod
  def get_leaderboard(contest):
    records = Record.objects.filter(contest=contest)
    teams = dict()
    for record in records:
      team_id_str = str(record.team_id)
      if team_id_str not in teams:
        team_info = dict()
        team_info['team_name'] = record.team.name
        team_info['members'] = record.members.all()
        team_info['submit_num'] = 1
        team_info['score'] = record.score
        team_info['tutor'] = record.team.tutor
        teams[team_id_str] = team_info
      else:
        teams[team_id_str]['submit_num'] += 1
        if record.score > teams[team_id_str]['score']:
          teams[team_id_str]['score'] = record.score
    leaderboard = [x[1] for x in teams.items()]
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    if leaderboard:
      last_score = leaderboard[0]['score']
      rank = 1
      for team in leaderboard:
        if team['score'] > last_score:
          rank += 1
          last_score = team['score']
        team['rank'] = rank
    return leaderboard


class TournamentListView(View):
  # 显示比赛列表
  @staticmethod
  def get(request):

    all_contests = Contest.objects.all()

    all_tournaments = Tournament.objects.all()

    tournaments_online = Tournament.objects\
      .filter(register_end_time__gt=datetime.datetime.now(), contest__submit_end_time__lte=datetime.datetime.now())

    tournaments_registering = Tournament.objects.filter(register_end_time__lte=datetime.datetime.now())

    tournaments_offline = Tournament.objects.exclude(contest__submit_end_time__gt=datetime.datetime.now())

    data = dict()
    data['tournaments_online'] = tournaments_online
    data['tournaments_registering'] = tournaments_registering
    data['tournaments_offline'] = tournaments_offline

    return render(request, 'tournament_list.html', data)


class BadRequestView(View):
  # 返回坏请求页面
  @staticmethod
  def get(request):
    return render(request, 'bad_request_400.html')


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
    team = Team.objects.filter(tournament=tournament).filter(members__in=contestant)
    if 'unique_id' in request.POST.keys():
      try:
        target_team = Team.objects.get(unique_id=request.POST['unique_id'])
      except ObjectDoesNotExist:
        target_team = None
      if not target_team:
        # invalid unique_id
        return redirect('contest-detail')
      if target_team.members.count() >= tournament.max_team_member_num:
        # too many members
        return redirect('contest-detail')
    if not team:
      if not target_team:
        team_name = contestant.name + '_' + tournament.name
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md5.update((target_team.name + now).encode('utf-8'))
        while Team.objects.filter(unique_id=md5.hexdigest()):
          now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          md5.update((target_team.name + now).encode('utf-8'))
        contest = tournament.contest_set.order('submit_begin_time').first()
        team = Team(name=team_name, tournament=tournament, unique_id=md5.hexdigest())
        team.contests.add(contest)
        team.save()
        return redirect('contest-detail')
      else:
        target_team.add(contestant)
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md5.update((target_team.name + now).encode('utf-8'))
        while Team.objects.filter(unique_id=md5.hexdigest()):
          now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          md5.update((target_team.name + now).encode('utf-8'))
        target_team.unique_id = md5.hexdigest()
        target_team.save()
        return redirect('contest-detail')
    else:
      if target_team:
        team = team[0]
        if target_team.members.count() + team.members.count() >= tournament.max_team_member_num:
          # too many members
          return redirect('contest-detail')
        for item in team.members:
          target_team.add(item)
        team.delete()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md5.update((target_team.name + now).encode('utf-8'))
        while Team.objects.filter(unique_id=md5.hexdigest()):
          now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          md5.update((target_team.name + now).encode('utf-8'))
        target_team.unique_id = md5.hexdigest()
        target_team.save()
        return redirect('contest-detail')


@method_decorator(login_required, name='dispatch')
class QuitTeamView(View):
  @staticmethod
  def post(request, *args):
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      contestant = request.user.contestant_profile
    except:
      # Invalid infomation
      return redirect('index')
    team = Team.objects.filter(tournament=tournament).filter(members__in=contestant)
    if not team:
      # No team
      return redirect('index')
    team.members.remove(contestant)
    return redirect('index')


def promote(team):
  tournament = team.tournament.contest_set.order('submit_begin_time')
  order = team.contests.count()
  contest = tournament[order]
  team.contests.add(contest)
  team.save()


