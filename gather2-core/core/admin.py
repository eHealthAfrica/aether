from django.contrib import admin
from reversion_compare.admin import CompareVersionAdmin
from .models import Survey, MapFunction, ReduceFunction


admin.site.register(ReduceFunction, CompareVersionAdmin)
admin.site.register(MapFunction, CompareVersionAdmin)
admin.site.register(Survey, CompareVersionAdmin)
