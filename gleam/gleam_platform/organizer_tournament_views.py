from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.utils import timezone
from .forms import ContestForm, TournamentForm
from .models import Tournament, Contest, Team, Record, LeaderBoardItem, Image

import datetime
import csv
import uuid
import json
import math


@method_decorator(login_required, name='dispatch')
class CreateTournamentView(View):
  # 渲染比赛创建页面
  @staticmethod
  def get(request):
    try:
      organizer = request.user.organizer_profile
    except:
      return render(request, 'error/page_403.html')
    return render(request, 'tournament/tournament_creation.html')

  # 创建比赛
  @staticmethod
  def post(request):
    data = {
      'name': request.POST.get('name'),
      'description': request.POST.get('description'),
      'register_begin_time': request.POST.get('register_begin_time'),
      'register_end_time': request.POST.get('register_end_time'),
      'overall_end_time': request.POST.get('overall_end_time'),
      'max_team_member_num': request.POST.get('max_team_member_num'),
    }
    tournament_form = TournamentForm(data)
    tournament = None
    contest_forms = []
    formfail = False
    if not tournament_form.is_valid():
      formfail = True

    form_len = (len(request.POST) - 7) // 6
    if form_len == 0:
      tournament_form.add_error('overall_end_time', '请最少添加一个阶段')
      formfail = True
    for i in range(1, form_len + 1):
      data = {
        'name': request.POST.get('name_' + str(i)),
        'description': request.POST.get('description_' + str(i)),
        'submit_begin_time': request.POST.get('submit_begin_time_' + str(i)),
        'submit_end_time': request.POST.get('submit_end_time_' + str(i)),
        'release_time': request.POST.get('release_time_' + str(i)),
        'pass_rule': request.POST.get('pass_rule_' + str(i))
      }
      form = ContestForm(data)
      contest_forms.append(form)
      if not form.is_valid():
        formfail = True

    prev_time = tournament_form.cleaned_data.get('register_end_time')
    for form in contest_forms:
      if form.cleaned_data.get('submit_begin_time') and prev_time:
        if form.cleaned_data.get('submit_begin_time') < prev_time:
          form.add_error('submit_begin_time', "提交截止时间应位于上一阶段结束之后")
          formfail = True
      prev_time = form.cleaned_data.get('release_time')

    overall_end_time = tournament_form.cleaned_data.get('overall_end_time')
    if overall_end_time and prev_time and overall_end_time < prev_time:
      tournament_form.add_error('overall_end_time', '比赛结束时间应位于所有阶段结束之后')
      formfail = True

    if not formfail:
      tournament = tournament_form.save(commit=False)
      image = Image(image=request.FILES.get('image'), type='P', owner=request.user)
      image.save()
      tournament.image = image
      tournament.organizer = request.user.organizer_profile
      tournament.status = Tournament.STATUS_PUBLISHED
      tournament.save()
      for form in contest_forms:
        contest = form.save(commit=False)
        contest.tournament = tournament
        contest.team_count = 0
        contest.save()
      return redirect('home-organizer')
    else:
      return render(request, 'tournament/tournament_creation.html', {'tournament_form': tournament_form,
                                                                     'contest_forms': contest_forms
                                                                     })


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
      tournament.image.image = request.FILES['image']
      tournament.image.save()
    tform = TournamentForm(request.POST, instance=tournament)
    formfail = False
    if tform.is_valid():
      tform.save()
    else:
      formfail = True

    contests = tournament.contest_set.all()
    zip = []
    for contest in contests:
      i = contest.id
      data = {
        'name': request.POST.get('name_' + str(i)),
        'description': request.POST.get('description_' + str(i)),
        'submit_begin_time': request.POST.get('submit_begin_time_' + str(i)),
        'submit_end_time': request.POST.get('submit_end_time_' + str(i)),
        'release_time': request.POST.get('release_time_' + str(i)),
        'pass_rule': request.POST.get('pass_rule_' + str(i))
      }
      form = ContestForm(data, instance=contest)
      zip.append({'contest': contest, 'form': form})

    prev_time = tournament.register_end_time
    for z in zip:
      form = z['form']
      if form.is_valid():
        if form.cleaned_data.get('submit_begin_time') and prev_time:
          if form.cleaned_data.get('submit_begin_time') < prev_time:
            form.add_error('submit_begin_time', "阶段开始时间应位于上一阶段公布成绩之后")
            formfail = True
          else:
            form.save()
      else:
        formfail = True
        if form.cleaned_data.get('submit_begin_time') and prev_time:
          if form.cleaned_data.get('submit_begin_time') < prev_time:
            form.add_error('submit_begin_time', "阶段开始时间应位于上一阶段公布成绩之后")
      prev_time = form.cleaned_data.get('release_time')

    if tournament.overall_end_time and prev_time and tournament.overall_end_time < prev_time:
      tform.add_error('overall_end_time', '比赛结束时间应位于所有阶段结束之后')
      formfail = True

    if formfail:
      tournament.status = Tournament.STATUS_SAVED
      #tournament.save()
      return render(request, 'tournament/tournament_edit.html', {'tournament': tournament, 'tform': tform, 'zip': zip})
    else:
      tournament.status = Tournament.STATUS_PUBLISHED
      tournament.save()
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
        # 'id': item.team.id,
        'team_name': item.team_name,
        'score': item.score,
        # 'time': item.time,
        'submit_num': item.submit_num,
        'rank': index + 1,
        'members': item.team.members.all(),
        'leader': item.team.leader,
        'tutor': item.team.tutor,
      })
      index += 1
    data = dict()
    data['leaderboard'] = leaderboard
    data['update_time'] = contest.last_csv_upload_time
    data['contest_id'] = contest_id
    # data['contest_id'] = contest.id
    contest_next = ContestLeaderboardOrganizerView.get_next_contest(contest)
    if contest_next:
      if contest.last_promote_time:
        team_promoted = Team.objects.filter(contests__in=[contest_next])
        team_promoted_ids = [team.id for team in team_promoted]
        data['promoted'] = team_promoted_ids

      else:
        total_num = leader_board_items.count()
        if contest.pass_rule < 1:
          promoted_num = int(math.floor(total_num * contest.pass_rule))
          team_promoted_ids = \
            [item.id for item in leader_board_items[:min([total_num, promoted_num])]]
        else:
          team_promoted_ids = [item.id for item in leader_board_items[:min([total_num, contest.pass_rule])]]
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

      contest.last_promote_time = timezone.now()
      contest.save()

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
