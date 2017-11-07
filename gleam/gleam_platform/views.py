from django.contrib import auth
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View

import django.utils.timezone as timezone
from .forms import *
from .models import *


def home(request):
    contests = Contest.objects.order_by('-submit_end_time')
    return render(request, 'home.html', {'contests': contests[:5]})


def msg(request, msgs):
    return render(request, 'msg.html', {'msgs': msgs})


# Todo: login required
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
        else: # Todo: error message
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
'''
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
            return redirect('organizer_login')
        return render(request, 'organizer_signup.html', {'user_form': user_form, 'organizer_form': organizer_form})


class OrganizerLogin(View):

    @staticmethod
    def get(request):
        return render(request, 'organizer_login.html')

    @staticmethod
    def post(request):
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return render(request, 'organizer_login_successful.html')
        else:
            return render(request, 'organizer_login.html', {'username': username, 'password': password})


class OrganizerLogout(View):

    @staticmethod
    def post(request):
        logout(request)
        redirect('organizer_login')





