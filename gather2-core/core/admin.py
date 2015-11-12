from django.contrib import admin

from .models import Survey


class SurveyAdmin(admin.ModelAdmin):
    pass


admin.site.register(Survey, SurveyAdmin)
