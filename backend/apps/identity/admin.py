from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class YfenUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Profil YFEN", {"fields": ("display_name",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Profil YFEN", {"fields": ("email", "display_name")}),)
    list_display = ("username", "email", "display_name", "is_staff", "is_active")
    search_fields = ("username", "email", "display_name")
