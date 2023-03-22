from copy import deepcopy

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import pgettext_lazy

from accounts.forms import CustomUserChangeForm, CustomUserCreationForm
from accounts.models import User


@admin.register(User)
class _CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    # --------------------------------------
    # List desplay

    list_display = list(UserAdmin.list_display)
    list_display.remove("first_name")
    list_display.remove("is_staff")
    list_display.remove("last_name")
    list_display.append("name")
    list_display = tuple(list_display)

    # --------------------------------------
    # List filter

    list_filter = list(UserAdmin.list_filter)
    list_filter.remove("is_active")
    list_filter.remove("is_staff")
    list_filter = tuple(list_filter)

    # --------------------------------------
    # Fieldsets

    fieldsets = list(deepcopy(UserAdmin.fieldsets))

    # Personal info
    (index,) = [
        index
        for index, (label, fieldset) in enumerate(fieldsets)
        if label == "Personal info"
    ]
    fields = list(fieldsets[index][1]["fields"])
    fields.insert(0, "name")
    fields.append("photo")
    fields.remove("first_name")
    fields.remove("last_name")
    fieldsets[index][1]["fields"] = fields
    del fields, index

    # Preferences
    fieldsets.append(
        [pgettext_lazy("user field subset", "Preferences"), {"fields": ["language"]}]
    )

    fieldsets = tuple(fieldsets)

    # --------------------------------------
    # Search fields

    search_fields = list(UserAdmin.search_fields)
    search_fields.remove("first_name")
    search_fields.remove("last_name")
    search_fields.append("name")
    search_fields = tuple(search_fields)
