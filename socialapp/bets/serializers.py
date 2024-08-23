from datetime import timedelta

from django.core.validators import MinValueValidator
from django.utils import timezone
from rest_framework import serializers

from socialapp.bets.models import Bet, Vote
from socialapp.meetings.models import Meeting, Attendance, Place
from socialapp.users.models import User
from socialapp.users.serializers import UserListSerializer
from socialapp.utils import DetailException


class BetsListSerializer(serializers.ModelSerializer):
    started_by = UserListSerializer()
    can_vote = serializers.SerializerMethodField()

    def get_can_vote(self, obj) -> bool:
        return not obj.votes.filter(user=self.context["request"].user).exists()

    class Meta:
        model = Bet
        fields = [
            "id",
            "started_by",
            "text",
            "total_votes",
            "can_vote",
            "label_1",
            "label_2",
            "ratio_1",
            "ratio_2",
            "total",
            "created_at",
            "deadline",
            "rewards_granted",
            "is_open",
        ]


class VoteSerializer(serializers.ModelSerializer):
    bet = BetsListSerializer(read_only=True)

    class Meta:
        model = Vote
        fields = "__all__"


class CreateBetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bet
        exclude = ["started_by", "rewards_granted"]

    def validate(self, attrs):
        attrs["started_by"] = self.context["request"].user
        if not attrs.get("deadline"):
            attrs["deadline"] = timezone.now() + timedelta(days=1)
        return super().validate(attrs)


class BetVoteSerializer(serializers.ModelSerializer):
    vote = serializers.ChoiceField(choices=Vote.Fields)

    class Meta:
        model = Vote
        fields = ["amount", "vote"]

    def validate(self, attrs):
        attrs["user"] = self.context["request"].user
        attrs["bet"] = self.context["bet"]
        if attrs["amount"] > self.context["request"].user.coins:
            raise DetailException("Not enough coins")
        if self.context["bet"].user_has_voted(attrs["user"]):
            raise DetailException("Already voted")
        if self.context["bet"].rewards_granted:
            raise DetailException("Rewards already granted")
        if not self.context["bet"].is_open:
            raise DetailException("Bet already closed, wait for rewards to be granted")
        attrs = super().validate(attrs)
        return attrs

    def create(self, validated_data):
        user = validated_data["user"]
        user.coins -= validated_data["amount"]
        user.save(update_fields=["coins"])
        return super().create(validated_data)
