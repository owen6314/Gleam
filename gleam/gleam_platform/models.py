from django.db import models
from django.contrib.auth.models import User

# max length of name(long version)
MAX_NAME_LEN_LONG = 80
# max length of name(short version)
MAX_NAME_LEN_SHORT = 24
# max length of flag
MAX_FLAG_LEN = 2
# max length of resident id number
MAX_RID_LEN = 18


class Contest(models.Model):
    # contest name
    name = models.CharField(max_length=MAX_NAME_LEN_LONG)


class Organizer(models.Model):

    # basic user for auth
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # organization name
    organization = models.CharField(max_length=MAX_NAME_LEN_LONG)


class Contestant(models.Model):

    # basic user for auth
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # resident id number
    resident_id = models.CharField(max_length=MAX_RID_LEN)
    # nick name
    nick_name = models.CharField(max_length=MAX_NAME_LEN_SHORT)
    # school name
    school = models.CharField(max_length=MAX_NAME_LEN_LONG)
    # gender
    GENDER_CHOICES = (('M', 'male'), ('F', 'female'), ('O', 'others'))
    gender = models.CharField(choices=GENDER_CHOICES, max_length=MAX_FLAG_LEN, default='O')


class Team(models.Model):
    # team name
    name = models.CharField(max_length=MAX_NAME_LEN_SHORT)
    # team members
    members = models.ManyToManyField(
        Contestant,
        through='Membership',
        through_fields=('team', 'contestant'),
    )


class Membership(models.Model):
    # team
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)
    # contestant
    contestant = models.ForeignKey(Contestant, on_delete=models.CASCADE, null=True)
