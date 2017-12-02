from django.db import models
from django import forms

from .models import *


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
    exclude = ['tournament', 'team_count', 'last_csv_upload_time']

  def clean(self):
    cleaned_data = super(ContestForm, self).clean()
    submit_begin_time = cleaned_data.get('submit_begin_time')
    submit_end_time = cleaned_data.get('submit_end_time')
    release_time = cleaned_data.get('release_time')
    if submit_begin_time and submit_end_time and release_time:
      if submit_begin_time <= submit_end_time and submit_end_time <= release_time:
        pass
      else:
        raise forms.ValidationError("Invalid time order")


class UploadImageForm(forms.ModelForm):
  img = forms.ImageField(required=True, label='Upload image')


class UploadFileForm(forms.ModelForm):
  file = forms.FileField(required=True, label='Upload file')


class ContestantForm(forms.ModelForm):
  class Meta:
    model = Contestant
    fields = ('nick_name', 'school')


class OrganizerForm(forms.ModelForm):
  class Meta:
    model = Organizer
    fields = '__all__'


class UserSignupForm(forms.ModelForm):
  password = forms.CharField(label='Password', max_length=80)

  class Meta:
    model = User
    fields = ('email',)

  def save(self, commit=True):
    # Save the provided password in hashed format
    user = super(UserSignupForm, self).save(commit=False)
    user.set_password(self.cleaned_data["password"])
    if commit:
      user.save()
    return user


class UserLoginForm(forms.Form):
  email = forms.EmailField()
  password = forms.CharField()


class ProfileContestantForm(forms.Form):

  profile_image = forms.ImageField()
  nick_name = forms.CharField()
  school = forms.CharField()
  gender = forms.CharField()


class ProfileOrganizerForm(forms.ModelForm):
  class Meta:
    model = Organizer
    fields = '__all__'