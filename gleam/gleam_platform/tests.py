from django.test import TestCase, Client



# 测试主页
class IndexTest(TestCase):


    # 测试主页url
    def test_index_url(self):
        c = Client()
        response = c.get('/')
        self.assertEqual(response.status_code, 200)
        response = c.get('/index')
        self.assertEqual(response.status_code, 200) 


'''
class SignupOrganizerTest(TestCase):
    

    # 测试组织者注册失败跳转回主页
    def test_signup_organizer_fail_url(self):
        c = Client()
        response = c.post('/signup/organizer')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/index')
    
    # 测试组织者注册成功跳转到组织者主页
    def test_signup_organizer_success_url(self):
        c = Client()
        response = c.post('/signup/organizer',{"password":"12345678admin", "email": "thss@163.com"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/home/organizer')

    def test_signup_organizer_info(self):
        c = Client()
        response = c.post('/signup/organizer',{"password":"12345678admin", "email": "thss@163.com"})
'''       





