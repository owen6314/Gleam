from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils import timezone
from .forms import ContestForm, TournamentForm
from .models import Tournament, Contest, Team, Record, LeaderBoardItem

import datetime
import csv
import uuid
import json


@method_decorator(login_required, name='dispatch')
class CreateTournamentView(View):
  # 渲染比赛创建页面
  @staticmethod
  def get(request):
    try:
      organizer = request.user.organizer_profile
    except:
      return render(request, 'page_403.html')
    return render(request, 'tournament/tournament_creation.html')

  # 创建比赛
  @staticmethod
  def post(request):
    tournament_form = TournamentForm(request.POST)
    tournament = None
    if tournament_form.is_valid():
      tournament = tournament_form.save(commit=False)
      tournament.image = request.FILES['image']
      tournament.organizer = request.user.organizer_profile
      tournament.status = Tournament.STATUS_SAVED
      tournament.save()
    # name = request.POST['name']
    # description = request.POST['description']
    # image = request.FILES['image']
    # register_begin_time = request.POST['register_begin_time']
    # register_end_time = request.POST['register_end_time']
    # tournament.overall_end_time = request.POST['overall_end_time']
    # organizer = request.user.organizer_profile
    # tournament = Tournament(name=name, description=description, image=image, register_begin_time=register_begin_time,
    #                         register_end_time=register_end_time, organizer=organizer, status=Tournament.STATUS_SAVED,
    #                         max_team_member_num=3)
    form_len = (len(request.POST) - 7) // 6
    for i in range(1, form_len + 1):
      data = {
        'name': request.POST['name_' + str(i)],
        'description': request.POST['description_' + str(i)],
        'submit_begin_time': request.POST['submit_begin_time_' + str(i)],
        'submit_end_time': request.POST['submit_end_time_' + str(i)],
        'release_time': request.POST['release_time_' + str(i)],
        'pass_rule': request.POST['pass_rule_' + str(i)]
      }
      form = ContestForm(data)
      if form.is_valid():
        contest = form.save(commit=False)
        contest.tournament = tournament
        contest.team_count = 0
        contest.save()
      else:
        # form validate fail
        pass
    return redirect('home-organizer')


@method_decorator(login_required, name='dispatch')
class EditTournamentView(View):
  @staticmethod
  def get(request, *args):
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
      organizer = request.user.organizer_profile
      assert tournament.organizer == organizer
    except:
      return redirect('permission-denied-403')
    tform = TournamentForm(instance=tournament)
    contests = tournament.contest_set.all()
    zip = []
    for contest in contests:
      i = contest.id
      # data = {
      #  'name': contest.name,
      #  'description': contest.description,
      #  'submit_begin_time': contest.submit_begin_time,
      #  'submit_end_time': contest.submit_end_time,
      #  'release_time': contest.release_time,
      #  'pass_rule': contest.pass_rule
      # }
      form = ContestForm(instance=contest)
      zip.append({'contest': contest, 'form': form})
    return render(request, 'tournament/tournament_edit.html', {'tournament': tournament, 'tform': tform, 'zip': zip})

  @staticmethod
  def post(request, *args):
    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
    except:
      return redirect('permission-denied-403')
    if 'image' in request.FILES.keys() and request.FILES['image']:
      tournament.image = request.FILES['image']
      tournament.save()
    tform = TournamentForm(request.POST, instance=tournament)
    formfail = False
    if tform.is_valid():
      tform.save()
    else:
      formfail = True

    # tournament.name = request.POST['name']
    # tournament.description = request.POST['description']
    # tournament.register_begin_time = request.POST['register_begin_time']
    # tournament.register_end_time = request.POST['register_end_time']
    # tournament.overall_end_time = request.POST['overall_end_time']
    # tournament.save()
    contests = tournament.contest_set.all()
    zip = []
    for contest in contests:
      i = contest.id
      data = {
        'name': request.POST['name_' + str(i)],
        'description': request.POST['description_' + str(i)],
        'submit_begin_time': request.POST['submit_begin_time_' + str(i)],
        'submit_end_time': request.POST['submit_end_time_' + str(i)],
        'release_time': request.POST['release_time_' + str(i)],
        'pass_rule': request.POST['pass_rule_' + str(i)]
      }
      form = ContestForm(data, instance=contest)
      zip.append({'contest': contest, 'form': form})

    for z in zip:
      form = z['form']
      if form.is_valid():
        form.save()
      else:
        formfail = True
    if formfail:
      return render(request, 'tournament/tournament_edit.html', {'tournament': tournament, 'tform': tform, 'zip': zip})
    else:
      return redirect('tournament-detail-organizer', tournament_id)


@method_decorator(login_required, name='dispatch')
class TournamentDetailOrganizerView(View):
  # 显示当前比赛信息
  @staticmethod
  def get(request, *args):

    tournament_id = int(args[0])
    try:
      tournament = Tournament.objects.get(pk=tournament_id)
    except:
      # 错误tournament id
      return redirect('permission-denied-403')

    # 如果用户类型不符, 拒绝请求
    if request.user.type != 'O':
      return redirect('permission-denied-403')

    # 如果比赛不是该主办方主办的
    if tournament.organizer != request.user.organizer_profile:
      return redirect('permission-denied-403')

    data = dict()

    data['tournament_id'] = tournament_id

    data['name'] = tournament.name

    data['organization'] = request.user.organizer_profile.organization

    data['register_begin_time'] = tournament.register_begin_time

    data['register_end_time'] = tournament.register_end_time

    teams = tournament.team_set.all()
    contestants = list()
    for team in teams:
      members = team.members.all()
      contestants.extend(members)
    data['contestant_num'] = len(contestants)

    try:
      data['current_contest'] = Contest.objects.filter(tournament=tournament) \
        .filter(submit_begin_time__lte=timezone.now()).order_by('-submit_begin_time')[0]
    except:
      data['current_contest'] = None

    data['contests_coming'] = Contest.objects.filter(tournament=tournament) \
      .filter(submit_begin_time__gt=timezone.now()).order_by('submit_begin_time')

    data['contests_finished'] = Contest.objects.filter(tournament=tournament) \
      .filter(submit_end_time__lt=timezone.now()).order_by('-submit_end_time')

    if data['current_contest']:

      data['countdown'] = (data['current_contest'].submit_end_time - timezone.now()).days
      data['update_time'] = data['current_contest'].release_time
      data['leaderboard'] = TournamentDetailOrganizerView.get_leaderboard(data['current_contest'])
    else:
      data['countdown'] = 'N/A'
      data['update_time'] = ''
      data['leaderboard'] = []

    return render(request, 'tournament/tournament_detail_organizer.html', data)

  @staticmethod
  def post(request, *args):
    tournament_id = args[0]
    file = request.FILES['ranking_csv']
    # file_name = os.path.join('tmp', str(uuid.uuid4()) + '.csv')
    file_name = str(uuid.uuid4()) + '.csv'
    with open(file_name, 'wb+') as dest:
      for chunk in file.chunks():
        dest.write(chunk)

    tournament = Tournament.objects.get(id=tournament_id)
    try:
      current_contest = Contest.objects.filter(tournament=tournament) \
        .filter(submit_begin_time__lte=timezone.now()).order_by('-submit_begin_time')[0]
    except:
      current_contest = None

    TournamentDetailOrganizerView.updataRecord(filename=file_name, current_contest=current_contest)
    response_data = {}

    return HttpResponse(json.dumps(response_data), content_type="application/json")

  @staticmethod
  # Emmm, maybe now we can use contest.leaderboarditem_set.filter('-score') to do that
  # cache the result may need some other tools like redis
  def get_leaderboard(contest):
    leaderboard = contest.leaderboarditem_set.order_by('-score')
    ret = []
    rank = 1
    for record in leaderboard:
      team_info = dict()
      team_info['team_name'] = record.team.name
      team_info['members'] = record.team.members.all()
      team_info['submit_num'] = record.submit_num
      team_info['score'] = record.score
      team_info['tutor'] = record.team.tutor
      team_info['rank'] = rank
      rank += 1
      ret.append(team_info)

    return ret

  @staticmethod
  def updataRecord(filename, current_contest, header=False, max_times=999):
    # hashcode, score, time
    with open(filename) as f:
      f_csv = csv.reader(f)
      if header:
        headers = next(f)
      for row in f_csv:
        unique_id = row[0]
        try:
          team = Team.objects.get(unique_id=unique_id)
        except ObjectDoesNotExist:
          # Invalid unique_id
          return -1
        try:
          time = datetime.datetime.strptime(row[2], "%Y/%m/%d %H:%M:%S")
        except ValueError:
          # Invalid time
          return -1
        record = Record(team=team, score=row[1], time=time, contest=current_contest)
        record.save()
        records = Record.objects.filter(team=team, time=time).order_by("-time")
        pre_leaderboard_item = current_contest.leaderboarditem_set.filter(team_id=team.id)
        if records.count() > max_times:
          pre_leaderboard_item[0].delete()
        if not pre_leaderboard_item:
          leaderboard_item = LeaderBoardItem(team=team, team_id=team.id, team_name=team.name, score=record.score,
                                             time=time, contest=current_contest)
          leaderboard_item.save()
        else:
          records = records.order_by("-score")
          pre_leaderboard_item[0].submit_num += 1
          if pre_leaderboard_item[0].score < records[0].score:
            pre_leaderboard_item[0].score = records[0].score
            pre_leaderboard_item[0].time = records[0].time
            pre_leaderboard_item[0].team_name = team.name
            pre_leaderboard_item[0].save()


class ContestLeaderboardOrganizerView(View):
  @staticmethod
  def get(request, contest_id):
    try:
      contest = Contest.objects.get(id=contest_id)
    except ObjectDoesNotExist:
      return redirect('404')

    leader_board_items = LeaderBoardItem.objects \
      .filter(contest=contest).order_by('-score').all()
    leaderboard = list()
    index = 0
    for item in leader_board_items:
      leaderboard.append({
        'id': item.team.id,
        'team_name': item.team_name,
        'score': item.score,
        'time': item.time,
        'rank': index + 1,
        'members': item.team.members.all(),
        'tutor': item.team.tutor,
      })
      index += 1
    data = dict()
    data['leaderboard'] = leaderboard
    data['contest_id'] = contest.id
    contest_next = ContestLeaderboardOrganizerView.get_next_contest(contest)
    if contest_next:
      team_promoted = Team.objects.filter(contests__in=[contest_next])
      team_promoted_ids = [team.id for team in team_promoted]
      data['promoted'] = team_promoted_ids
    else:
      data['promoted'] = []
    return render(request, 'organizer/organizer_contest_leaderboard.html', data)

  @staticmethod
  def post(request, contest_id):
    team_promoted_ids = request.POST.getlist('promoted')
    try:
      contest = Contest.objects.get(id=contest_id)
    except ObjectDoesNotExist:
      return redirect('404')
    contest_next = ContestLeaderboardOrganizerView.get_next_contest(contest)
    if contest_next:
      leader_board_items = LeaderBoardItem.objects \
        .filter(contest=contest).order_by('-score').all()
      for item in leader_board_items:
        if str(item.team_id) in team_promoted_ids:
          if contest_next not in item.team.contests.all():
            item.team.contests.add(contest_next)
            item.team.save()
        else:
          if contest_next in item.team.contests.all():
            item.team.contests.remove(contest_next)
            item.team.save()

    return redirect('contest-leaderboard-organizer', contest_id)

  @staticmethod
  def get_next_contest(contest):
    tournament = contest.tournament
    try:
      contest_next = Contest.objects \
        .filter(tournament=tournament, submit_begin_time__gte=contest.submit_end_time) \
        .order_by('submit_begin_time')[0]
      return contest_next
    except IndexError:
      return None
