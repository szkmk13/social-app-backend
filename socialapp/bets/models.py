from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from socialapp.users.models import User


class Bet(models.Model):
    started_by = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()

    label_1 = models.CharField(max_length=50, default="TAK")
    label_2 = models.CharField(max_length=50, default="NIE")

    ratio_1 = models.FloatField(default=2)
    ratio_2 = models.FloatField(default=2)

    deadline = models.DateTimeField()
    created_at = models.DateField(auto_now=True)
    rewards_granted = models.BooleanField(default=False)

    def user_has_voted(self, user) -> bool:
        return self.votes.filter(user=user).exists()

    @property
    def is_open(self) -> bool:
        return self.deadline > timezone.now()

    def vote_for(self, a_or_b, amount):
        """vote impact is calculated by this equation y=x^0.7"""
        if self.total == 0:
            vote_impact = 0.23
        else:
            vote_impact = (amount / self.total * 100) ** 0.5 / 100
        if a_or_b == Vote.Fields.a:
            new_ratio_candidate = self.ratio_1 * (1 - vote_impact)
            self.ratio_1 = 1.05 if new_ratio_candidate < 1.05 else round(new_ratio_candidate, 2)
            self.ratio_2 = round(self.ratio_2 * (1 + vote_impact), 2)
        elif a_or_b == Vote.Fields.b:
            new_ratio_candidate = self.ratio_2 * (1 - vote_impact)
            self.ratio_2 = 1.05 if new_ratio_candidate < 1.05 else round(new_ratio_candidate, 2)
            self.ratio_1 = round(self.ratio_1 * (1 + vote_impact), 2)
        self.save()

    @property
    def total(self) -> int:
        return int(self.votes.aggregate(Sum("amount", default=0))["amount__sum"])

    @property
    def total_votes(self) -> int:
        return self.votes.count()

    def filter_votes_for(self, value_voting_for):
        return self.votes.filter(vote=value_voting_for)

    def exclude_votes_for(self, value_voting_for):
        return self.votes.exclude(vote=value_voting_for)

    def __str__(self):
        return self.text


class Vote(models.Model):
    class Fields(models.TextChoices):
        a = "a"
        b = "b"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="votes")
    bet = models.ForeignKey(Bet, on_delete=models.CASCADE, related_name="votes")
    vote = models.CharField(max_length=1)

    amount = models.IntegerField(validators=[MinValueValidator(1)])
    reward = models.IntegerField(default=0)
    has_won = models.BooleanField(default=None, null=True)
