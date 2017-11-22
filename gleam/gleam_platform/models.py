from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import ugettext_lazy as _

# max length of name(long version)
MAX_NAME_LEN_LONG = 128
# max length of name(short version)
MAX_NAME_LEN_SHORT = 32
# max length of flag
MAX_FLAG_LEN = 2
# max length of resident id number
MAX_RID_LEN = 18


class Organizer(models.Model):
  organization = models.CharField(max_length=MAX_NAME_LEN_LONG, verbose_name=u'组织')

  class Meta:
    verbose_name = u'Organizer'

  def __str__(self):
    return 'id:%d email:%s' % (self.user_set.all()[0].id, self.user_set.all()[0].email)


class Tournament(models.Model):
  name = models.CharField(max_length=MAX_NAME_LEN_LONG)

  organizer = models.ForeignKey(Organizer)

  description = models.TextField()

  status = models.IntegerField()


  image = models.ImageField(null=True, blank=True)
  max_member = models.IntegerField(null=True)

  register_begin_time = models.DateTimeField()
  register_end_time = models.DateTimeField()

  max_team_member_num = models.IntegerField()

  team_count = models.IntegerField()


  STATUS_DELETED = -1
  STATUS_SAVED = 0
  STATUS_PUBLISHED = 1
  STATUS_FINISHED = 2

  def __str__(self):
    return 'name:%s orgid:%s' % (self.name, self.organizer.user_set.all()[0].id)


class Contest(models.Model):
  name = models.CharField(max_length=MAX_NAME_LEN_LONG)

  submit_begin_time = models.DateTimeField()
  submit_end_time = models.DateTimeField()
  release_time = models.DateTimeField()
  description = models.TextField()

  tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, null=True)

  team_count = models.IntegerField(default=0)


class Contestant(models.Model):
  # # resident id number
  # resident_id = models.CharField(max_length=MAX_RID_LEN)
  # nick name
  nick_name = models.CharField(max_length=MAX_NAME_LEN_SHORT)
  # school name
  school = models.CharField(max_length=MAX_NAME_LEN_LONG)
  # gender
  GENDER_CHOICES = (('M', 'male'), ('F', 'female'), ('O', 'others'))
  gender = models.CharField(choices=GENDER_CHOICES, max_length=MAX_FLAG_LEN, default='O')

  def __str__(self):
    return 'id:%d email:%s' % (self.user_set.all()[0].id, self.user_set.all()[0].email)


class UserManager(BaseUserManager):
  """Define a model manager for User model with no username field."""

  use_in_migrations = True

  def _create_user(self, email, password, **extra_fields):
    """Create and save a User with the given email and password."""
    if not email:
      raise ValueError('The given email must be set')
    email = self.normalize_email(email)
    user = self.model(email=email, **extra_fields)
    user.set_password(password)
    user.save()  # using=self._db)
    return user

  def create_user(self, email, password=None, **extra_fields):
    """Create and save a regular User with the given email and password."""
    extra_fields.setdefault('is_staff', False)
    extra_fields.setdefault('is_superuser', False)
    return self._create_user(email, password, **extra_fields)

  def create_superuser(self, email, password, **extra_fields):
    """Create and save a SuperUser with the given email and password."""
    extra_fields.setdefault('is_staff', True)
    extra_fields.setdefault('is_superuser', True)

    if extra_fields.get('is_staff') is not True:
      raise ValueError('Superuser must have is_staff=True.')
    if extra_fields.get('is_superuser') is not True:
      raise ValueError('Superuser must have is_superuser=True.')

    return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
  """User model."""

  username = None
  email = models.EmailField(_('email address'), unique=True, max_length=80)

  TYPE_CHOICES = (('O', 'Organizer'), ('C', 'Contestant'))
  type = models.CharField(max_length=MAX_FLAG_LEN, choices=TYPE_CHOICES)

  organizer_profile = models.ForeignKey(Organizer, null=True, on_delete=models.CASCADE)
  contestant_profile = models.ForeignKey(Contestant, null=True, on_delete=models.CASCADE)

  USERNAME_FIELD = 'email'
  REQUIRED_FIELDS = []

  objects = UserManager()


  def __str__(self):
    return 'id:%d email:%s' % (self.id, self.email)


# class Profile(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#
#     TYPE_CHOICES = (('O', 'Organizer'), ('C', 'Contestant'))
#     type = models.CharField(max_length=MAX_FLAG_LEN, choices=TYPE_CHOICES)
#
#     organizer_profile = models.ForeignKey(Organizer, null=True, on_delete=models.CASCADE)
#     contestant_profile = models.ForeignKey(Contestant, null=True, on_delete=models.CASCADE)
#
#
# @receiver(post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         Profile.objects.create(user=instance)


class Team(models.Model):
  # team name
  name = models.CharField(max_length=MAX_NAME_LEN_SHORT)
  # team members
  members = models.ManyToManyField(
    Contestant,
    through='Membership',
    through_fields=('team', 'contestant'),
  )
  leader = models.ForeignKey('Contestant', on_delete=models.CASCADE, related_name='my_team', null=True)
  # team contest
  tournament = models.ForeignKey(Tournament, null=True)
  unique_id = models.CharField(max_length=128, unique=True)
  tutor = models.CharField(max_length=MAX_NAME_LEN_SHORT, null=True)


class Membership(models.Model):
  # team
  team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True)
  # contestant
  contestant = models.ForeignKey(Contestant, on_delete=models.CASCADE, null=True)


# def generate_dataset_filename(instance, filename):
#   return "datasets/%s/%s" % (instance.contest.name, filename)
#
#
# class Dataset(models.Model):
#   contest = models.ForeignKey('Contest')
#   dataset = models.FileField(upload_to=generate_dataset_filename)
#
#
# def generate_submission_filename(instance, filename):
#   return "submissions/%s/%s" % (instance.contest.name, filename)


class Record(models.Model):
  team = models.ForeignKey('Team')
  score = models.DecimalField(max_digits=4, decimal_places=2)

  time = models.DateTimeField()

  contest = models.ForeignKey('Contest', null=True)
