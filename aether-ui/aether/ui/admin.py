from django.contrib import admin

from .api import models


class PipelineAdmin(admin.ModelAdmin):

    list_display = ('name', 'published_on',)
    search_fields = ('name',)
    ordering = list_display


admin.site.register(models.Pipeline, PipelineAdmin)
