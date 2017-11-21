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
class CreateContestView(View):
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
    form = ContestForm(request.POST)
    if form.is_valid():
      organizer = request.user.organizer_profile
      contest = form.save(commit=False)
      contest.organizer = organizer
      contest.status = Contest.STATUS_SAVED
      contest.save()
    return redirect('home-organizer')


@method_decorator(login_required, name='dispatch')
class TournamentDetailOrganizerView(View):
  # 显示当前比赛信息
  @staticmethod
  def get(request, *args):

    tournament_id = args[1]
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
    data['organization'] = request.user.organizer_profile.organization

    teams = tournament.team_set.all()
    contestants = list()
    for team in teams:
      members = team.members.all()
      contestants.extend(members)
    data['contestant_num'] = len(contestants)

    data['current_contest'] = Tournament.objects\
      .filter(submit_begin_time__lte = datetime.datetime.now()).order_by('-submit_begin_time')[0]

    data['contests_coming'] = Tournament.objects\
      .filter(submit_begin_time__gt = datetime.datetime.now()).order_by('submit_begin_time')

    data['contests_finished'] = Tournament.objects\
      .filter(submit_end_time__lt = datetime.datetime.now()).order_by('-submit_end_time')

    data['countdown'] = data['current_contest'].submit_end_time - datetime.datetime.now()

    data['update_time'] = data['current_contest'].release_time

    return render(request, 'tournament_detail_organizer.html', data)

  @staticmethod
  def post(self):
    pass


class TournamentListView(View):
  # 显示比赛列表
  @staticmethod
  def get(request):
    tournaments_published = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED)
    tournaments_finished = Tournament.objects.filter(status=Tournament.STATUS_FINISHED)
    # for tournament in tournaments_published:
    #     tournament.team_count = len(tournament.team_count.all())
    # for tournament in tournaments_finished:
    #     tournament.team_count = len(tournament.team_count.all())
    return render(request, 'contest_list.html', {'tournaments_published': tournaments_published,
                                                 'tournaments_finished': tournaments_finished})


class BadRequestView(View):
  # 返回坏请求页面
  @staticmethod
  def get(request):
    return render(request, 'bad_request_400.html')


@method_decorator(login_required, name='dispatch')
class RegisterView(View):
  @staticmethod
  def post(request, *args):
    tournament_id = args[1]
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
        team = Team(name=team_name, tournament=tournament, unique_id=md5.hexdigest())
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
    tournament_id = args[1]
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
      if len(pre_records) > max_times:
        # too many record
        return -1
      record = Record(team=team, score=row[1], time=time)
      record.save()
      team.score = row[1] if row[1] > team.score else team.score
