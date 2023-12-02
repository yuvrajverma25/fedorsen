from django.contrib import admin
from .models import AccessCode,AllowedCode


admin.site.register(AccessCode)


class AllowedCodeAdmin(admin.ModelAdmin):
    list_display = ('code',)  # Displayed columns in the admin list view
    search_fields = ('code',)  # Enable search by code in the admin panel

# Register the AllowedCode model with its admin class
admin.site.register(AllowedCode, AllowedCodeAdmin)