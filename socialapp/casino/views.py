import itertools

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from socialapp.casino.models import HighCard, Roulette
from socialapp.casino.serializers import (
    GameSerializer,
    HighCardResultSerializer,
    HighCardPlaySerializer,
    RouletteSerializer,
    RouletteResultSerializer,
)


@extend_schema(tags=["casino WORK IN PROGRESS"])
class CardGameViewSet(GenericViewSet):
    queryset = HighCard.objects.all()
    permission_classes = [IsAuthenticated]

    @action(detail=True)
    def play(self, request, pk=None):
        card_game = HighCard.objects.get(id=pk)
        return Response(card_game.play())


@extend_schema(tags=["casino"])
class CasinoViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_classes = {"roulette": RouletteSerializer, "high_card": HighCardPlaySerializer}

    CARD_VALUES = [2, 3, 4, 5, 6, 7, 8, 9, 10, "J", "Q", "K", "A"]
    CARD_SUITS = ["clubs", "hearts", "diamonds", "spades"]
    DECK = [f"{x}of{y}" for x, y in itertools.product(CARD_VALUES, CARD_SUITS)]

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, GameSerializer)

    @extend_schema(
        request=RouletteSerializer,
        responses={200: RouletteResultSerializer},
        summary="""Place bet on roulette""",
    )
    @action(methods=["post"], detail=False)
    def roulette(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request, "user": request.user})
        serializer.is_valid(raise_exception=True)
        user_number = serializer.validated_data.get("number")
        roulette = Roulette()
        result = roulette.play(
            user=request.user,
            bet=serializer.validated_data["bet"],
            bet_amount=serializer.validated_data["bet_amount"],
            user_number=user_number,
        )
        serializer = RouletteResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=HighCardPlaySerializer,
        responses={200: HighCardResultSerializer},
        summary="""Place a bet if next card will be higher lower or same""",
    )
    @action(methods=["post"], detail=False)
    def high_card(self, request, *args, **kwargs):
        serializer = HighCardPlaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        game_object, _ = HighCard.objects.get_or_create(user=request.user)
        bet_amount = serializer.validated_data["bet_amount"]
        bet = serializer.validated_data["bet"]
        data = game_object.play(deck=self.DECK, bet_amount=bet_amount, bet=bet)
        serializer = HighCardResultSerializer(data=data, context={"user": request.user, "game_object": game_object})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)
