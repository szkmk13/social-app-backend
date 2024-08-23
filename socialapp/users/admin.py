from django.contrib.auth import admin as auth_admin
from django.utils.translation import gettext_lazy as _

from .forms import UserAdminChangeForm
from .forms import UserAdminCreationForm
from .models import User, Quest, DailyQuest, DailyCoins, PatchNotes, Message
from django.contrib import admin


@admin.register(PatchNotes)
class PatchNotesAdmin(admin.ModelAdmin):
    list_display = ("version", "date", "text")
    list_filter = ("date",)


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "duration", "level_required", "coins", "points", "exp")


@admin.register(DailyCoins)
class DailyCoinsAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "amount")
    list_filter = ("date", "user")


@admin.register(DailyQuest)
class DailyQuestAdmin(admin.ModelAdmin):
    list_display = ("user", "quest", "created_at", "will_end_at", "redeemed")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("receiver", "sender", "message", "coins", "read")
    list_filter = ("read", "receiver", "sender")


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    form = UserAdminChangeForm
    add_form = UserAdminCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        # (_("Personal info"), {"fields": ("name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    # "groups",
                    # "user_permissions",
                ),
            },
        ),
        ("Trójmiejskie", {"fields": ("level", "exp", "coins", "points")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    list_display = ["username", "level", "exp", "points", "coins", "is_active"]
    search_fields = ["name"]
    actions = [
        "write_message",
    ]

    @admin.action()
    def write_message(self, request, queryset):
        for user in queryset:
            Message.objects.create(receiver=user, message="test")
