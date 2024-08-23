from datetime import timedelta
from time import sleep

from rest_framework.test import APITestCase, APIClient

from socialapp.users.tests.factories import UserFactory, QuestFactory, DailyQuestFactory


class TestUserViewSet(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_me(self):
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, 200)

    def test_change_username(self):
        response = self.client.patch(f"/api/users/{self.user.id}/", data={"username": "test"})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "test")

    def test_change_username_of_not_yourself(self):
        user2 = UserFactory()
        response = self.client.patch(f"/api/users/{user2.id}/", data={"username": "test"})
        self.assertEqual(response.status_code, 403)

    def test_get_info_of_other_user(self):
        user2 = UserFactory()
        response = self.client.get(f"/api/users/{user2.id}/")
        self.assertEqual(response.status_code, 200)

    def test_claim_daily_coins(self):
        coins_before = self.user.coins
        response = self.client.post("/api/users/redeem_daily_coins/")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, coins_before + 50)

    def test_claim_daily_coins_redeem_second_time(self):
        response = self.client.post("/api/users/redeem_daily_coins/")
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/users/redeem_daily_coins/")
        self.assertEqual(response.status_code, 400)


class TestDailyQuestViewSet(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.quest = QuestFactory(duration=timedelta(minutes=1))
        self.client.force_authenticate(user=self.user)

    def test_choices(self):
        response = self.client.get("/api/quests/choices/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_start_daily_quest(self):
        response = self.client.post("/api/quests/start/", data={"quest": self.quest.id})
        self.assertEqual(response.status_code, 201)

    def test_start_daily_quest_twice(self):
        self.client.post("/api/quests/start/", data={"quest": self.quest.id})
        response = self.client.post("/api/quests/start/", data={"quest": self.quest.id})
        self.assertEqual(response.status_code, 400)

    def test_redeem(self):
        quest2 = QuestFactory(duration=timedelta(seconds=1))
        DailyQuestFactory(quest=quest2, user=self.user)
        sleep(1)
        response = self.client.post("/api/quests/redeem/")
        self.assertEqual(response.status_code, 200)

    def test_redeem_already_redeemed(self):
        DailyQuestFactory(quest=self.quest, user=self.user, redeemed=True)
        response = self.client.post("/api/quests/redeem/")
        self.assertEqual(response.status_code, 400)

    def test_redeem_not_started(self):
        response = self.client.post("/api/quests/redeem/")
        self.assertEqual(response.status_code, 400)

    def test_redeem_during(self):
        self.client.post("/api/quests/start/", data={"quest": self.quest.id})
        response = self.client.post("/api/quests/redeem/")
        self.assertEqual(response.status_code, 400)
