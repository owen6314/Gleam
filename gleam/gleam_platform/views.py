from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator

import django.utils.timezone as timezone
from .forms import *
from .models import *


class HomeView(View):
    @staticmethod
    def get(request):
        contests = Contest.objects.order_by('-submit_end_time')
        return render(request, 'home.html', {'contests': contests[:5]})


def msg(request, msgs):
    return render(request, 'msg.html', {'msgs': msgs})

'''
@method_decorator(login_required, name='dispatch')
class CreateContest(View):
    @staticmethod
    def get(request):
        return render(request, 'create_contest.html', {'form': ContestForm()})

    @staticmethod
    def post(request):
        form = ContestForm(request.POST)
        if form.is_valid():
            organizer = request.user.profile.organizer_profile
            contest = form.save(commit=False)
            contest.organizer = organizer
            contest.status = Contest.STATUS_SAVED
            contest.save()
            msgs = []
            msgs.append("Success")
            return msg(request, msgs)
        else:  # Todo: error message
            msgs = []
            msgs.append("Fail")
            return msg(request, msgs)


class ContestDetail(View):
    @staticmethod
    def get(request, contest_id):
        contest = get_object_or_404(Contest, pk=contest_id)
        contestant = request.user.profile.contestant_profile
        if not contestant:
            return render(request, 'contest.html', {'contest': contest})
        team = contestant.Team_set.filter(contest=contest)
        if not team:
            return render(request, 'contest.html', {'contest': contest})
        submissions = Submission.objects.filter(contest=contest, team=team).order_by('-time')
        return render(request, 'contest.html',
                      {'contest': contest, 'submissions': submissions[:10], 'form': UploadFileForm()})

    @staticmethod
    def post(request, contest_id):
        contest = get_object_or_404(Contest, pk=contest_id)
        contestant = request.user.profile.contestant_profile
        team = contestant.Team_set.filter(contest=contest)
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            submission = Submission.objects.create(contest=contest, team=team, score=99.99,
                                                   data=request.FILES['file'], time=timezone.now())
            submission.save()
            return redirect('contest', contest_id)
'''


# class OrganizerSignup(View):
#     @staticmethod
#     def get(request):
#         user_form = UserCreationForm()
#         organizer_form = OrganizerForm()
#         return render(request, 'organizer_signup.html', {'user_form': user_form, 'organizer_form': organizer_form})
#
#     @staticmethod
#     def post(request):
#         user_form = UserCreationForm(request.POST)
#         organizer_form = OrganizerForm(request.POST)
#         if user_form.is_valid() and organizer_form.is_valid():
#             user = user_form.save()
#             profile = get_object_or_404(Profile, user=user)
#             profile.type = 'O'
#             organizer_profile = organizer_form.save()
#             profile.organizer_profile = organizer_profile
#             profile.save()
#             return redirect('login')
#         return render(request, 'organizer_signup.html', {'user_form': user_form, 'organizer_form': organizer_form})


# class ContestantSignup(View):
#     @staticmethod
#     def get(request):
#         user_form = UserCreationForm()
#         contestant_form = ContestantForm()
#         return render(request, 'contestant_signup.html', {'user_form': user_form, 'contestant_form': contestant_form})
#
#     @staticmethod
#     def post(request):
#         user_form = UserCreationForm(request.POST)
#         contestant_form = ContestantForm(request.POST)
#         if user_form.is_valid() and contestant_form.is_valid():
#             user = user_form.save()
#             profile = get_object_or_404(Profile, user=user)
#             profile.type = 'C'
#             contestant_profile = contestant_form.save()
#             profile.contestant_profile = contestant_profile
#             profile.save()
#             return redirect('login')
#         return render(request, 'contestant_signup.html', {'user_form': user_form, 'contestant_form': contestant_form})


# class LoginView(View):
#     @staticmethod
#     def get(request):
#         return render(request, 'login.html')
#
#     @staticmethod
#     def post(request):
#         username = request.POST['username']
#         password = request.POST['password']
#
#         user = authenticate(request, username=username, password=password)
#
#         if user is not None:
#             login(request, user)
#             return redirect('home')
#         else:
#             return render(request, 'login.html', {'username': username, 'password': password})


# @method_decorator(login_required, name='dispatch')
# class LogoutView(View):
#     @staticmethod
#     def get(request):
#         auth.logout(request)
#         return redirect('home')


# @method_decorator(login_required, name='dispatch')
# class UserDetailView(View):
#     @staticmethod
#     def get(request):
#         profile = request.user.profile
#         type = profile.type
#         details = dict()
#
#         # Organizer
#         if type == 'O':
#             details['organization'] = profile.organizer_profile.organization
#             return render(request, 'organizer_detail.html', context=details)
#
#         # Contestant
#         elif type == 'C':
#             details['resident_id'] = profile.contestant_profile.resident_id
#             details['nick_name'] = profile.contestant_profile.nick_name
#             details['school'] = profile.contestant_profile.school
#             details['gender'] = profile.contestant_profile.gender
#             return render(request, 'contestant_detail.html', context=details)


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
        form = UserAuthForm(request.POST)
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
        form = UserAuthForm(request.POST)
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
        form = UserAuthForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # 验证密码 和 用户类型
            user = authenticate(request, email=email, password=password)
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
        form = UserAuthForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # 验证密码 和 用户类型
            user = authenticate(request, email=email, password=password)
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


class HomeOrganizerView(View):
    # 显示赛事方主页
    @staticmethod
    def get(request):
        try:
            organizer = request.user.profile.organizer_profile
        except:
            # 403 permission denied
            return redirect('index')
        contests = Contest.objects.filter(organizer=organizer).order_by('-submit_end_time')
        number = len(contests)
        total_team = sum([len(contest.Team_set.all()) for contest in contests])
        pass


class HomeContestantView(View):
    # 显示参赛者主页
    @staticmethod
    def get(request):
        try:
            contestant = request.user.profile.contestant_profile
        except:
            # 403 permission denied
            return redirect('index')
        contests = Contest.objects.filter(status__in=[Contest.STATUS_PUBLISH, Contest.STATUS_FINISH]).order_by('-submit_end_time')
        teams = contestant.Team_set.all()
        my_contests = [team.contest for team in teams]
        pass


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
        form = OrganizerDetailForm(data)

        return render(request, 'organizer_detail.html', {'form': form})

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
        return render(request, 'contestant_detail.html', {'form': form})


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
        form = ContestantDetailForm(data)

        return render(request, 'contestant_detail.html', {'form': form})

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
            profile.nick_name = form.cleaned_data['email']
            profile.school = form.cleaned_data['school']
            profile.save()

        return render(request, 'contestant_detail.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class CreateContestView(View):
    # 渲染比赛创建页面
    @staticmethod
    def get(request):
        try:
            organizer = request.user.profile.organizer_profile
        except:
            # 403 permission denied
            return redirect('index')

        pass

    # 创建比赛
    @staticmethod
    def post(request):
        form = ContestForm(request.POST)
        if form.is_valid():
            organizer = request.user.profile.organizer_profile
            contest = form.save(commit=False)
            contest.organizer = organizer
            contest.status = Contest.STATUS_SAVED
            contest.save()
        pass


class ContestDetailView(View):
    # 显示当前比赛信息
    @staticmethod
    def get(request, *args):
        contest_id = args[1]
        contest = get_object_or_404(Contest, pk=contest_id)
        contestant = request.user.profile.contestant_profile
        if not contestant:
            return render(request, 'contest.html', {'contest': contest})
        team = contestant.Team_set.filter(contest=contest)
        if not team:
            return render(request, 'contest.html', {'contest': contest})
        submissions = Submission.objects.filter(contest=contest, team=team).order_by('-time')
        return render(request, 'contest.html',
                      {'contest': contest, 'submissions': submissions[:10], 'form': UploadFileForm()})
        pass


class ContestListView(View):
    # 显示比赛列表
    @staticmethod
    def get(request):
        contests_published = Contest.objects.filter(status=Contest.STATUS_PUBLISHED)
        contests_finished = Contest.objects.filter(status=Contest.STATUS_FINISHED)
        count_published = [len(contest.Team_set) for contest in contests_published]
        count_finished = [len(contest.Team_set) for contest in contests_finished]
        return render(request, 'contest_list.html', {'contests_published': contests_published,
                                                     'contest_finished': contests_finished,
                                                     'count_published': count_published,
                                                     'count_finished': count_finished})


class BadRequestView(View):
    # 返回坏请求页面
    @staticmethod
    def get(request):
        return render(request, 'bad_request_400.html')

