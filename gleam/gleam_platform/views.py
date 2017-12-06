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

import gleam_platform.tools as tool
from gleam import settings


class SignupOrganizerView(View):
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
  # 注册参赛者
  # email password
  @staticmethod
  def post(request):
    form = UserSignupForm(request.POST)
    if form.is_valid():
      user = form.save(commit=False)

      # 未进行邮箱激活
      user.is_active = False

      # 设置用户类型
      user.type = 'C'

      # 连接用户类型对应的用户信息表单
      profile = Contestant.objects.create()
      user.contestant_profile = profile

      user.save()

      current_site = get_current_site(request)
      mail_subject = '激活Gleam账户，迎接美丽新世界'
      message = render_to_string('email_confirmation.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': tool.account_activation_token.make_token(user),
      })
      to_email = form.cleaned_data.get('email')
      email = EmailMessage(
        mail_subject, message, settings.EMAIL_FROM, to=[to_email]
      )
      email.send()

      # return render(request, 'email_activate.html', {'user_id': user.id, 'domain': 'http://'+ current_site})
      return redirect('confirmation-email-send', user.id)

    # 跳转到index
    return redirect('index')

class SendConfirmationEmailView(View):
  @staticmethod
  def get(request, user_id):
    try:
      user = User.objects.get(id=user_id)
    except ObjectDoesNotExist:
      return redirect('404')

    current_site = get_current_site(request)
    mail_subject = '激活Gleam账户，迎接美丽新世界'
    message = render_to_string('email_confirmation.html', {
      'user': user,
      'domain': current_site.domain,
      'uid': urlsafe_base64_encode(force_bytes(user.pk)),
      'token': tool.account_activation_token.make_token(user),
    })
    email = EmailMessage(
      mail_subject, message, settings.EMAIL_FROM, to=[user.email]
    )
    email.send()

    return render(request, 'email_activate.html', {'user_id': user.id, 'domain': 'http://'+ current_site.domain})


class LoginOrganizerView(View):
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
      if user is not None and user.type == 'C':
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
    return render(request, 'index.html')


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

    data['user'] = request.user

    # 参加该主办方主办的所有比赛的所有队伍数
    data['total_team_num'] = 0
    for tournament in tournaments:
      data['total_team_num'] += len(tournament.team_set.all())

    # 已保存的比赛
    data['tournaments_saved'] = Tournament.objects.filter(status=Tournament.STATUS_SAVED)

    # 已结束的比赛
    data['tournaments_finished'] = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED,
                                                             overall_end_time__lte=timezone.now())

    # 已结束的比赛数目
    data['tournament_finished_num'] = len(data['tournaments_finished'])

    # 即将开始的比赛
    data['tournaments_coming'] = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED,
                                                           register_begin_time__gte=timezone.now())

    # 即将开始的比赛数目
    data['tournament_coming_num'] = len(data['tournaments_coming'])

    # 正在进行的比赛
    data['tournaments_ongoing'] = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED,
                                                            register_begin_time__lte=timezone.now())

    # 正在进行的比赛数目
    data['tournament_ongoing_num'] = len(data['tournaments_ongoing'])

    return render(request, 'organizer_home.html', data)


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
    # tournaments = Tournament.objects.filter(status__in=[Tournament.STATUS_PUBLISHED]).order_by('-register_begin_time')

    data = dict()
    data['tournaments'] = Tournament.objects.filter(team__members=request.user.contestant_profile).distinct()

    return render(request, 'contestant_home.html', data)


class ProfileOrganizerView(View):
  # 显示赛事方信息
  @staticmethod
  def get(request, *args):
    user_id = args[0]
    data = dict()

    try:
      user = User.objects.get(id=user_id)
      organizer = user.organizer_profile
    except:
      return redirect('404')
    data['organizer'] = organizer

    tournaments_coming = tool.get_conditional_tournaments(organizer=organizer, type='COMING')
    tournaments_ongoing = tool.get_conditional_tournaments(organizer=organizer, type='ONGOING')
    tournaments_finished = tool.get_conditional_tournaments(organizer=organizer, type='FINISHED')

    data['tournament_ongoing_num'] = tournaments_ongoing.count()
    ongoing_team_num = 0
    for tournament in tournaments_ongoing:
      ongoing_team_num += tournament.team_set.count()
    data['ongoing_team_num'] = ongoing_team_num
    data['tournament_finished_num'] = tournaments_finished.count()
    finished_team_num = 0
    for tournament in tournaments_finished:
      finished_team_num += tournament.team_set.count()
    data['total_team_num'] = ongoing_team_num + finished_team_num

    # TODO 贡献度算法
    data['contribution'] = 0.5

    data['tournaments_recent'] = tournaments_ongoing | tournaments_coming
    data['tournaments_faraway'] = tournaments_finished

    return render(request, 'organizer_profile.html', data)



    # # 更新赛事方信息
    # @staticmethod
    # def post(request):
    #   # 如果用户类型不符, 拒绝请求
    #   if request.user.type != 'O':
    #     return redirect('permission-denied-403')
    #
    #   form = ProfileOrganizerForm(request.POST)
    #   if form.is_valid():
    #     user = request.user
    #     profile = user.organizer_profile
    #     # user.email = form.cleaned_data['email']
    #     profile.organization = form.cleaned_data['organization']
    #     profile.save()
    #
    #   return ProfileOrganizerView.get(request)


@method_decorator(login_required, name='dispatch')
class ProfileContestantView(View):
  # 显示参赛者信息
  @staticmethod
  def get(request, user_id):
    # # 如果用户类型不符, 拒绝请求
    # if request.user.type != 'C':
    #   return redirect('permission-denied-403')
    try:
      user = User.objects.get(id=user_id)
    except:
      return redirect('404')

    if user.type != 'C':
      return redirect('403')

    fields = ['nick_name', 'gender', 'school', 'introduction']
    data = tool.load_model_obj_data_to_dict(user.contestant_profile, fields)
    data['email'] = user.email
    data['user'] = user

    return render(request, 'contestant_profile.html', data)

    # # 更新参赛者信息
    # @staticmethod
    # def post(request):
    #   # 如果用户类型不符, 拒绝请求
    #   if request.user.type != 'C':
    #     return redirect('permission-denied-403')
    #   form = ProfileContestantForm(request.POST, request.FILES)
    #   if form.is_valid():
    #     user = request.user
    #     user.profile_image = form.cleaned_data['profile_image']
    #     profile = user.contestant_profile
    #     profile.nick_name = form.cleaned_data['nick_name']
    #     profile.school = form.cleaned_data['school']
    #     profile.gender = form.cleaned_data['gender']
    #     profile.save()
    #
    #   return redirect('profile-contestant')


@method_decorator(login_required, name='dispatch')
class CreateTournamentView(View):
  # 渲染比赛创建页面
  @staticmethod
  def get(request):
    try:
      organizer = request.user.organizer_profile
    except:
      return render(request, 'page_403.html')
    return render(request, 'tournament_creation.html')

  # 创建比赛
  @staticmethod
  def post(request):
    tournament_form = TournamentForm(request.POST)
    tournament = None
    if tournament_form.is_valid():
      tournament = tournament_form.save(commit=False)
      tournament.image = request.FILES['image']
      tournament.organizer = request.user.organizer_profile
      tournament.status = Tournament.STATUS_SAVED
      tournament.save()
    # name = request.POST['name']
    # description = request.POST['description']
    # image = request.FILES['image']
    # register_begin_time = request.POST['register_begin_time']
    # register_end_time = request.POST['register_end_time']
    # tournament.overall_end_time = request.POST['overall_end_time']
    # organizer = request.user.organizer_profile
    # tournament = Tournament(name=name, description=description, image=image, register_begin_time=register_begin_time,
    #                         register_end_time=register_end_time, organizer=organizer, status=Tournament.STATUS_SAVED,
    #                         max_team_member_num=3)
    form_len = (len(request.POST) - 7) // 6
    for i in range(1, form_len + 1):
      data = {
        'name': request.POST['name_' + str(i)],
        'description': request.POST['description_' + str(i)],
        'submit_begin_time': request.POST['submit_begin_time_' + str(i)],
        'submit_end_time': request.POST['submit_end_time_' + str(i)],
        'release_time': request.POST['release_time_' + str(i)],
        'pass_rule': request.POST['pass_rule_' + str(i)]
      }
      form = ContestForm(data)
      if form.is_valid():
        contest = form.save(commit=False)
        contest.tournament = tournament
        contest.team_count = 0
        contest.save()
      else:
        # form validate fail
        pass
    return redirect('home-organizer')


@method_decorator(login_required, name='dispatch')
class EditTournamentView(View):
  @staticmethod
  def get(request, *args):
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      organizer = request.user.organizer_profile
      assert tournament.organizer == organizer
    except:
      return redirect('permission-denied-403')
    tform = TournamentForm(instance=tournament)
    contests = tournament.contest_set.all()
    zip = []
    for contest in contests:
      i = contest.id
      #data = {
      #  'name': contest.name,
      #  'description': contest.description,
      #  'submit_begin_time': contest.submit_begin_time,
      #  'submit_end_time': contest.submit_end_time,
      #  'release_time': contest.release_time,
      #  'pass_rule': contest.pass_rule
      #}
      form = ContestForm(instance=contest)
      zip.append({'contest': contest, 'form': form})
    return render(request, 'tournament_edit.html', {'tournament': tournament, 'tform': tform, 'zip': zip})

  @staticmethod
  def post(request, *args):
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
    except:
      return redirect('permission-denied-403')
    if 'image' in request.FILES.keys() and request.FILES['image']:
      tournament.image = request.FILES['image']
      tournament.save()
    tform = TournamentForm(request.POST, instance=tournament)
    formfail = False
    if tform.is_valid():
      tform.save()
    else:
      formfail = True

    #tournament.name = request.POST['name']
    #tournament.description = request.POST['description']
    #tournament.register_begin_time = request.POST['register_begin_time']
    #tournament.register_end_time = request.POST['register_end_time']
    #tournament.overall_end_time = request.POST['overall_end_time']
    #tournament.save()
    contests = tournament.contest_set.all()
    zip = []
    for contest in contests:
      i = contest.id
      data = {
        'name': request.POST['name_' + str(i)],
        'description': request.POST['description_' + str(i)],
        'submit_begin_time': request.POST['submit_begin_time_' + str(i)],
        'submit_end_time': request.POST['submit_end_time_' + str(i)],
        'release_time': request.POST['release_time_' + str(i)],
        'pass_rule': request.POST['pass_rule_' + str(i)]
      }
      form = ContestForm(data, instance=contest)
      zip.append({'contest': contest, 'form': form})

    for z in zip:
      form = z['form']
      if form.is_valid():
        form.save()
      else:
        formfail = True
    if formfail:
      return render(request, 'tournament_edit.html', {'tournament': tournament, 'tform': tform, 'zip': zip})
    else:
      return redirect('tournament-detail-organizer', tournament_id)


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
      return redirect('permission-denied-403')

    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'O':
      return redirect('permission-denied-403')

    # 如果比赛不是该主办方主办的
    if tournament.organizer != request.user.organizer_profile:
      return redirect('permission-denied-403')

    data = dict()

    data['tournament_id'] = tournament_id

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

    try:
      data['current_contest'] = Contest.objects.filter(tournament=tournament) \
        .filter(submit_begin_time__lte=timezone.now()).order_by('-submit_begin_time')[0]
    except:
      data['current_contest'] = None

    data['contests_coming'] = Contest.objects.filter(tournament=tournament) \
      .filter(submit_begin_time__gt=timezone.now()).order_by('submit_begin_time')

    data['contests_finished'] = Contest.objects.filter(tournament=tournament) \
      .filter(submit_end_time__lt=timezone.now()).order_by('-submit_end_time')

    if data['current_contest']:

      data['countdown'] = (data['current_contest'].submit_end_time - timezone.now()).days
      data['update_time'] = data['current_contest'].release_time
      data['leaderboard'] = TournamentDetailOrganizerView.get_leaderboard(data['current_contest'])
    else:
      data['countdown'] = 'N/A'
      data['update_time'] = ''
      data['leaderboard'] = []

    return render(request, 'tournament_detail_organizer.html', data)

  @staticmethod
  def post(request, *args):
    tournament_id = args[0]
    file = request.FILES['ranking_csv']
    # file_name = os.path.join('tmp', str(uuid.uuid4()) + '.csv')
    file_name = str(uuid.uuid4()) + '.csv'
    with open(file_name, 'wb+') as dest:
      for chunk in file.chunks():
        dest.write(chunk)

    tournament = Tournament.objects.get(id=tournament_id)
    try:
      current_contest = Contest.objects.filter(tournament=tournament) \
        .filter(submit_begin_time__lte=timezone.now()).order_by('-submit_begin_time')[0]
    except:
      current_contest = None

    TournamentDetailOrganizerView.updataRecord(filename=file_name, current_contest=current_contest)
    response_data = {}

    return HttpResponse(json.dumps(response_data), content_type="application/json")

  @staticmethod
  # Emmm, maybe now we can use contest.leaderboarditem_set.filter('-score') to do that
  # cache the result may need some other tools like redis
  def get_leaderboard(contest):
    records = Record.objects.filter(contest=contest)
    teams = dict()
    for record in records:
      team_id_str = str(record.team_id)
      if team_id_str not in teams:
        team_info = dict()
        team_info['team_name'] = record.team.name
        team_info['members'] = record.team.members.all()
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
  def updataRecord(filename, current_contest, header=False, max_times=999):
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
          time = datetime.datetime.strptime(row[2], "%Y/%m/%d %H:%M:%S")
        except ValueError:
          # Invalid time
          return -1
        record = Record(team=team, score=row[1], time=time, contest=current_contest)
        record.save()
        records = Record.objects.filter(team=team, time=time).order_by("-time")
        pre_leaderboard_item = current_contest.leaderboarditem_set.filter(team_id=team.id)
        if records.count() > max_times:
          pre_leaderboard_item[0].delete()
        if not pre_leaderboard_item:
          leaderboard_item = LeaderBoardItem(team=team, team_id=team.id, team_name=team.name, score=record.score,
                                             time=time, contest=current_contest)
          leaderboard_item.save()
        else:
          records = records.order_by("-score")
          if pre_leaderboard_item[0].score < records[0].score:
            pre_leaderboard_item[0].score = records[0].score
            pre_leaderboard_item[0].time = records[0].time
            pre_leaderboard_item[0].team_name = team.name
            pre_leaderboard_item[0].save()


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
      data['leaderboard'] = TournamentDetailOrganizerView.get_leaderboard(data['current_contest'])
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

    tournaments_online = Tournament.objects.filter(status=Tournament.STATUS_PUBLISHED) \
      .filter(register_end_time__lt=timezone.now(), contest__submit_end_time__gte=timezone.now()).distinct()

    tournaments_registering = Tournament.objects.filter(tatus=Tournament.STATUS_PUBLISHED,
                                                        register_end_time__gte=timezone.now()).distinct()

    tournaments_offline = Tournament.objects.exclude(tatus=Tournament.STATUS_PUBLISHED,
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


def promote(team):
  tournament = team.tournament.contest_set.order_by('submit_begin_time')
  order = team.contests.count()
  contest = tournament[order]
  team.contests.add(contest)
  team.save()


def activate(request, uidb64, token):
  try:
    uid = force_text(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk=uid)
  except(TypeError, ValueError, OverflowError, User.DoesNotExist):
    user = None
  if user is not None and tool.account_activation_token.check_token(user, token):
    user.is_active = True
    user.save()
    login(request, user)
    return redirect('index')
  else:
    return HttpResponse('垃圾验证码!')


@method_decorator(login_required, name='dispatch')
class ProfileEditOrganizerView(View):
  @staticmethod
  def get(request):
    fields = ['organization', 'biography', 'description', 'location', 'field', 'website']
    data = tool.load_model_obj_data_to_dict(request.user.organizer_profile, fields)
    form = ProfileOrganizerForm(initial=data)
    return render(request, 'organizer_profile_edit.html', {'form': form})

  @staticmethod
  def post(request):
    form = ProfileOrganizerForm(request.POST, request.FILES)
    if form.is_valid():
      # 保存除avatar之外的所有field
      fields = ['organization', 'biography', 'description', 'location', 'field', 'website']
      tool.save_form_data_to_model_obj(request.user.organizer_profile, form, fields)

      # 保存avatar
      avatar = Image()
      avatar.image = form.cleaned_data['avatar']
      avatar.type = 'P'
      avatar.owner = request.user
      avatar.save()
      request.user.organizer_profile.avatar = avatar
      request.user.organizer_profile.save()

      return redirect('profile-organizer', request.user.id)
    else:
      return render(request, 'contestant_profile_edit.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class ProfileEditContestantView(View):
  @staticmethod
  def get(request):
    fields = ['nick_name', 'school', 'gender', 'introduction', 'resident_id']
    data = tool.load_model_obj_data_to_dict(request.user.contestant_profile, fields)
    form = ProfileContestantForm(initial=data)
    return render(request, 'contestant_profile_edit.html', {'form': form})

  @staticmethod
  def post(request):
    form = ProfileContestantForm(request.POST, request.FILES)
    if form.is_valid():
      # 保存除avatar之外的所有field
      fields = ['nick_name', 'school', 'gender', 'introduction', 'resident_id']
      tool.save_form_data_to_model_obj(request.user.contestant_profile, form, fields)

      # 保存avatar
      avatar = Image()
      avatar.image = form.cleaned_data['avatar']
      avatar.type = 'P'
      avatar.owner = request.user
      avatar.save()
      request.user.contestant_profile.avatar = avatar
      request.user.contestant_profile.save()

      return redirect('profile-contestant', request.user.id)
    else:
      return render(request, 'contestant_profile_edit.html', {'form': form})


class BadRequestView(View):
  # 返回坏请求页面
  @staticmethod
  def get(request):
    return render(request, 'page_400.html')


class PermissionDeniedView(View):
  # 返回拒绝页面
  @staticmethod
  def get(request):
    return render(request, 'page_403.html')


class NotFoundView(View):
  # 返回拒绝页面
  @staticmethod
  def get(request):
    return render(request, 'page_404.html')


class PromotionView(View):
  @staticmethod
  def get(request, contest_id):
    try:
      contest = Contest.objects.get(id=contest_id)
    except ObjectDoesNotExist:
      return redirect('404')

    leader_board_items = LeaderBoardItem.objects \
      .filter(contest=contest).order_by('-score')
    teams = [
      {
        'id': item['team'].id,
        'name': item['team_name'],
        'score': item['score'],
        'time': item['time'],
        'rank': index + 1,
      }
      for index, item in enumerate(leader_board_items)
    ]
    data = dict()
    data['teams'] = teams
    contest_next = PromotionView.get_next_contest(contest)
    if contest_next:
      team_promoted = Team.objects.filter(contests__in=[contest_next])
      team_promoted_ids = [team.id for team in team_promoted]
      data['promoted'] = team_promoted_ids
      return render(request, 'checkboxes_test.html', data)

  @staticmethod
  def post(request, contest_id):
    team_promoted_ids = request.POST.getlist('promoted')
    try:
      contest = Contest.objects.get(id=contest_id)
    except ObjectDoesNotExist:
      return redirect('404')
    contest_next = PromotionView.get_next_contest(contest)
    if contest_next:
      leader_board_items = LeaderBoardItem.objects \
        .filter(contest=contest).order_by('-score')
      for item in leader_board_items:
        if item.team_id in team_promoted_ids:
          if contest_next not in item.team.contests.all():
            item.team.contests.add(contest_next)
            item.team.save()
        else:
          if contest_next in item.team.contests.all():
            item.team.contests.remove(contest_next)
            item.team.save()

    return redirect('promotion')

  @staticmethod
  def get_next_contest(contest):
    tournament = contest.tournament
    try:
      contest_next = Contest.objects \
        .filter(tournament=tournament, submit_begin_time__gte=contest.submit_end_time) \
        .order_by('submit_begin_time')[0]
      return contest_next
    except IndexError:
      return None
