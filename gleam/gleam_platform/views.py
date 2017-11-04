from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from django.forms import inlineformset_factory

from .models import Organizer
from django.contrib.auth.models import User


class OrganizerSignUp(View):

    @staticmethod
    def get(request):
        return render(request, 'organizer_sign_up.html')
