from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from .api import models, forms


class ProjectAdmin(CompareVersionAdmin):
    list_display = ('id', 'name', 'revision',)
    readonly_fields = ('id',)


class MappingAdmin(CompareVersionAdmin):
    form = forms.MappingForm
    list_display = ('id', 'name', 'revision', 'project',)
    readonly_fields = ('id',)


class SubmissionAdmin(CompareVersionAdmin):
    form = forms.SubmissionForm
    list_display = ('id', 'revision', 'mapping', 'map_revision',)
    readonly_fields = ('id',)


class SchemaAdmin(CompareVersionAdmin):
    form = forms.SchemaForm
    list_display = ('id', 'name', 'revision',)
    readonly_fields = ('id',)


class ProjectSchemaAdmin(CompareVersionAdmin):
    list_display = ('id', 'name', 'is_encrypted', 'project', 'schema',)
    readonly_fields = ('id',)


class EntityAdmin(CompareVersionAdmin):
    form = forms.EntityForm
    list_display = ('id', 'revision', 'status', 'projectschema',  'submission',)
    readonly_fields = ('id', 'submission',)


admin.site.register(models.Project, ProjectAdmin)
admin.site.register(models.Mapping, MappingAdmin)
admin.site.register(models.Submission, SubmissionAdmin)
admin.site.register(models.Schema, SchemaAdmin)
admin.site.register(models.ProjectSchema, ProjectSchemaAdmin)
admin.site.register(models.Entity, EntityAdmin)
