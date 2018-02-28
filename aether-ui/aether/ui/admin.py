from django.contrib import admin

from .api import models


class UserTokensAdmin(admin.ModelAdmin):

    list_display = ('user', 'kernel_token', 'odk_token',)
    search_fields = ('user',)
    ordering = list_display


admin.site.register(models.UserTokens, UserTokensAdmin)
