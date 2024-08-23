from django.contrib import admin

from socialapp.bingo.models import BingoField, Bingo, BingoEntry


@admin.register(Bingo)
class BingoAdmin(admin.ModelAdmin):
    list_display = ("date", "card")
    list_filter = ("date",)


@admin.register(BingoField)
class BingoFieldAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(BingoEntry)
class BingoEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "bingo", "marked")
    list_filter = ("bingo", "user")

    def date(self, obj):
        return obj.bingo.date
