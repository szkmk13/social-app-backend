from django.db import models
from socialapp.users.models import User


class Place(models.Model):
    name = models.CharField(max_length=100)

    @property
    def used_in_meetings(self) -> int:
        return self.meeting_set.count()

    def __str__(self):
        return self.name


class Meeting(models.Model):
    MIN_ATTENDANCE = 3

    date = models.DateField()
    users = models.ManyToManyField(User, through="Attendance")
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True)
    confirmed_by_majority = models.BooleanField(default=False)
    description = models.TextField(default="")

    pizza = models.BooleanField(default=False)
    casino = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} {self.place.name}"

    @property
    def count_attended(self) -> int:
        return self.users.count()

    @property
    def count_confirmed(self) -> int:
        return self.attendance_set.filter(confirmed=True).count()

    @property
    def majority_threshold(self) -> int:
        return round(self.count_attended / 2)

    @property
    def confirmed_by_less_half_users(self) -> bool:
        return self.count_confirmed < self.majority_threshold

    def rewards_based_on_size_of_meeting(self) -> dict:
        return {
            "coins": 100 * (1 + (self.count_attended - self.MIN_ATTENDANCE) / 2),
            "points": 50 * (1 + (self.count_attended - self.MIN_ATTENDANCE) / 2),
            "exp": 100 * (1 + (self.count_attended - self.MIN_ATTENDANCE)),
        }

    def confirmed_by_user(self, user):
        if user in self.users.all():
            return self.attendance_set.get(user=user).confirmed
        return False


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="+")
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    drinking = models.BooleanField(default=True)
    confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} at {self.meeting}"
