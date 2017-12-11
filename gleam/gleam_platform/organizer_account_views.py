from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.utils import timezone

from .forms import UserSignupForm, UserLoginForm, ProfileOrganizerForm, AccountEditForm
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


# @method_decorator(login_required, name='dispatch')
# class LogoutOrganizerView(View):
#   # 登出
#   @staticmethod
#   def get(request):
#     auth.logout(request)
#     return redirect('index')


@method_decorator(login_required, name='dispatch')
class HomeOrganizerView(View):
  # 显示赛事方主页
  @staticmethod
  def get(request):
    if request.user.type != 'O' or not request.user.organizer_profile:
      return redirect('403')
    else:
      organizer = request.user.organizer_profile

    # 该主办方创建的所有比赛，按比赛开始注册时间逆序排列
    tournaments = Tournament.objects.filter(organizer=organizer).order_by('-register_begin_time')

    data = dict()

    # # 参加该主办方主办的所有比赛的所有队伍数
    # data['total_team_num'] = 0
    # for tournament in tournaments:
    #   data['total_team_num'] += len(tournament.team_set.all())

    # 已保存的比赛
    data['tournaments_saved'] = tournaments.filter(status=Tournament.STATUS_SAVED)
    # 已结束的比赛
    data['tournaments_finished'] = tournaments.filter(status=Tournament.STATUS_PUBLISHED,
                                                             overall_end_time__lte=timezone.now())
    # 已结束的比赛数目
    data['tournament_finished_num'] = len(data['tournaments_finished'])
    # 即将开始的比赛
    data['tournaments_coming'] = tournaments.filter(status=Tournament.STATUS_PUBLISHED,
                                                           register_begin_time__gte=timezone.now())
    # # 即将开始的比赛数目
    # data['tournament_coming_num'] = len(data['tournaments_coming'])
    # 正在进行的比赛
    data['tournaments_ongoing'] = tournaments.filter(status=Tournament.STATUS_PUBLISHED,
                                                     register_begin_time__lte=timezone.now(),
                                                     overall_end_time__gt=timezone.now())
    # 正在进行的比赛数目
    data['tournament_ongoing_num'] = len(data['tournaments_ongoing'])
    # 由该主办方主办，当前正在进行（register_begin_time <= now overall_end_time）的
    # 所有比赛，的参赛总人次。
    data['ongoing_contestant_num'] = 0
    for tournament in data['tournaments_ongoing']:
      for team in tournament.team_set.all():
        # 一个队长 + 队员数
        data['ongoing_contestant_num'] += team.members.count + 1
    # 由该主办方主办的所有比赛，的参赛总人次。
    data['total_contestant_num'] = 0
    for tournament in tournaments:
      for team in tournament.team_set.all():
        # 一个队长 + 队员数
        data['total_contestant_num'] += team.members.count + 1

    data['heat'] = organizer.profile_page_visit_num

    # 贡献度
    data['contribution'] = tool.get_contribution(organizer)

    return render(request, 'organizer/organizer_home.html', data)


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
    # 每次被访问，点击数加一
    organizer.profile_page_visit_num += 1
    organizer.save()

    tournaments_all = tool.get_conditional_tournaments(organizer=organizer, type='ALL')
    tournaments_coming = tool.get_conditional_tournaments(organizer=organizer, type='COMING')
    tournaments_ongoing = tool.get_conditional_tournaments(organizer=organizer, type='ONGOING')
    tournaments_finished = tool.get_conditional_tournaments(organizer=organizer, type='FINISHED')

    data['tournament_ongoing_num'] = tournaments_ongoing.count()
    data['ongoing_contestant_num'] = 0
    for tournament in tournaments_ongoing:
      for team in tournament.team_set.all():
        # 一个队长 + 队员数
        data['ongoing_contestant_num'] += team.members.count + 1

    data['tournament_finished_num'] = tournaments_finished.count()
    data['total_contestant_num'] = 0
    for tournament in tournaments_all:
      for team in tournament.team_set.all():
        # 一个队长 + 队员数
        data['total_contestant_num'] += team.members.count + 1

    # ongoing_team_num = 0
    # for tournament in tournaments_ongoing:
    #   ongoing_team_num += tournament.team_set.count()
    # data['ongoing_team_num'] = ongoing_team_num
    # finished_team_num = 0
    # for tournament in tournaments_finished:
    #   finished_team_num += tournament.team_set.count()
    # data['total_team_num'] = ongoing_team_num + finished_team_num

    # TODO 贡献度算法
    data['contribution'] = tool.get_contribution(organizer)
    data['heat'] = organizer.profile_page_visit_num

    data['tournaments_recent'] = tournaments_ongoing | tournaments_coming
    data['tournaments_faraway'] = tournaments_finished

    return render(request, 'organizer/organizer_profile.html', data)


@method_decorator(login_required, name='dispatch')
class ProfileEditOrganizerView(View):
  @staticmethod
  def get(request):
    fields = ['organization', 'biography', 'description', 'location', 'field', 'website']
    data = tool.load_model_obj_data_to_dict(request.user.organizer_profile, fields)
    form = ProfileOrganizerForm(initial=data)
    return render(request, 'organizer/organizer_profile_edit.html', {'form': form})

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
      return render(request, 'organizer/organizer_profile_edit.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class AccountEditOrganizerView(View):

  @staticmethod
  def get(request):
    if request.user.type != 'O' or not request.user.organizer_profile:
      return redirect('403')
    form = AccountEditForm()
    return render(request, 'organizer/account_edit.html', {'form': form})


  @staticmethod
  def post(request):
    if request.user.type != 'O' or not request.user.organizer_profile:
      return redirect('403')
    form = AccountEditForm(request.POST)
    if form.is_valid():
      old_password = form.cleaned_data['old_password']
      new_password = form.cleaned_data['new_password']
      user = authenticate(username=request.user.email, password=old_password)

      if user:
        user.set_password(new_password)
        user.save()
        return redirect('home-organizer')
      else:
        form.add_error('old_password', u'原密码错误')
        return render(request, 'organizer/account_edit.html', {'form': form})

    else:
      return render(request, 'organizer/account_edit.html', {'form': form})