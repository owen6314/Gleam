from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm

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
            #creator = request.user.profile.
            post = form.save()
            post.creator = creator
            post.save()
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
        contestant = Contestant.objects.get(user=request.user)
        team = contestant.Team_set.filter(contest=contest)
        if not team:
            return render(request, 'contest.html', {'contest': contest})
        submissions = Submission.objects.filter(contest=contest, team=team).order_by('-time')
        return render(request, 'contest.html',
                      {'contest': contest, 'submissions': submissions[:10], 'form': UploadFileForm()})

    @staticmethod
    def post(request, contest_id):
        contest = get_object_or_404(Contest, pk=contest_id)
        contestant = Contestant.objects.get(user=request.user)
        team = contestant.Team_set.filter(contest=contest)
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            submission = Submission.objects.create(contest=contest, team=team, score=99.99,
                                                   data=request.FILES['file'], time=timezone.now())
            submission.save()
            return redirect('contest', contest_id)


class OrganizerSignup(View):

    @staticmethod
    def get(request):
        user_form = UserCreationForm()
        profile_form = ProfileForm()
        return render(request, 'organizer_signup.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })

    @staticmethod
    def post(request):
        user_form = UserCreationForm(data=request.POST)

        if user_form.is_valid():
            try:
                user = user_form.save()
                auth.login(request, user)
                profile_form = ProfileForm(data=request.POST, instance=user)
                profile_form.save()
                return redirect('organizer_login')
            except:
                return redirect('organizer_signup')
        else:
            return redirect('organizer_signup')



class OrganizerLogin(View):

    @staticmethod
    def get(request):
        return render(request, 'organizer_login.html')




