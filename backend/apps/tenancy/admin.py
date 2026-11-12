from django.contrib import admin

from .models import BusinessUnit, LegalEntity, Workspace, WorkspaceMembership


class WorkspaceMembershipInline(admin.TabularInline):
    model = WorkspaceMembership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "default_currency", "status", "created_at")
    list_filter = ("status", "default_currency")
    search_fields = ("name", "owner__email")
    inlines = (WorkspaceMembershipInline,)


@admin.register(LegalEntity)
class LegalEntityAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "workspace", "country_code", "functional_currency", "status")
    list_filter = ("status", "country_code", "functional_currency")
    search_fields = ("name", "code", "workspace__name")


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "entity", "unit_type", "manager", "is_active")
    list_filter = ("unit_type", "is_active")
    search_fields = ("name", "code", "entity__name")


@admin.register(WorkspaceMembership)
class WorkspaceMembershipAdmin(admin.ModelAdmin):
    list_display = ("workspace", "user", "role", "is_active", "invited_at")
    list_filter = ("role", "is_active")
    search_fields = ("workspace__name", "user__email")
