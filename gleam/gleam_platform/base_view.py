from django.views import View
from django.core.exceptions import PermissionDenied

class SignupOrganizerView(View):
  @staticmethod
  def validate_user_type(user, type):
    if user.type != type:
      raise PermissionDenied

