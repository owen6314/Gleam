from django.test import TestCase, Client
from gleam_platform.models import User, Tournament, Contest, Organizer, Contestant, Team
from gleam_platform.contestant_tournament_views import RegisterView, QuitTeamView, KickContestantView, \
  TransferLeaderView
from django.utils import timezone
import datetime


class SignupContestantTest(TestCase):
  # 参赛者登录失败跳转到主页
  def test_signup_contestant_fail_url(self):
    c = Client()
    #response = c.post('/signup/contestant')
    #self.assertEqual(response.status_code, 302)
    #self.assertEqual(response.url, '/index')

  # 参赛者注册成功,发送确认邮件
  def test_signup_contestant_success_url(self):
    c = Client()
    response = c.post('/signup/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    self.assertEqual(response.status_code, 302)
    self.assertIn('confirmation-email-send', response.url)

  # 测试注册成功后的参赛者信息(未激活)
  def test_signup_contestant_info(self):
    c = Client()
    response = c.post('/signup/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    u = User.objects.get(email="thss@163.com")
    self.assertEqual(u.email, "thss@163.com")

  def tearDown(self):
    User.objects.filter(email="thss@163.com").delete()


class LoginContestantTest(TestCase):
  # 登录失败，跳转到主页
  def test_login_organizer_fail_url(self):
    c = Client()
    response = c.post('/login/contestant')
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.url, '/index')


class ContestantTournamentTest(TestCase):
  def setUp(self):
    now = timezone.now()
    organizer = Organizer()
    organizer.save()
    tournament = Tournament(name='T1', organizer=organizer, description='T1D', max_team_member_num=4,
                            status=Tournament.STATUS_PUBLISHED,
                            register_begin_time=now - datetime.timedelta(days=1),
                            register_end_time=now + datetime.timedelta(days=1),
                            overall_end_time=now + datetime.timedelta(days=31))
    tournament.save()
    contest1 = Contest(name='T1C1', description='T1C1D', tournament=tournament,
                       submit_begin_time=now + datetime.timedelta(days=1),
                       submit_end_time=now + datetime.timedelta(days=6),
                       release_time=now + datetime.timedelta(days=7))
    contest1.save()
    contest2 = Contest(name='T1C2', description='T1C2D', tournament=tournament,
                       submit_begin_time=now + datetime.timedelta(days=7),
                       submit_end_time=now + datetime.timedelta(days=13),
                       release_time=now + datetime.timedelta(days=14))
    contest2.save()
    contestant1 = Contestant(nick_name='c1')
    contestant1.save()
    contestant2 = Contestant(nick_name='c2')
    contestant2.save()
    contestant3 = Contestant(nick_name='c3')
    contestant3.save()
    return super().setUp()

  def test_register_create_success(self):
    tournament = Tournament.objects.get(name='T1')
    contestant = Contestant.objects.get(nick_name='c1')
    _, msg = RegisterView.register(tournament, contestant, None)
    self.assertEqual(msg, "组队成功")

  def test_register_join_success(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    _, msg = RegisterView.register(tournament, member, team)
    self.assertEqual(msg, "加队成功")

  def test_register_join_full_fail(self):
    tournament = Tournament.objects.get(name='T1')
    tournament.max_team_member_num = 1
    tournament.save()
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    _, msg = RegisterView.register(tournament, member, team)
    self.assertEqual(msg, "该队伍人已满，请与队长联系")

  def test_register_duplicate_fail(self):
    tournament = Tournament.objects.get(name='T1')
    contestant = Contestant.objects.get(nick_name='c1')
    _, msg = RegisterView.register(tournament, contestant, None)
    _, msg2 = RegisterView.register(tournament, contestant, None)
    self.assertEqual(msg, "组队成功")
    self.assertEqual(msg2, "您已经参加了一只队伍，如要变更请先退队")

  def test_register_invalid_time_fail(self):
    tournament = Tournament.objects.get(name='T1')
    contestant = Contestant.objects.get(nick_name='c1')
    tournament.register_begin_time = timezone.now() + datetime.timedelta(hours=1)
    tournament.register_end_time = timezone.now() + datetime.timedelta(hours=3)
    tournament.save()
    _, msg = RegisterView.register(tournament, contestant, None)
    self.assertEqual(msg, '目前已不在报名时间内')
    tournament.register_begin_time = timezone.now() - datetime.timedelta(hours=3)
    tournament.register_end_time = timezone.now() - datetime.timedelta(hours=1)
    tournament.save()
    _, msg = RegisterView.register(tournament, contestant, None)
    self.assertEqual(msg, '目前已不在报名时间内')

  def test_quit_no_team_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    _, msg = QuitTeamView.quit(tournament, leader)
    self.assertEqual(msg, "您还没有在任何一只队伍里")

  def test_quit_leader_success(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    RegisterView.register(tournament, leader, None)
    _, msg = QuitTeamView.quit(tournament, leader)
    self.assertEqual(msg, "退队成功")

  def test_quit_leader_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = QuitTeamView.quit(tournament, leader)
    self.assertEqual(msg, "请先移交队长再进行退队")

  def test_quit_member_success(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = QuitTeamView.quit(tournament, member)
    self.assertEqual(msg, "退队成功")

  def test_kick_member_success(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = KickContestantView.kick(tournament, team, leader, member)
    self.assertEqual(msg, "踢出成员成功")

  def test_kick_other_member_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    other_member = Contestant.objects.get(nick_name='c3')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = KickContestantView.kick(tournament, team, leader, other_member)
    self.assertEqual(msg, "您指定的人不在队伍里面")

  def test_kick_not_leader_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = KickContestantView.kick(tournament, team, member, leader)
    self.assertEqual(msg, "您不是队长，无权踢出成员")

  def test_kick_self_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = KickContestantView.kick(tournament, team, leader, leader)
    self.assertEqual(msg, "您不能直接踢出自己")

  def test_kick_invalid_time_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    tournament.register_begin_time = timezone.now() + datetime.timedelta(hours=1)
    tournament.register_end_time = timezone.now() + datetime.timedelta(hours=3)
    tournament.save()
    _, msg = KickContestantView.kick(tournament, team, leader, member)
    self.assertEqual(msg, "注册时间已过，不能踢出成员，有需要请联系主办方")

  def test_transfer_success(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = TransferLeaderView.transfer(tournament, team, leader, member)
    self.assertEqual(msg, "移交队长成功")

  def test_transfer_other_member_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    other_member = Contestant.objects.get(nick_name='c3')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = TransferLeaderView.transfer(tournament, team, leader, other_member)
    self.assertEqual(msg, "您指定的人不在队伍里面")

  def test_kick_not_leader_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = TransferLeaderView.transfer(tournament, team, member, leader)
    self.assertEqual(msg, "您不是队长，无法移交队长")

  def test_kick_self_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = TransferLeaderView.transfer(tournament, team, leader, leader)
    self.assertEqual(msg, "您已经是队长，无法移交队长")