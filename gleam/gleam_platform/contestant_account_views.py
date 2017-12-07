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

from .forms import UserSignupForm, UserLoginForm, ProfileContestantForm
from .models import Tournament, Contestant, User, Image

import gleam_platform.tools as tool
from gleam import settings


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

    return render(request, 'email_activate.html', {'user_id': user.id, 'domain': 'http://' + current_site.domain})


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
class LogoutContestantView(View):
  # 登出
  @staticmethod
  def get(request):
    auth.logout(request)
    return redirect('index')


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
