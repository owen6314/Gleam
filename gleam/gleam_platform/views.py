from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views import View
from django.forms import inlineformset_factory

import django.utils.timezone as timezone
from .forms import *
from .models import *

# Create your views here.


def home(request):
    contests = Contest.objects.order_by('-submit_end_time')
    return render(request, 'home.html', {'contests': contests[:5]})


@login_required
def create_contest(request):
    if request.method == 'POST':
        form = CreateContestForm(request.POST)
        creator = XXX.objects.get(username=request.user.username)
        post = form.save()
        post.creator = creator
        post.save()
        return home(request)
    return render(request, 'create_contest.html', {'form': CreateContestForm()})


@login_required
def contest(request, contest_id):
    contest = get_object_or_404(Contest, pk=contest_id)
    contestant = Contestant.objects.get(username=request.user.username)
    team = contestant.Team_set.filter(contest=contest)
    if not team:
        return render(request, 'contest.html', {'contest': contest})
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            submission = Submission.objects.create(contest=contest, team=team, score=99.99,
                                                   data=request.FILES['file'], time=timezone.now())
            submission.save()
            return redirect('contest', contest_id)
    submissions = Submission.objects.filter(contest=contest, team=team).order_by('-time')
    return render(request, 'contest.html',
                  {'contest': contest, 'submissions': submissions[:10], 'form': UploadFileForm()})


class OrganizerSignUp(View):

    @staticmethod
    def get(request):
        return render(request, 'organizer_sign_up.html')

