from django.test import TestCase, Client
from gleam_platform.models import User, Tournament, Contest, Organizer, Contestant, Team
from gleam_platform.contestant_tournament_views import RegisterView, QuitTeamView, KickContestantView, \
  TransferLeaderView
from django.utils import timezone
import datetime
from django.http import HttpResponseRedirect


class SignupContestantTest(TestCase):
  # 参赛者登录失败跳转到主页
  def test_signup_contestant_fail_url(self):
    c = Client()
    response = c.post('/signup/contestant')
    self.assertEqual(response.status_code, 200)
    # self.assertEqual(response.url, '/index')

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


class ContestantTournamentUnitTest(TestCase):
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
    Contestant(nick_name='c1').save()
    Contestant(nick_name='c2').save()
    Contestant(nick_name='c3').save()
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

  def test_transfer_not_leader_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = TransferLeaderView.transfer(tournament, team, member, leader)
    self.assertEqual(msg, "您不是队长，无法移交队长")

  def test_transfer_self_fail(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='c1')
    member = Contestant.objects.get(nick_name='c2')
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    _, msg = TransferLeaderView.transfer(tournament, team, leader, leader)
    self.assertEqual(msg, "您已经是队长，无法移交队长")


class TournamentDetailTest(TestCase):

  def setUp(self):
    now = timezone.now()
    organizer = Organizer()
    organizer.save()
    tournament = Tournament(name='T1', organizer=organizer, description='unchanged', max_team_member_num=4,
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
    c = Client()
    c.post('/signup/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    user = User.objects.get(email="thss@163.com")
    user.is_active = True
    user.save()
    return super().setUp()

  def test_tournament_detail_success(self):
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    tournament_id = Tournament.objects.get(name='T1').id
    response = c.get('/tournament-detail/contestant/%d/' % tournament_id)
    self.assertEqual(response.status_code, 200)

  def test_tournament_list_success(self):
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    response = c.get('/tournament-list')
    self.assertEqual(response.status_code, 200)


class ContestantTeamOperationTest(TestCase):
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
    c = Client()
    c.post('/signup/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    user = User.objects.get(email="thss@163.com")
    user.is_active = True
    user.contestant_profile.nick_name = 'leader'
    user.contestant_profile.save()
    user.save()
    c.post('/signup/contestant', {"password": "12345678admin", "email": "thsss@163.com"})
    user = User.objects.get(email="thsss@163.com")
    user.is_active = True
    user.contestant_profile.nick_name = 'member'
    user.contestant_profile.save()
    user.save()
    return super().setUp()

  def test_register_success(self):
    tournament = Tournament.objects.get(name='T1')
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    c.post('/register/%d/' % tournament.id)
    team = Team.objects.filter(tournament=tournament)
    self.assertEqual(team.count(), 1)

  def test_quit_success(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='leader')
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    RegisterView.register(tournament, leader, None)
    self.assertEqual(Team.objects.count(), 1)
    c.get('/quit/%d/' % tournament.id)
    self.assertEqual(Team.objects.count(), 0)

  def test_kick_success(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='leader')
    member = Contestant.objects.get(nick_name='member')
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    self.assertEqual(team.members.count(), 2)
    c.get('/kick/%d/%d/%d/' % (tournament.id, team.id, member.id))
    team.refresh_from_db()
    self.assertEqual(team.members.count(), 1)

  def test_transfer_success(self):
    tournament = Tournament.objects.get(name='T1')
    leader = Contestant.objects.get(nick_name='leader')
    member = Contestant.objects.get(nick_name='member')
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    RegisterView.register(tournament, leader, None)
    team = Team.objects.first()
    RegisterView.register(tournament, member, team)
    self.assertEqual(team.leader.id, leader.id)
    c.get('/transfer/%d/%d/%d/' % (tournament.id, team.id, member.id))
    team.refresh_from_db()
    self.assertEqual(team.leader.id, member.id)


class ContestantProfileEditTest(TestCase):
  def setUp(self):
    c = Client()
    c.post('/signup/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    user = User.objects.get(email="thss@163.com")
    user.is_active = True
    user.contestant_profile.save()
    user.save()
    return super().setUp()

  def test_resident_id_valid(self):
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    c.post('/profile-edit/contestant', {"resident_id": "110103199705041234"})
    user = User.objects.get(email="thss@163.com")
    self.assertEqual(user.contestant_profile.resident_id, "110103199705041234")
    
  def test_resident_id_invalid(self):
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    c.post('/profile-edit/contestant', {"resident_id": "xxx"})
    user = User.objects.get(email="thss@163.com")
    self.assertEqual(user.contestant_profile.resident_id, None)


class ContestantAccountEditTest(TestCase):
  def setUp(self):
    c = Client()
    c.post('/signup/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    user = User.objects.get(email="thss@163.com")
    user.is_active = True
    user.contestant_profile.save()
    user.save()
    return super().setUp()
  
  def test_old_password_valid(self):
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    response = c.post('/contestant/account-edit', {"old_password": "12345678admin", "new_password": "12345678admin"})
    self.assertTrue(isinstance(response, HttpResponseRedirect))
  
  def test_old_password_invalid(self):
    c = Client()
    c.post('/login/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    response = c.post('/contestant/account-edit', {"old_password": "12345678", "new_password": "12345678admin"})
    self.assertFalse(isinstance(response, HttpResponseRedirect))


class ContestantSendEmailTest(TestCase):
  def setUp(self):
    c = Client()
    c.post('/signup/contestant', {"password": "12345678admin", "email": "thss@163.com"})
    self.user = User.objects.get(email="thss@163.com")
    return super().setUp()
  
  def test_send_email_success(self):
    c = Client()
    response = c.get('/confirmation-email-send/' + str(self.user.id) + '/')
    self.assertFalse(isinstance(response, HttpResponseRedirect))
    
  def test_send_email_fail_user_not_exists(self):
    c = Client()
    self.user.is_active = True
    self.user.contestant_profile.save()
    self.user.save()
    response = c.get('/confirmation-email-send/' + str(self.user.id + 100000) + '/')
    self.assertTrue(isinstance(response, HttpResponseRedirect))
  


