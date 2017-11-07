from django import forms
from .models import Organizer
from django.contrib.auth.models import User
from .models import Contest, Submission, Profile, Contestant, Organizer
from django.contrib.auth.forms import UserCreationForm


class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        exclude = ['organizer', 'status']


class UploadImageForm(forms.ModelForm):
    img = forms.ImageField(required=True, label='Upload image')


class UploadFileForm(forms.ModelForm):
    file = forms.FileField(required=True, label='Upload file')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('type',)


class ContestantForm(forms.ModelForm):
    class Meta:
        model = Contestant
        fields = ('resident_id', 'nick_name', 'school')


class OrganizerForm(forms.ModelForm):
    class Meta:
        model = Organizer
        fields = '__all__'