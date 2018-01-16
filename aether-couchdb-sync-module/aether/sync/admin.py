from django.contrib import admin

from .api.models import MobileUser, DeviceDB

admin.site.register(MobileUser)
admin.site.register(DeviceDB)
