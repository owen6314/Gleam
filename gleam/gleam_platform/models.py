from django.db import models

# Create your models here.


class Contest(models.Model):
    name = models.CharField(max_length=128)
    creator = models.ForeignKey(Manager)
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


def generate_filename(self, filename):
    return "submissions/%s/%s" % (self.contest.name, filename)


class Submission(models.Model):
    contest = models.ForeignKey('Contest')
    team = models.ForeignKey('Team')
    score = models.DecimalField(..., max_digits=4, decimal_places=2)
    data = models.FileField(upload_to=generate_filename)
    time = models.DateTimeField()



