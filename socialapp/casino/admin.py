from django.contrib import admin
from django.http import HttpResponseRedirect

from socialapp.casino.models import Spin, Game, Symbol


@admin.register(Symbol)
class SymbolAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "image", "weight", "value")


@admin.register(Spin)
class SpinAdmin(admin.ModelAdmin):
    list_display = ("user", "game", "amount", "has_won")
    list_filter = ("user", "game")


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    actions = ["play"]

    @admin.action()
    def run(self, request, queryset):
        obj = queryset.first()
        obj.play(user=request.user, chosen_lines=1)
        return HttpResponseRedirect("/admin/casino/game")
