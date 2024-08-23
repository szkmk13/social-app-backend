from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from socialapp.meetings.models import Meeting
from socialapp.meetings.tests.factories import (
    MeetingWith1UserFactory,
    MeetingFactory,
    PlaceFactory,
    AttendanceFactory,
)
from socialapp.users.tests.factories import UserFactory, QuestFactory, DailyQuestFactory


class TestMeetingModels(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_place_used_in_meeting(self):
        place = PlaceFactory()
        MeetingFactory(place=place)
        self.assertEqual(place.used_in_meetings, 1)
        self.assertEqual(place.__str__(), place.name)

    def test_attendance_str(self):
        meeting = MeetingFactory()
        attendance = AttendanceFactory(user=self.user, meeting=meeting)
        self.assertEqual(attendance.__str__(), f"{self.user} at {meeting}")

    def test_meeting_confirmed_by_user_false(self):
        meeting = MeetingFactory()
        AttendanceFactory(user=self.user, meeting=meeting)
        self.assertEqual(meeting.confirmed_by_user(self.user), False)

    def test_meeting_confirmed_by_user_true(self):
        meeting = MeetingFactory()
        AttendanceFactory(user=self.user, meeting=meeting, confirmed=True)
        self.assertEqual(meeting.confirmed_by_user(self.user), True)

    def test_meeting_confirmed_by_user_not_in_meeting_false(self):
        meeting = MeetingFactory()
        AttendanceFactory(meeting=meeting, confirmed=True)
        self.assertEqual(meeting.confirmed_by_user(self.user), False)
