from rest_framework.serializers import *
from django.core.validators import MinValueValidator

from socialapp.casino.models import Game, Symbol, Spin, GAMES, Roulette
from socialapp.utils import DetailException


class SymbolSerializer(ModelSerializer):
    class Meta:
        model = Symbol
        fields = "__all__"


class GameSerializer(ModelSerializer):
    class Meta:
        model = Game
        fields = "__all__"


class GameSpinSerializer(ModelSerializer):
    bet_amount = IntegerField(write_only=True, validators=[MinValueValidator(0)])
    lines_chosen = IntegerField(default=1, write_only=True)

    class Meta:
        model = Game
        fields = ["bet_amount", "lines_chosen"]

    def validate(self, attrs):
        user = self.context["request"].user
        if attrs["bet_amount"] > user.coins:
            raise DetailException("Insufficient coins")
        return attrs


class HighCardPlaySerializer(Serializer):
    bet_amount = IntegerField(write_only=True, validators=[MinValueValidator(0)])
    bet = ChoiceField(choices=["high", "low", "equal"])


class HighCardResultSerializer(Serializer):
    demo_play = BooleanField(default=False)
    card_value = CharField()
    card_suit = CharField()
    bet_amount = IntegerField()
    has_won = BooleanField(default=False)
    reward = IntegerField(default=0)

    multipliers = ListField(required=False)

    next_card_value = CharField(required=False)
    previous_card_value = CharField(required=False)
    bet = CharField(write_only=True)

    FACES_VALUES = {"J": 11, "Q": 12, "K": 13, "A": 14}
    HIGH_LOW_MULTIPLIER = 1.4
    EQUAL_MULTIPLIER = 6

    class Meta:
        fields = "__all__"

    def to_representation(self, instance):
        instance = super().to_representation(instance)
        card_value_string = instance["card_value"]
        card_value = self.FACES_VALUES.get(card_value_string) if card_value_string.isalpha() else int(card_value_string)
        instance["multipliers"] = self.calculate_multipliers_based_on_previous_card(card_value)
        return instance

    def calculate_multipliers_based_on_previous_card(self, card_value) -> (float, float, float):
        equal = 6
        if card_value == 8:
            low = 1.55
            high = 1.55
        elif card_value == 2:
            low = 0
            high = 1
        elif card_value == 14:
            low = 1
            high = 0
        elif card_value > 8:
            low = round(0.1 * -abs(card_value - 8) + 1.55, 2)
            high = round(0.1 * abs(card_value - 8) + 1.55, 2)
        else:
            low = round(0.1 * abs(card_value - 8) + 1.55, 2)
            high = round(0.1 * -abs(card_value - 8) + 1.55, 2)
        return low, equal, high

    def validate(self, attrs):
        if attrs["demo_play"]:
            return attrs
        previous_card_value = (
            self.FACES_VALUES.get(attrs["previous_card_value"])
            if attrs["previous_card_value"].isalpha()
            else int(attrs["previous_card_value"])
        )
        next_card_value = (
            self.FACES_VALUES.get(attrs["next_card_value"])
            if attrs["next_card_value"].isalpha()
            else int(attrs["next_card_value"])
        )
        bet_amount = attrs.get("bet_amount")
        user = self.context["user"]
        if user.coins < bet_amount:
            raise DetailException("Insufficient coins")
        bet = attrs.get("bet")
        low_multiplier, equal_multiplier, high_multiplier = self.calculate_multipliers_based_on_previous_card(
            previous_card_value
        )

        user.coins -= bet_amount
        if bet == "high":
            if next_card_value > previous_card_value:
                user.coins += high_multiplier * bet_amount
                attrs["has_won"] = True
                attrs["reward"] = high_multiplier * bet_amount
        elif bet == "low":
            if next_card_value < previous_card_value:
                user.coins += low_multiplier * bet_amount
                attrs["has_won"] = True
                attrs["reward"] = low_multiplier * bet_amount
        elif bet == "equal":
            if next_card_value == previous_card_value:
                user.coins += equal_multiplier * bet_amount
                attrs["has_won"] = True
                attrs["reward"] = equal_multiplier * bet_amount

        spin = Spin(game=GAMES.HIGH_CARD, user=user, has_won=attrs["has_won"])
        spin.amount = attrs["reward"] - bet_amount if attrs["has_won"] else bet_amount
        spin.save()
        user.save(update_fields=["coins"])
        return attrs


class SpinResultSerializer(Serializer):
    won = BooleanField(read_only=True, default=False)
    amount = IntegerField(read_only=True, default=0)
    result: ListSerializer[SymbolSerializer] = ListSerializer(child=SymbolSerializer(many=True))


class RouletteSerializer(Serializer):
    bet_amount = IntegerField(write_only=True, validators=[MinValueValidator(0)])
    bet = ChoiceField(choices=Roulette.CHOICES)
    number = IntegerField(write_only=True, required=False)

    def validate(self, attrs):
        if attrs.get("number") and attrs["bet"] != Roulette.CHOICES.NUMBER:
            raise DetailException("Chose number as bet")
        user = self.context["request"].user
        if attrs["bet_amount"] > user.coins:
            raise DetailException("Insufficient coins")
        return super().validate(attrs)


class RouletteResultSerializer(Serializer):
    has_won = BooleanField(default=False)
    amount = IntegerField()
    rolled_number = IntegerField()
    rolled_number_index = IntegerField()
    color = CharField()
