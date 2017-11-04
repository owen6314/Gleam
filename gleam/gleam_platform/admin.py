from django.contrib import admin

from .models import Organizer, Contestant, Team, Membership

admin.site.register([Organizer, Contestant, Team, Membership])
