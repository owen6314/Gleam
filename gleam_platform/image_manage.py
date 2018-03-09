from django.contrib.auth.decorators import login_required
from django.views.static import serve

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.shortcuts import HttpResponse

from .models import Image
from gleam.settings import MEDIA_ROOT


def serve_image(request, path, document_root=MEDIA_ROOT):
  try:
    obj = Image.objects.get(image=path)
    if obj.type != 'P' and request.user not in obj.accesses.all():
      raise PermissionDenied
    return serve(request, path, document_root)

  except:
    return HttpResponse("Sorry you don't have permission to access this file")
