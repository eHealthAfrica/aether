from django.contrib import admin

from .models import UserTokens


class UserTokensAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'kernel_token',
        'odk_importer_token',
        'couchdb_sync_token',
    )


admin.site.register(UserTokens, UserTokensAdmin)
