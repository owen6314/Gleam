from django import forms

from .models import *

import gleam_platform.tools as tool
# max length of name(long version)
MAX_NAME_LEN_LONG = 80
# max length of name(short version)
MAX_NAME_LEN_SHORT = 24

# max length of flag
MAX_FLAG_LEN = 2
# max length of resident id number
MAX_RID_LEN = 18


class ResidentIDField(forms.Field):
  def to_python(self, value):
    """Normalize data to a list of strings."""
    # Return an empty list if no input was given.
    if not value:
      return []
    return value.split(',')

  def validate(self, value):
    """Check if value consists only of valid emails."""
    # Use the parent's handling of required fields, etc.
    super(ResidentIDField, self).validate(value)
    if not tool.validate_rid(value):
      raise forms.ValidationError('身份证号错误')


class ContestForm(forms.ModelForm):
  class Meta:
    model = Contest
    exclude = ['tournament', 'team_count', 'last_csv_upload_time']

  def clean(self):
    cleaned_data = super(ContestForm, self).clean()
    submit_begin_time = cleaned_data.get('submit_begin_time')
    submit_end_time = cleaned_data.get('submit_end_time')
    release_time = cleaned_data.get('release_time')
    pass_rule = cleaned_data.get('pass_rule')
    if submit_begin_time and submit_end_time and release_time:
      if submit_begin_time <= submit_end_time <= release_time:
        pass
      else:
        raise forms.ValidationError("Invalid time order")
    if submit_begin_time and submit_end_time and release_time:
      if submit_begin_time <= submit_end_time <= release_time:
        pass
      else:
        raise forms.ValidationError("Invalid time order")
    if pass_rule :
      if pass_rule < 0.001:
        raise forms.ValidationError("Invalid rule")


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



class ProfileOrganizerForm(forms.Form):
  avatar = forms.ImageField(required=False)
  organization = forms.CharField(max_length=MAX_NAME_LEN_LONG, required=False)
  biography = forms.CharField(required=False)
  description = forms.CharField(required=False)
  location = forms.CharField(required=False)
  field = forms.CharField(max_length=256, required=False)
  website = forms.URLField(required=False)


class ProfileContestantForm(forms.Form):
  avatar = forms.ImageField(required=False)
  nick_name = forms.CharField(max_length=MAX_NAME_LEN_SHORT, required=False)
  school = forms.CharField(required=False)
  gender = forms.CharField(required=False)
  introduction = forms.CharField(required=False)
  resident_id = ResidentIDField(required=False)
