from django.contrib import admin

from socialapp.meetings.models import Meeting, Attendance, Place


class AttendanceInline(admin.TabularInline):
    model = Attendance


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("__str__", "date", "confirmed_by_majority")
    list_filter = ("confirmed_by_majority", "date")
    inlines = [AttendanceInline]
    actions = ["confirm"]

    def confirm(self, request, queryset):
        queryset.update(confirmed_by_majority=True)
        return


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("user", "meeting", "confirmed")
    list_filter = ("user", "confirmed")


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name",)
