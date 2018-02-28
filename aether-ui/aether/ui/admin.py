from django.contrib import admin

from .api import models


class UserTokensAdmin(admin.ModelAdmin):

    list_display = ('user', 'kernel_token', 'odk_token',)
    search_fields = ('user',)
    ordering = list_display


class SurveyAdmin(admin.ModelAdmin):

    list_display = ('mapping_id', 'name',)
    search_fields = ('name',)
    ordering = list_display


class MaskAdmin(admin.ModelAdmin):

    list_display = ('survey', 'name', 'columns',)
    search_fields = ('survey__name', 'name', 'columns',)
    ordering = list_display


admin.site.register(models.UserTokens, UserTokensAdmin)
admin.site.register(models.Survey, SurveyAdmin)
admin.site.register(models.Mask, MaskAdmin)
