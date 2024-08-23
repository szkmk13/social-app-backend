import enum
import itertools
import random
from abc import abstractmethod
from random import shuffle

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import TextChoices

from socialapp.users.admin import User


class GAMES(models.TextChoices):
    HIGH_CARD = "HighCard"
    ROULETTE = "Roulette"
    BLACK_JACK = "BlackJack"
    BELLS = "Bells"


class Symbol(models.Model):
    name = models.CharField(max_length=128)
    image = models.ImageField()
    weight = models.PositiveIntegerField(
        default=1, help_text="Weight of the symbol, the higher number the bigger chance of it rolling"
    )
    value = models.PositiveIntegerField(
        default=1,
        help_text="Value of the symbol, if user rolls a line of them, this is the amount it's gonna be multiplied by",
    )

    def __str__(self):
        return f"{self.name} weight:{self.weight} multiplier:{self.value}"


class Spin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.CharField(max_length=20, choices=GAMES.choices)
    time = models.DateTimeField(auto_now_add=True)

    has_won = models.BooleanField(default=False)
    chosen_lines = models.PositiveIntegerField(default=1)
    amount = models.IntegerField(validators=[MinValueValidator(1)])


class Game(models.Model):
    name = models.CharField(max_length=50, default="")

    @property
    def type(self):
        return

    def __str__(self):
        return self.name


class HighCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    last_card = models.CharField(max_length=20, default="")

    def play(self, deck: list, bet_amount: int, bet: str, *args, **kwargs) -> dict:
        shuffle(deck)
        next_card = deck[0]

        if bet_amount == 0:
            card_value, card_suit = next_card.split("of")
            data = {
                "bet_amount": bet_amount,
                "card_suit": card_suit,
                "card_value": card_value,
                "demo_play": True,
                "bet": bet,
            }
            self.last_card = next_card
            self.save()
            return data

        next_card_value, next_card_suit = next_card.split("of")
        data = {
            "bet_amount": bet_amount,
            "card_suit": next_card_suit,
            "card_value": next_card_value,
            "previous_card_value": self.last_card.split("of")[0],
            "next_card_value": next_card_value,
            "bet": bet,
        }
        self.last_card = next_card
        self.save()
        return data


class Roulette(Game):
    NUMBER_MULTIPLIER = 36
    COLUMN_AND_DOZEN_MULTIPLIER = 3
    COLOR_MULTIPLIER = 2
    RED_COLOR = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
    BLACK_COLOR = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

    class CHOICES(TextChoices):
        EVEN = "EVEN"
        ODD = "ODD"
        BLACK = "BLACK"
        RED = "RED"
        GREEN = "GREEN"
        NUMBER = "NUMBER"
        FIRST_12 = "FIRST12"
        SECOND_12 = "SECOND12"
        THIRD_12 = "THIRD12"
        ROW_1 = "ROW_1"
        ROW_2 = "ROW_2"
        ROW_3 = "ROW_3"
        HALF_LOW = "HALF_LOW"
        HALF_HIGH = "HALF_HIGH"

    def check_bet(self, bet, ball_roll, user_number):
        if bet == self.CHOICES.GREEN or user_number == 0:
            return ball_roll == 0
        elif bet == self.CHOICES.ODD:
            return ball_roll % 2 == 1
        elif bet == self.CHOICES.EVEN:
            return ball_roll % 2 == 0
        elif bet == self.CHOICES.HALF_HIGH:
            return ball_roll >= 19
        elif bet == self.CHOICES.HALF_LOW:
            return ball_roll <= 18
        elif bet == self.CHOICES.RED:
            return ball_roll in self.RED_COLOR
        elif bet == self.CHOICES.BLACK:
            return ball_roll in self.BLACK_COLOR
        elif bet == self.CHOICES.FIRST_12:
            return 1 <= ball_roll <= 12
        elif bet == self.CHOICES.SECOND_12:
            return 13 <= ball_roll <= 24
        elif bet == self.CHOICES.THIRD_12:
            return 25 <= ball_roll <= 36
        elif bet == self.CHOICES.ROW_1:
            return ball_roll % 3 == 1
        elif bet == self.CHOICES.ROW_2:
            return ball_roll % 3 == 2
        elif bet == self.CHOICES.ROW_3:
            return ball_roll % 3 == 0
        return user_number == ball_roll

    def bet_multiplier(self, bet):
        if bet in [self.CHOICES.GREEN, self.CHOICES.NUMBER]:
            return self.NUMBER_MULTIPLIER
        if bet in [
            self.CHOICES.RED,
            self.CHOICES.BLACK,
            self.CHOICES.EVEN,
            self.CHOICES.ODD,
            self.CHOICES.HALF_HIGH,
            self.CHOICES.HALF_LOW,
        ]:
            return self.COLOR_MULTIPLIER
        if bet in [
            self.CHOICES.ROW_2,
            self.CHOICES.ROW_3,
            self.CHOICES.ROW_1,
            self.CHOICES.FIRST_12,
            self.CHOICES.SECOND_12,
            self.CHOICES.THIRD_12,
        ]:
            return self.COLUMN_AND_DOZEN_MULTIPLIER

    VALUE_TO_FRONTEND_INDEX = {
        0: 0,
        32: 1,
        15: 2,
        19: 3,
        4: 4,
        21: 5,
        2: 6,
        25: 7,
        17: 8,
        34: 9,
        6: 10,
        27: 11,
        13: 12,
        36: 13,
        11: 14,
        30: 15,
        8: 16,
        23: 17,
        10: 18,
        5: 19,
        24: 20,
        16: 21,
        33: 22,
        1: 23,
        20: 24,
        14: 25,
        31: 26,
        9: 27,
        22: 28,
        18: 29,
        29: 30,
        7: 31,
        28: 32,
        12: 33,
        35: 34,
        3: 35,
        26: 36,
    }

    def play(self, user, bet, bet_amount, user_number, *args, **kwargs):
        ball_roll = random.randint(0, 36)
        user.coins -= bet_amount
        spin = Spin(game=GAMES.ROULETTE, user=user, amount=bet_amount)
        user_number = user_number or 100
        has_won = self.check_bet(bet=bet, ball_roll=ball_roll, user_number=user_number)
        won_amount = 0
        if has_won:
            won_amount = bet_amount * self.bet_multiplier(bet=bet)
            user.coins += won_amount
            spin.amount = won_amount - bet_amount
            spin.has_won = True
        spin.save()
        user.save()
        color = "RED"
        if ball_roll == 0:
            color = "GREEN"
        elif ball_roll in self.BLACK_COLOR:
            color = "BLACK"
        return {
            "rolled_number": ball_roll,
            "rolled_number_index": self.VALUE_TO_FRONTEND_INDEX[ball_roll],
            "has_won": has_won,
            "amount": won_amount,
            "color": color,
        }


class BlackJack(Game):
    @staticmethod
    def play(user, chosen_lines, *args, **kwargs):
        return None


class Bells(Game):
    @staticmethod
    def play(user, chosen_lines, *args, **kwargs):
        return None
