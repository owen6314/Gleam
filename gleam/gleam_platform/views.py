from django.contrib import auth
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator

import django.utils.timezone as timezone
from .forms import *
from .models import *
import datetime
import hashlib


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
            user = authenticate(email=email, password=password)
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
            user = authenticate(email=email, password=password)
            if user is not None: # and user.type == 'C':
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
        contests = Contest.objects.filter(organizer=organizer).order_by('-submit_end_time')
        data = dict()
        for contest in contests:
            contest.team_count = len(contest.team_set.all())
        data['contests_saved'] = contests.filter(status=Contest.STATUS_SAVED)
        data['contests_finished'] = contests.filter(status=Contest.STATUS_FINISHED)
        data['count_finished'] = len(data['contests_finished'])
        data['contests_ready'] = contests.filter(status=Contest.STATUS_PUBLISHED).filter(submit_begin_time__gte=datetime.datetime.now())
        data['contests_online'] = contests.filter(status=Contest.STATUS_PUBLISHED).filter(submit_begin_time__lte=datetime.datetime.now())
        data['count_online'] = len(data['contests_online'])
        data['team_count_online'] = sum(contest.team_count for contest in data['contests_online'])
        data['team_count_finished'] = sum(contest.team_count for contest in data['contests_finished'])
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
        contests = Contest.objects.filter(status__in=[Contest.STATUS_PUBLISHED, Contest.STATUS_FINISHED]).order_by('-submit_end_time')
        teams = contestant.team_set.all()
        my_contests = [team.contest for team in teams]
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



class ContestDetailView(View):
    # 显示当前比赛信息
    @staticmethod
    def get(request, *args):
        contest_id = args[1]
        contest = get_object_or_404(Contest, pk=contest_id)
        contestant = request.user.profile.contestant_profile
        if not contestant:
            return render(request, 'contest.html', {'contest': contest})
        team = contestant.team_set.filter(contest=contest)
        if not team:
            return render(request, 'contest.html', {'contest': contest})
        submissions = Submission.objects.filter(contest=contest, team=team).order_by('-time')
        return render(request, 'contest.html',
                      {'contest': contest, 'submissions': submissions[:10], 'form': UploadFileForm()})


class ContestListView(View):
    # 显示比赛列表
    @staticmethod
    def get(request):
        contests_published = Contest.objects.filter(status=Contest.STATUS_PUBLISHED)
        contests_finished = Contest.objects.filter(status=Contest.STATUS_FINISHED)
        for contest in contests_published:
            contest.team_count = len(contest.team_count.all())
        for contest in contests_finished:
            contest.team_count = len(contest.team_count.all())
        return render(request, 'contest_list.html', {'contests_published': contests_published,
                                                     'contests_finished': contests_finished})


class BadRequestView(View):
    # 返回坏请求页面
    @staticmethod
    def get(request):
        return render(request, 'bad_request_400.html')


@method_decorator(login_required, name='dispatch')
class RegisterView(View):

    @staticmethod
    def post(request, *args):
        contest_id = args[1]
        md5 = hashlib.md5()
        try:
            contest = Contest.objects.get(pk=contest_id)
            contestant = request.user.contestant_profile
        except:
            # Invalid infomation
            return redirect('index')
        team = Team.objects.filter(Contest=contest).filter(members=contestant)
        if 'hashcode' in request.POST.keys:
            target_team = Team.objects.filter(hashcode=request.POST['hashcode'])
            if not target_team:
                # invalid hashcode
                return redirect('contest-detail')
            target_team = target_team[0]
            if target_team.members.count() >= contest.max_member:
                # too many members
                return redirect('contest-detail')
        if not team:
            if not target_team:
                team_name = contestant.name + '_' + contest.name
                md5.update((target_team.name + datetime.datetime.now).encode('utf-8'))
                while Team.objects.filter(hashcode=md5.hexdigest):
                    md5.update((target_team.name + datetime.datetime.now).encode('utf-8'))
                team = Team(name=team_name, hashcode=md5.hexdigest())
                team.save()
                return redirect('contest-detail')
            else:
                target_team.add(contestant)
                md5.update((target_team.name + datetime.datetime.now).encode('utf-8'))
                while Team.objects.filter(hashcode=md5.hexdigest):
                    md5.update((target_team.name + datetime.datetime.now).encode('utf-8'))
                target_team.hashcode = md5.hexdigest()
                target_team.save()
                return redirect('contest-detail')
        else:
            if target_team:
                team = team[0]
                if target_team.members.count() + team.members.count() >= contest.max_member:
                    # too many members
                    return redirect('contest-detail')
                for item in team.members:
                    target_team.add(contestant)
                team.delete()
                md5.update((target_team.name + datetime.datetime.now).encode('utf-8'))
                while Team.objects.filter(hashcode=md5.hexdigest):
                    md5.update((target_team.name + datetime.datetime.now).encode('utf-8'))
                target_team.hashcode = md5.hexdigest()
                target_team.save()
                return redirect('contest-detail')


@method_decorator(login_required, name='dispatch')
class QuitTeamView(View):
    @staticmethod
    def post(request, *args):
        contest_id = args[1]
        try:
            contest = Contest.objects.get(pk=contest_id)
            contestant = request.user.contestant_profile
        except:
            # Invalid infomation
            return redirect('index')
        team = Team.objects.filter(Contest=contest).filter(members=contestant)
        if not team:
            # No team
            return redirect('index')
        team.members.remove(contestant)





