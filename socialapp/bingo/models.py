from django.db import models
from django.utils import timezone

from socialapp.users.models import User


class BingoField(models.Model):
    """Used only for dynamic setting of a possible bingo fields"""

    name = models.CharField(max_length=100)
    url = models.URLField(default=None, blank=True, null=True)

    def __str__(self):
        return self.name


class Bingo(models.Model):
    date = models.DateField(default=timezone.now)
    card = models.JSONField(blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ("-date",)
        unique_together = ("date", "card")

    def __str__(self):
        return f"Bingo {self.date}"

    def generate_card(self, possible_fields: [BingoField], bingo_size=24):
        possible_fields = possible_fields.order_by("?")[0:bingo_size]
        return {field.name: {"completed": False, "url": field.url} for field in possible_fields}

    @property
    def order(self) -> dict:
        """Done in this way bcs JSONField orders keys of json"""
        return self.card["order"]

    def save(self, *args, **kwargs):
        if self.id is None:
            self.card = {"order": self.generate_card(BingoField.objects.all())}
        return super(Bingo, self).save(*args, **kwargs)

    def clear_card(self):
        current_card = self.card["order"]
        for field in current_card:
            field["completed"] = False
            # current_card[field] = False
        self.card["order"] = current_card
        self.completed = False
        self.save()
        self.bingoentry_set.all().delete()

    def _check_win_condition(self):
        order = self.order
        current_values = [bingo_field["completed"] for bingo_field in order.values()]
        possible_wins = [
            [0, 1, 2, 3, 4],
            [5, 6, 7, 8, 9],
            [10, 11, 12, 13, 14],
            [15, 16, 17, 18, 19],
            [20, 21, 22, 23, 24],
            [0, 5, 10, 15, 20],
            [1, 6, 11, 16, 21],
            [2, 7, 12, 17, 22],
            [3, 8, 13, 18, 23],
            [4, 9, 14, 19, 24],
            [0, 6, 12, 18, 24],
            [4, 8, 12, 16, 20],
        ]
        for pw in possible_wins:
            for i in pw:
                if not current_values[i]:
                    return False
            return True
        return False

    def change_field(self, field_name: str):
        order = self.order
        order[field_name]["completed"] = True
        self.card["order"] = order
        if self._check_win_condition():
            self.completed = True
        self.save()

    def check_field(self, field_name) -> bool:
        order = self.order
        print(order[field_name]["completed"])
        return order[field_name]["completed"]


class BingoEntry(models.Model):
    """Used to statistics"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    bingo = models.ForeignKey(Bingo, on_delete=models.CASCADE)
    bingo_field = models.ForeignKey(BingoField, on_delete=models.CASCADE)

    marked = models.BooleanField(default=False)
