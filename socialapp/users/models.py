import math
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import CharField, Sum, QuerySet, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class PatchNotes(models.Model):
    date = models.DateField(unique=True)
    text = models.TextField(help_text="You can use markdown here")
    title = models.CharField(max_length=100)
    version = models.CharField(max_length=40, blank=True)
    major = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Patch Notes"

    def save(self, *args, **kwargs):
        last_version = PatchNotes.objects.order_by("-date").first()
        if not last_version:
            return super().save(*args, **kwargs)
        if self.id is None:
            last_version = last_version.version
            major_number, minor_number = last_version.split(".")
            this_major = int(major_number)
            this_minor = int(minor_number)
            if self.major:
                this_major += 1
                this_minor = 0
            else:
                this_minor += 1
            self.version = f"{this_major}.{this_minor}"
        return super().save(*args, **kwargs)


class User(AbstractUser):
    """
    Default custom user model for socialapp.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    # First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    description = models.TextField(_("Description"), default="")

    points = models.IntegerField(default=0)
    coins = models.IntegerField(default=500)
    exp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    @property
    def exp_to_next_level(self) -> int:
        return round(math.sqrt(self.level / 10) * 1000 + (self.level - 1) ** 2)

    def save(self, *args, **kwargs):
        if self.exp >= self.exp_to_next_level:
            self.exp -= self.exp_to_next_level
            self.level += 1
        super().save(*args, **kwargs)

    def has_daily_quest(self) -> bool:
        return self.daily_quests.filter(created_at__date=timezone.now()).exists()

    def todays_quest(self) -> object | None:
        today = timezone.now()
        yesterday = today - timedelta(days=1)
        queryset = self.daily_quests.filter(Q(created_at__date=today) | Q(created_at__date=yesterday, redeemed=False))
        return queryset.first()

    def tokens_redeemed(self) -> bool:
        if quest := self.daily_quests.filter(created_at__date=timezone.now()).first():
            return quest.redeemed
        return False

    def redeem_from_quest(self, daily_quest) -> None:
        self.coins += daily_quest.quest.coins
        self.points += daily_quest.quest.points
        self.exp += daily_quest.quest.exp

        self.save()
        daily_quest.redeemed = True
        daily_quest.save(update_fields=["redeemed"])

    def redeem_from_attendance(self):
        self.coins += 15
        self.save(update_fields=["coins"])

    @property
    def daily_coins_redeemed(self) -> bool:
        return self.daily_coins.filter(date=timezone.now()).exists()

    @property
    def coins_lost_in_casino(self) -> int:
        return int(self.spin_set.filter(has_won=False).aggregate(Sum("amount", default=0))["amount__sum"])

    @property
    def coins_won_in_casino(self) -> int:
        return int(self.spin_set.filter(has_won=True).aggregate(Sum("amount", default=0))["amount__sum"])

    @property
    def casino_wins(self) -> int:
        return self.spin_set.filter(has_won=True).count()

    @property
    def casino_loses(self) -> int:
        return self.spin_set.filter(has_won=False).count()

    @property
    def has_unread_messages(self) -> bool:
        return self.messages_to.filter(read=False).exists()

    @property
    def unread_messages(self) -> QuerySet:
        return self.messages_to.filter(read=False)


class Message(models.Model):
    receiver = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="messages_to")
    sender = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="messages_from", null=True, blank=True)
    message = models.TextField()
    coins = models.IntegerField(default=100)
    read = models.BooleanField(default=False)


class DailyCoins(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_coins")
    date = models.DateField(auto_now_add=True)
    amount = models.FloatField(default=0)

    def save(self, *args, **kwargs):
        if self.id is None:
            daily_coins = 50
            self.user.coins += daily_coins
            self.user.save(update_fields=["coins"])
            self.amount = daily_coins
        return super().save(*args, **kwargs)


class Quest(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    duration = models.DurationField(default=0, help_text="in seconds")

    level_required = models.IntegerField(default=0)

    coins = models.IntegerField(default=150)
    points = models.IntegerField(default=10)
    exp = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.duration.total_seconds() / 60} min {self.title}"


class DailyQuest(models.Model):
    created_at = models.DateTimeField(blank=False, default=timezone.now)
    will_end_at = models.DateTimeField(blank=True)  # editable=False
    redeemed = models.BooleanField(default=False)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name="daily_quests")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_quests")

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, *args, **kwargs):
        if self.id is None:
            self.will_end_at = self.created_at + self.quest.duration
        super().save(force_insert, force_update, using, update_fields)
