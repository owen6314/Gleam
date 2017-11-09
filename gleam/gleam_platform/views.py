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


class OrganizerSignup(View):
    @staticmethod
    def get(request):
        user_form = UserCreationForm()
        organizer_form = OrganizerForm()
        return render(request, 'organizer_signup.html', {'user_form': user_form, 'organizer_form': organizer_form})

    @staticmethod
    def post(request):
        user_form = UserCreationForm(request.POST)
        organizer_form = OrganizerForm(request.POST)
        if user_form.is_valid() and organizer_form.is_valid():
            user = user_form.save()
            profile = get_object_or_404(Profile, user=user)
            profile.type = 'O'
            organizer_profile = organizer_form.save()
            profile.organizer_profile = organizer_profile
            profile.save()
            return redirect('login')
        return render(request, 'organizer_signup.html', {'user_form': user_form, 'organizer_form': organizer_form})


class ContestantSignup(View):
    @staticmethod
    def get(request):
        user_form = UserCreationForm()
        contestant_form = ContestantForm()
        return render(request, 'contestant_signup.html', {'user_form': user_form, 'contestant_form': contestant_form})

    @staticmethod
    def post(request):
        user_form = UserCreationForm(request.POST)
        contestant_form = ContestantForm(request.POST)
        if user_form.is_valid() and contestant_form.is_valid():
            user = user_form.save()
            profile = get_object_or_404(Profile, user=user)
            profile.type = 'C'
            contestant_profile = contestant_form.save()
            profile.contestant_profile = contestant_profile
            profile.save()
            return redirect('login')
        return render(request, 'contestant_signup.html', {'user_form': user_form, 'contestant_form': contestant_form})


class LoginView(View):
    @staticmethod
    def get(request):
        return render(request, 'login.html')

    @staticmethod
    def post(request):
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'username': username, 'password': password})


@method_decorator(login_required, name='dispatch')
class LogoutView(View):
    @staticmethod
    def get(request):
        auth.logout(request)
        return redirect('home')


@method_decorator(login_required, name='dispatch')
class UserDetailView(View):
    @staticmethod
    def get(request):
        profile = request.user.profile
        type = profile.type
        details = dict()

        # Organizer
        if type == 'O':
            details['organization'] = profile.organizer_profile.organization
            return render(request, 'organizer_detail.html', context=details)

        # Contestant
        elif type == 'C':
            details['resident_id'] = profile.contestant_profile.resident_id
            details['nick_name'] = profile.contestant_profile.nick_name
            details['school'] = profile.contestant_profile.school
            details['gender'] = profile.contestant_profile.gender
            return render(request, 'contestant_detail.html', context=details)


class SignupOrganizerView(View):
    # 注册赛事方
    # email password
    @staticmethod
    def post(request):
        pass


class SignupContestantView(View):
    # 注册参赛者
    # email password
    @staticmethod
    def post(request):
        pass


class LoginOrganizerView(View):
    # 赛事方登录
    # email password
    @staticmethod
    def post(request):
        pass


class LoginContestantView(View):
    # 参赛方登录
    # email password
    @staticmethod
    def post(request):
        pass


class IndexView(View):
    # 渲染主页
    @staticmethod
    def get(request):
        pass


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
        contests = Contest.objects.filter(status__in=[STATUS_PUBLISH, STATUS_FINISH]).order_by('-submit_end_time')
        teams = contestant.Team_set.all()
        my_contests = [team.contest for team in teams]
        pass


class ProfileOrganizerView(View):
    # 显示赛事方信息
    @staticmethod
    def get(request):
        pass

    # 更新赛事方信息
    @staticmethod
    def post(request):
        pass


class ProfileContestantView(View):
    # 显示参赛者信息
    @staticmethod
    def get(request):
        pass

    # 更新参赛者信息
    @staticmethod
    def post(request):
        pass


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
    def get(request):
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
        contests = Contest.objects.filter(status__in=[STATUS_PUBLISH, STATUS_FINISH])
        pass