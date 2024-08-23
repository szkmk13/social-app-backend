from django.db.models import Count
from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status

from socialapp.meetings.models import Meeting, Place, Attendance
from socialapp.meetings.serializers import (
    MeetingListSerializer,
    MeetingAddSerializer,
    PlaceSerializer,
    MeetingDetailSerializer,
    ConfirmMeetingListSerializer,
)


@extend_schema(summary="Meetings view", tags=["meetings"])
class MeetingViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.CreateModelMixin):
    queryset = Meeting.objects.order_by("-date")
    serializer_classes = {
        "retrieve": MeetingDetailSerializer,
        "create": MeetingAddSerializer,
        "confirmed": ConfirmMeetingListSerializer,
        "not_confirmed": ConfirmMeetingListSerializer,
        "places": PlaceSerializer,
    }

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, MeetingListSerializer)

    @extend_schema(summary="List of most used places", responses={200: PlaceSerializer(many=True)})
    @action(methods=["get"], detail=False)
    def places(self, request, *args, **kwargs):
        places = Place.objects.annotate(meetings_count=Count("meeting")).order_by("-meetings_count")
        return Response(self.get_serializer(places, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="List of meetings that are confirmed",
        responses={200: ConfirmMeetingListSerializer(many=True)},
    )
    @action(methods=["get"], detail=False)
    def confirmed(self, request, *args, **kwargs):
        queryset = self.get_queryset().filter(confirmed_by_majority=True)
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="List of meetings that are confirmed",
        responses={200: ConfirmMeetingListSerializer(many=True)},
    )
    @action(methods=["get"], detail=False)
    def not_confirmed(self, request, *args, **kwargs):
        not_confirmed_meetings = self.get_queryset().filter(confirmed_by_majority=False)
        serializer = ConfirmMeetingListSerializer(not_confirmed_meetings, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Confirm your attendance on meeting, by doing so gain coins and points",
        request=None,
        responses={200: str},
    )
    @action(methods=["post"], detail=True)
    def confirm(self, request, *args, **kwargs):
        meeting = self.get_object()
        user = request.user
        attendance = meeting.attendance_set.get(user=request.user)
        if not attendance:
            return Response(data="You weren't there", status=status.HTTP_400_BAD_REQUEST)
        if attendance.confirmed:
            return Response(data="You have already confirmed your attendance", status=status.HTTP_400_BAD_REQUEST)

        attendance.confirmed = True
        attendance.save(update_fields=["confirmed"])
        user.redeem_from_attendance()

        if meeting.confirmed_by_majority:
            return Response("Confirmed")

        current_confirmed_count = self.get_object().count_confirmed
        if current_confirmed_count >= meeting.majority_threshold:
            meeting.confirmed_by_majority = True
            meeting.save(update_fields=["confirmed_by_majority"])
            rewards = meeting.rewards_based_on_size_of_meeting()
            for user in meeting.users.all():
                user.coins += rewards["coins"]
                user.points += rewards["points"]
                user.exp += rewards["exp"]
                user.save()
        return Response("Confirmed")

    @extend_schema(summary="Decline your attendance on meeting", request=None, responses={200: str})
    @action(methods=["post"], detail=True)
    def decline(self, request, *args, **kwargs):
        meeting = self.get_object()
        user = request.user
        attendance = get_object_or_404(Attendance, meeting=meeting, user=user)
        if attendance.confirmed:
            return Response(data="You have already confirmed your attendance", status=status.HTTP_400_BAD_REQUEST)
        return Response(data="You confirmed that you weren't there", status=status.HTTP_200_OK)
