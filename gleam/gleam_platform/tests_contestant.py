from django.test import TestCase, Client
from gleam_platform.models import User


class SignupContestantTest(TestCase):

    # 参赛者登录失败跳转到主页
    def test_signup_contestant_fail_url(self):
        c = Client()
        response = c.post('/signup/contestant')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/index')

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
