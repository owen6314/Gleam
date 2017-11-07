from django.db import models
from django.contrib.auth.models import User, UserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser

# max length of name(long version)
MAX_NAME_LEN_LONG = 80
# max length of name(short version)
MAX_NAME_LEN_SHORT = 24
# max length of flag
MAX_FLAG_LEN = 2
# max length of resident id number
MAX_RID_LEN = 18

class Organizer(models.Model):
    o_organization = models.CharField(max_length=MAX_NAME_LEN_LONG, verbose_name=u'组织')

    # objects = UserManager()

    class Meta:
        verbose_name = u'Organizer'


class Contestant(models.Model):
    # resident id number
    resident_id = models.CharField(max_length=MAX_RID_LEN)
    # nick name
    nick_name = models.CharField(max_length=MAX_NAME_LEN_SHORT)
    # school name
    school = models.CharField(max_length=MAX_NAME_LEN_LONG)
    # gender
    GENDER_CHOICES = (('M', 'male'), ('F', 'female'), ('O', 'others'))
    gender = models.CharField(choices=GENDER_CHOICES, max_length=MAX_FLAG_LEN, default='O')


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    TYPE_CHOICES = (('O', 'Organizer'), ('C', 'Contestant'))
    type = models.CharField(max_length=MAX_FLAG_LEN, choices=TYPE_CHOICES)

    organizer_profile = models.ForeignKey(Organizer, null=True)
    contestant_profile = models.ForeignKey(Contestant, null=True)

    # # organization name
    # o_organization = models.CharField(max_length=MAX_NAME_LEN_LONG, verbose_name=u'组织')
    #
    # # resident id number
    # c_resident_id = models.CharField(max_length=MAX_RID_LEN)
    # # nick name
    # c_nick_name = models.CharField(max_length=MAX_NAME_LEN_SHORT)
    # # school name
    # c_school = models.CharField(max_length=MAX_NAME_LEN_LONG)
    # # gender
    # GENDER_CHOICES = (('M', 'male'), ('F', 'female'), ('O', 'others'))
    # gender = models.CharField(choices=GENDER_CHOICES, max_length=MAX_FLAG_LEN, default='O')


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


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


class Contest(models.Model):
    name = models.CharField(max_length=MAX_NAME_LEN_LONG)
    organizer = models.ForeignKey(Organizer)
    signup_begin_time = models.DateTimeField()
    signup_end_time = models.DateTimeField()
    submit_begin_time = models.DateTimeField()
    submit_end_time = models.DateTimeField()
    announcement_time = models.DateTimeField()
    description = models.TextField()
    evaluation = models.TextField()
    prizes = models.TextField()
    data_description = models.TextField()
    status = models.IntegerField()

    STATUS_DELETED = -1
    STATUS_SAVED = 0
    STATUS_PUBLISHED = 1
    STATUS_FINISHED = 2


def generate_filename(instance, filename):
    return "submissions/%s/%s" % (instance.contest.name, filename)


class Submission(models.Model):
    contest = models.ForeignKey('Contest')
    team = models.ForeignKey('Team')
    score = models.DecimalField(max_digits=4, decimal_places=2)
    data = models.FileField(upload_to=generate_filename)
    time = models.DateTimeField()
