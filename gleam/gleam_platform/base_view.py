from django.views import View
from django.core.exceptions import PermissionDenied

class BaseView(View):
  @staticmethod
  def validate_user_type(user, type):
    if user.type != type:
      raise PermissionDenied

  @staticmethod
  def get_model_data(model, fields):
    data = dict()
    for field in fields:
      data[field] = getattr(model, field)
    return data
