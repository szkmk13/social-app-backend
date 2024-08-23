from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from socialapp.users.models import User, DailyQuest, Quest, DailyCoins, PatchNotes
from socialapp.permissions import IsYouOrReadOnly

from socialapp.users.serializers import (
    UserListSerializer,
    DailyQuestSerializer,
    DailyQuestStartSerializer,
    QuestSerializer,
    PatchNotesSerializer,
    DailyQuestStatusSerializer,
    UserDetailSerializer,
    DailyQuestRedeemSerializer,
    ReadMessageSerializer,
)

from django.http import Http404

from allauth.account.models import (
    get_emailconfirmation_model,
)


class SocialappConfirmEmailView(GenericAPIView):
    permission_classes = [AllowAny]

    def get_object(self, queryset=None):
        key = self.kwargs["key"]
        model = get_emailconfirmation_model()
        emailconfirmation = model.from_key(key)
        if not emailconfirmation:
            raise Http404()
        return emailconfirmation

    @extend_schema(request=None, responses={200: None})
    def post(self, *args, **kwargs):
        self.object = confirmation = self.get_object()
        email_address = confirmation.confirm(self.request)
        if not email_address:
            return Response("Email does not exist", status=404)
        user = confirmation.email_address.user
        user.is_active = True
        user.save()
        return Response({"detail": "Email confirmed"})


@extend_schema(tags=["patch notes"], summary="List of patch notes ordered by date")
class PatchNotesView(ListModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    queryset = PatchNotes.objects.order_by("-date")
    serializer_class = PatchNotesSerializer


@extend_schema(summary="Default actions to users")
class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = User.objects.all()
    permission_classes = [IsYouOrReadOnly]
    serializer_classes = {
        "list": UserListSerializer,
        "read_message": ReadMessageSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, UserDetailSerializer)

    @extend_schema(summary="Info about current user")
    @action(detail=False)
    def me(self, request):
        serializer = self.get_serializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @extend_schema(tags=["daily"], summary="Redeem daily coins")
    @action(detail=False, methods=["post"])
    def redeem_daily_coins(self, request):
        user = request.user
        if user.daily_coins_redeemed:
            return Response("Coins already redeemed", status=status.HTTP_400_BAD_REQUEST)
        DailyCoins.objects.create(user=user)
        user.refresh_from_db()
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Read message and claim rewards", request=ReadMessageSerializer, responses={204: None})
    @action(detail=False, methods=["post"])
    def read_message(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        message = serializer.validated_data["id"]
        user.coins += message.coins
        message.read = True
        user.save(update_fields=["coins"])
        message.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["daily"])
class DailyQuestViewSet(GenericViewSet):
    serializer_class = DailyQuestSerializer
    queryset = DailyQuest.objects.all()
    serializer_classes = {
        "start": DailyQuestStartSerializer,
        "choices": QuestSerializer,
        "status": DailyQuestStatusSerializer,
    }

    def get_queryset(self):
        return DailyQuest.objects.filter(user=self.request.user)  # type: ignore[misc]

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, DailyQuestSerializer)

    @extend_schema(request=None, responses=QuestSerializer(many=True), summary="List of possible daily quests")
    @action(detail=False, methods=["get"], pagination_class=None)
    def choices(self, request):
        serializer = self.get_serializer(
            Quest.objects.order_by("level_required"), many=True, context={"request": request}
        )
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @extend_schema(
        request=DailyQuestStartSerializer, responses={201: DailyQuestStartSerializer}, summary="Start a daily quest"
    )
    @action(detail=False, methods=["post"])
    def start(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=None, responses={200: DailyQuestRedeemSerializer}, summary="Redeem reward from a daily quest"
    )
    @action(detail=False, methods=["post"])
    def redeem(self, request):
        if request.user.tokens_redeemed():
            return Response("Rewards already redeemed", status=status.HTTP_400_BAD_REQUEST)
        now = timezone.now()
        daily_quest = request.user.todays_quest()
        if not daily_quest:
            return Response("No daily quest", status=status.HTTP_400_BAD_REQUEST)
        if daily_quest.will_end_at >= now:
            return Response("Quest already started, wait for it to end", status=status.HTTP_400_BAD_REQUEST)

        request.user.redeem_from_quest(daily_quest)
        return Response(
            data=DailyQuestRedeemSerializer(daily_quest.quest).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(request=None, responses={200: DailyQuestStatusSerializer}, summary="Status of a daily quest")
    @action(detail=False, methods=["get"])
    def status(self, request):
        if request.user.todays_quest():
            serializer = self.get_serializer(request.user.todays_quest(), context={"request": request})
            return Response(serializer.data)
        if not request.user.has_daily_quest():
            return Response({"detail": "Quest not started"}, status.HTTP_400_BAD_REQUEST)
