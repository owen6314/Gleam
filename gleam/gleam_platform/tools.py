from django.utils import timezone
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six

from .models import Tournament

class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + six.text_type(timestamp) +
            six.text_type(user.is_active)
        )
account_activation_token = TokenGenerator()

def load_model_obj_data_to_dict(obj, fields):
  data = dict()
  for field in fields:
    data[field] = getattr(obj, field)
  return data

def save_form_data_to_model_obj(obj, form, fields=None):
  # 把form里经过清洗的数据保存到obj里

  if not fields:
    fields = form.cleaned_data.keys()
  for field in fields:
    setattr(obj, field, form.cleaned_data[field])
  obj.save()

def get_conditional_tournaments(organizer=None, reverse_order=False, type='ALL'):
  """
  按照条件获取锦标赛
  :param organizer: [optional] 比赛组织者
  :param reverse_order: [optional] 按注册开始时间排序时是否逆序
  :param type: [optional] 筛选方式
    'ALL': 返回全部
    'ONGOING': 返回当前进行中的（注册开始时间以后，最终结束时间以前）
    'FINISHED'： 返回已经结束的
    'COMING': 返回未来的
  :return:
  """
  tournaments = Tournament.objects.all()

  if organizer:
    tournaments.filter(organizer=organizer)

  if type.upper() == 'ONGOING':
    tournaments.filter(register_begin_time__lte=timezone.now(), overall_end_time__gt=timezone.now())
  elif type.upper() == 'FINISHED':
    tournaments.filter(overall_end_time__lte=timezone.now())
  elif type.upper() == 'COMING':
    tournaments.filter(register_begin_time__gt=timezone.now())

  if reverse_order:
    tournaments.order_by('-register_begin_time')
  else:
    tournaments.order_by('register_begin_time')

  return tournaments


