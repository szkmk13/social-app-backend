import json
from datetime import timedelta
from time import sleep

from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from socialapp.meetings.models import Meeting
from socialapp.meetings.tests.factories import PlaceFactory, MeetingFactory, AttendanceFactory
from socialapp.users.tests.factories import UserFactory, QuestFactory, DailyQuestFactory


class TestMeetingsViewset(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.place = PlaceFactory()

    def test_places(self):
        response = self.client.get("/api/meetings/places/")
        self.assertEqual(len(response.data), 1)

    def test_meetings_list_no_meetings(self):
        response = self.client.get("/api/meetings/confirmed/")
        self.assertEqual(len(response.data), 0)

    def test_meetings_list_0_confirmed_meeting(self):
        MeetingFactory()
        response = self.client.get("/api/meetings/confirmed/")
        self.assertEqual(len(response.data), 0)

    def test_meetings_list_1_confirmed_meeting(self):
        MeetingFactory(confirmed_by_majority=True)
        response = self.client.get("/api/meetings/confirmed/")
        self.assertEqual(len(response.data), 1)

    def test_meetings_to_confirm_by_you(self):
        meeting = MeetingFactory()
        AttendanceFactory(user=self.user, meeting=meeting)
        response = self.client.get("/api/meetings/not_confirmed/")
        self.assertEqual(len(response.data), 1)

    def test_meetings_to_confirm_by_others(self):
        meeting = MeetingFactory()
        AttendanceFactory(user=self.user, meeting=meeting, confirmed=True)
        AttendanceFactory(meeting=meeting)
        AttendanceFactory(meeting=meeting)
        response = self.client.get("/api/meetings/not_confirmed/")
        self.assertEqual(len(response.data), 1)

    def test_decline_meeting(self):
        meeting = MeetingFactory()
        AttendanceFactory(user=self.user, meeting=meeting)
        response = self.client.post(f"/api/meetings/{meeting.id}/decline/")
        self.assertEqual(response.status_code, 200)

    def test_decline_meeting_already_confirmed(self):
        meeting = MeetingFactory()
        AttendanceFactory(user=self.user, meeting=meeting, confirmed=True)
        response = self.client.post(f"/api/meetings/{meeting.id}/decline/")
        self.assertEqual(response.status_code, 400)

    def test_decline_meeting_not_there(self):
        meeting = MeetingFactory()
        response = self.client.post(f"/api/meetings/{meeting.id}/decline/")
        self.assertEqual(response.status_code, 404)

    def test_create_meeting(self):
        user1 = UserFactory()
        user2 = UserFactory()
        data = {"place_name": self.place.name, "participants": [user1.id, user2.id, self.user.id]}
        response = self.client.post("/api/meetings/", data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Meeting.objects.count(), 1)
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.coins, 500)

    def test_confirm_attendance(self):
        meeting = MeetingFactory()
        AttendanceFactory(meeting=meeting)
        AttendanceFactory(meeting=meeting)
        AttendanceFactory(meeting=meeting)
        AttendanceFactory(user=self.user, meeting=meeting)

        response = self.client.post(f"/api/meetings/{meeting.id}/confirm/")
        self.assertEqual(response.status_code, 200)

    def test_confirm_attendance_with_threshold(self):
        meeting = MeetingFactory()
        AttendanceFactory(meeting=meeting, confirmed=True)
        AttendanceFactory(meeting=meeting)
        AttendanceFactory(meeting=meeting)
        AttendanceFactory(user=self.user, meeting=meeting)

        response = self.client.post(f"/api/meetings/{meeting.id}/confirm/")
        self.assertEqual(response.status_code, 200)
        meeting.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(meeting.confirmed_by_majority, True)
        self.assertNotEqual(self.user.points, 0)

    def test_confirm_attendance_with_threshold_true(self):
        meeting = MeetingFactory(confirmed_by_majority=True)
        AttendanceFactory(user=self.user, meeting=meeting)
        response = self.client.post(f"/api/meetings/{meeting.id}/confirm/")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(meeting.confirmed_by_majority, True)
        self.assertNotEqual(self.user.coins, 0)

    def test_confirm_attendance_already_confirmed(self):
        meeting = MeetingFactory(confirmed_by_majority=True)
        AttendanceFactory(user=self.user, meeting=meeting, confirmed=True)
        response = self.client.post(f"/api/meetings/{meeting.id}/confirm/")
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, 500)
