from django.test import TestCase, Client
from gleam_platform.models import User, Organizer, Tournament, Contest
from django.utils import timezone
import datetime

# 测试主页
class IndexTest(TestCase):

  # 测试主页url
  def test_index_url(self):
    c = Client()
    response = c.get('/')
    self.assertEqual(response.status_code, 200)
    response = c.get('/index')
    self.assertEqual(response.status_code, 200)


class SignupOrganizerTest(TestCase):

  # 测试组织者注册失败跳转回主页
  def test_signup_organizer_fail_url(self):
    c = Client()
    response = c.post('/signup/organizer')
    self.assertEqual(response.status_code, 200)
    #self.assertEqual(response.url, '/index')

  # 测试组织者注册成功跳转到组织者主页
  def test_signup_organizer_success_url(self):
    c = Client()
    response = c.post('/signup/organizer', {"password": "12345678admin", "email": "thss@163.com"})
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.url, '/home/organizer')

  # 测试注册成功后的组织者信息
  def test_signup_organizer_info(self):
    c = Client()
    response = c.post('/signup/organizer', {"password": "12345678admin", "email": "thss@163.com"})
    u = User.objects.get(email="thss@163.com")
    self.assertEqual(u.email, "thss@163.com")

  def tearDown(self):
    User.objects.filter(email="thss@163.com").delete()


class LoginOrganizerTest(TestCase):

  def setUp(self):
    c = Client()
    response = c.post('/signup/organizer', {"password": "12345678admin", "email": "thss@163.com"})

  # 登录失败，跳转到主页
  def test_login_organizer_fail_url(self):
    c = Client()
    response = c.post('/login/organizer')
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.url, '/index')

  def test_login_organizer_success_url(self):
    c = Client()
    response = c.post('/login/organizer', {"password": "12345678admin", "email": "thss@163.com"})
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response.url, '/home/organizer')

  def tearDown(self):
    User.objects.filter(email="thss@163.com").delete()


class CreateTournamentTest(TestCase):

  def setUp(self):
    c = Client()
    c.post('/signup/organizer', {"password": "12345678admin", "email": "thss@163.com"})

  def test_create_tournament_success(self):
    c = Client()
    c.post('/login/organizer', {"password": "12345678admin", "email": "thss@163.com"})
    c.get('/home/organizer')
    c.get('/create-contest')
    c.post('/create-contest', {
      'csrfmiddlewaretoken': '1234567890abc',
      'name': 'testonly',
      'description': 'testonlydescription',
      'register_begin_time': '2017-12-01 00:00',
      'register_end_time': '2017-12-07 00:00',
      'overall_end_time': '2017-12-31 00:00',
      'max_team_member_num': '3',
      'name_1': 'test_1',
      'description_1': 'test_1_description',
      'submit_begin_time_1': '2017-12-08 00:00',
      'submit_end_time_1': '2017-12-15 00:00',
      'release_time_1': '2017-12-18 00:00',
      'pass_rule_1': '25'
    })
    tournament = Tournament.objects.get(name='testonly')
    self.assertEqual(tournament.description, 'testonlydescription')
    response = c.get('/tournament-detail/organizer/%d/' % tournament.id)
    self.assertEqual(response.status_code, 200)


  def tearDown(self):
    User.objects.filter(email="thss@163.com").delete()
    Tournament.objects.filter(name='testonly').delete()


class EditTournamentTest(TestCase):

  def setUp(self):
    c = Client()
    c.post('/signup/organizer', {"password": "12345678admin", "email": "thss@163.com"})
    now = timezone.now()
    organizer = User.objects.get(email="thss@163.com").organizer_profile
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
    return super().setUp()

  def test_edit_tournament_success(self):
    c = Client()
    c.post('/login/organizer', {"password": "12345678admin", "email": "thss@163.com"})
    tournament = Tournament.objects.get(name='T1')
    contest_id = tournament.contest_set.first().id
    res = c.get('/edit-tournament/%d/' % tournament.id)
    res = c.post('/edit-tournament/%d/' % tournament.id, {
      'csrfmiddlewaretoken': '1234567890abc',
      'name': 'T1',
      'description': 'changed',
      'register_begin_time': '2017-12-01 00:00',
      'register_end_time': '2017-12-07 00:00',
      'overall_end_time': '2017-12-31 00:00',
      'max_team_member_num': '3',
      'name_%d' % contest_id: 'test_1',
      'description_%d' % contest_id: 'test_1_description',
      'submit_begin_time_%d' % contest_id: '2017-12-08 00:00',
      'submit_end_time_%d' % contest_id: '2017-12-15 00:00',
      'release_time_%d' % contest_id: '2017-12-18 00:00',
      'pass_rule_%d' % contest_id: '25'
    })
    tournament.refresh_from_db()
    self.assertEqual(tournament.description, 'changed')

  def test_edit_tournament_invalid_time_fail(self):
    c = Client()
    c.post('/login/organizer', {"password": "12345678admin", "email": "thss@163.com"})
    tournament = Tournament.objects.get(name='T1')
    contest_id = tournament.contest_set.first().id
    c.post('/edit-tournament/%d/' % tournament.id, {
      'csrfmiddlewaretoken': '1234567890abc',
      'name': 'T1',
      'description': 'changed',
      'register_begin_time': '2017-12-08 00:00',
      'register_end_time': '2017-12-07 00:00',
      'overall_end_time': '2017-12-31 00:00',
      'max_team_member_num': '3',
      'name_%d' % contest_id: 'test_1',
      'description_%d' % contest_id: 'test_1_description',
      'submit_begin_time_%d' % contest_id: '2017-12-08 00:00',
      'submit_end_time_%d' % contest_id: '2017-12-15 00:00',
      'release_time_%d' % contest_id: '2017-12-18 00:00',
      'pass_rule_%d' % contest_id: '25'
    })
    tournament.refresh_from_db()
    self.assertEqual(tournament.description, 'unchanged')


class GetLeaderBoardTest(TestCase):

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
    return super().setUp()

  def test_get_leader_board_success(self):
    c = Client()
    c.post('/login/organizer', {"password": "12345678admin", "email": "thss@163.com"})
    contest_id = Contest.objects.first().id
    response = c.get('/contest-leaderboard/organizer/%d/' % contest_id)
    self.assertEqual(response.status_code, 200)
