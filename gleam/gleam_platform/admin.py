from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Organizer, Contestant, Team, Membership, Profile, Contest

admin.site.register([Contest, Profile])

