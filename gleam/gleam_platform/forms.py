from django.db import models
from django import forms
from .models import Organizer
from .models import Contest, Submission, Contestant, Organizer, User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _

# max length of name(long version)
MAX_NAME_LEN_LONG = 80
# max length of name(short version)
MAX_NAME_LEN_SHORT = 24

# max length of flag
MAX_FLAG_LEN = 2
# max length of resident id number
MAX_RID_LEN = 18

class ContestForm(forms.ModelForm):
    class Meta:
        model = Contest
        exclude = ['organizer', 'status']


class UploadImageForm(forms.ModelForm):
    img = forms.ImageField(required=True, label='Upload image')


class UploadFileForm(forms.ModelForm):
    file = forms.FileField(required=True, label='Upload file')




#
# class ProfileForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ('type',)


class ContestantForm(forms.ModelForm):
    class Meta:
        model = Contestant
        fields = ('resident_id', 'nick_name', 'school')


class OrganizerForm(forms.ModelForm):
    class Meta:
        model = Organizer
        fields = '__all__'


class UserSignupForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'password')

class UserLoginForm(forms.Form):
    email = models.EmailField('email address')
    password = models.CharField('password', max_length=80)

class ContestantDetailForm(forms.Form):
    email = models.EmailField('email address', unique=True)
    nick_name = models.CharField('nick_name', max_length=MAX_NAME_LEN_SHORT)
    school = models.CharField('school', max_length=MAX_NAME_LEN_LONG)

    GENDER_CHOICES = (('M', 'male'), ('F', 'female'), ('O', 'others'))
    gender = models.CharField(choices=GENDER_CHOICES, max_length=MAX_FLAG_LEN, default='O')

class OrganizerDetailForm(forms.Form):
    email = models.EmailField('email address', unique=True)
    organization = models.CharField(max_length=MAX_NAME_LEN_LONG, verbose_name=u'组织')
