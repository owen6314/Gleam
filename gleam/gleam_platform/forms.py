from django import forms

from .models import Tournament, Contest, Organizer, Contestant, User

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


class TournamentForm(forms.ModelForm):
  class Meta:
    model = Tournament
    exclude = ['organizer', 'status', 'team_count', 'image']

  def clean_max_team_member_num(self):
    max_team_member_num = self.cleaned_data['max_team_member_num']
    if max_team_member_num < 1:
      raise forms.ValidationError('队伍最大人数应为正数')
    return max_team_member_num


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
      if submit_end_time <= submit_begin_time:
        self.add_error('submit_end_time', '提交截止时间应位于开始时间之后')
      if release_time <= submit_end_time:
        self.add_error('release_time', '成绩公布时间应位于提交截止时间之后')

  def clean_pass_rule(self):
    pass_rule = self.cleaned_data['pass_rule']
    if pass_rule <= 0:
      raise forms.ValidationError('通过规则应为正数')
    return pass_rule


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


class PromotionForm(forms.Form):
  promoted = forms.MultipleChoiceField()
  # choices=(("1", "A"), ("2", "B"), ("3", "C"), ("4", "D")))