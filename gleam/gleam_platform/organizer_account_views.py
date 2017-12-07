from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator

from django.utils import timezone
from .forms import UserSignupForm, UserLoginForm, ProfileOrganizerForm
from .models import Tournament, Organizer, User, Image

import gleam_platform.tools as tool


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


@method_decorator(login_required, name='dispatch')
class LogoutOrganizerView(View):
  # 登出
  @staticmethod
  def get(request):
    auth.logout(request)
    return redirect('index')


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
