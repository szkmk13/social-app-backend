from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from socialapp.bingo.models import Bingo, BingoEntry, BingoField
from socialapp.bingo.serializers import BingoSerializer, BingoChangeFieldSerializer


class BingoViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Bingo.objects.all()
    serializer_classes = {
        "list": BingoSerializer,
        "mark_field_as_done": BingoChangeFieldSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes[self.action]

    @extend_schema(request=BingoChangeFieldSerializer, responses={200: BingoSerializer})
    @action(methods=["post"], detail=True)
    def change_field(self, request, *args, **kwargs):
        bingo = self.get_object()
        serializer = self.get_serializer(data=request.data, context={"bingo": bingo})
        serializer.is_valid(raise_exception=True)
        field_name = serializer.validated_data["field_name"]
        bingo.change_field(field_name=field_name)
        BingoEntry.objects.create(
            bingo=bingo, date=bingo.date, bingo_field=BingoField.objects.get(name=field_name), marked=True
        )
        return Response(BingoSerializer(bingo).data)

    @extend_schema(request=None, responses={200: str}, description="Clears today's bingo")
    @action(methods=["post"], detail=True)
    def clear(self, request, *args, **kwargs):
        bingo = self.get_object()
        bingo.clear_card()
        return Response("Card cleared", 200)


class BingoGetOrCreateAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = BingoSerializer

    def get(self, request, *args, **kwargs):
        bingo, _ = Bingo.objects.get_or_create(date=timezone.now().date())
        serializer = self.serializer_class(bingo)
        return Response(serializer.data, status=200)
