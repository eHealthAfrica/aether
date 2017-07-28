from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin

from . import models, forms


class ReadOnlyAdmin(CompareVersionAdmin):  # pragma: no cover
    '''
    ReadOnly, does not allow to add, edit or delete
    '''
    actions = None

    def has_add_permission(self, request):
        return False

    # without this permission it's not possible to display the object
    # def has_change_permission(self, request, obj=None):
    #     return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass


class SurveyAdmin(CompareVersionAdmin):
    form = forms.SurveyForm
    list_display = ('id', 'name', 'created_by',)


class ResponseAdmin(CompareVersionAdmin):
    form = forms.ResponseForm
    list_display = ('id', 'survey', 'created_by',)


class AttachmentAdmin(CompareVersionAdmin):
    list_display = ('id', 'response', 'name',)


class MapFunctionAdmin(CompareVersionAdmin):
    list_display = ('id', 'survey', 'code',)
    readonly_fields = ('code_prettified',)


class ReduceFunctionAdmin(CompareVersionAdmin):
    list_display = ('id', 'map_function', 'code',)
    readonly_fields = ('code_prettified', 'output_prettified', 'error',)


class MapResultAdmin(ReadOnlyAdmin):
    list_display = ('id', 'response', 'map_function', 'output', 'error',)
    readonly_fields = ('id', 'response', 'map_function', 'output_prettified', 'error',)


admin.site.register(models.Survey, SurveyAdmin)
admin.site.register(models.Response, ResponseAdmin)
admin.site.register(models.Attachment, AttachmentAdmin)
admin.site.register(models.MapFunction, MapFunctionAdmin)
admin.site.register(models.MapResult, MapResultAdmin)
admin.site.register(models.ReduceFunction, ReduceFunctionAdmin)
