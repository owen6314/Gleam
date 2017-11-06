from django import forms
from .models import Organizer
from django.contrib.auth.models import User
from .models import Contest, Submission, Profile
from django.contrib.auth.forms import UserCreationForm


class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        fields = ['name', 'signup_begin_time', 'signup_end_time', 'submit_begin_time', 'submit_end_time',
                  'announcement_time', 'description', 'evaluation', 'prizes', 'data_description']


class UploadImageForm(forms.ModelForm):
    img = forms.ImageField(required=True, label='Upload image')


class UploadFileForm(forms.ModelForm):
    file = forms.FileField(required=True, label='Upload file')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('type',)
