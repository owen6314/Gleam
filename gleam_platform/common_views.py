from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator


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


class BadRequestView(View):
  # 返回坏请求页面
  @staticmethod
  def get(request):
    return render(request, 'error/page_500.html')


class PermissionDeniedView(View):
  # 返回拒绝页面
  @staticmethod
  def get(request):
    return render(request, 'error/page_403.html')


class NotFoundView(View):
  # 返回拒绝页面
  @staticmethod
  def get(request):
    return render(request, 'error/page_404.html')
