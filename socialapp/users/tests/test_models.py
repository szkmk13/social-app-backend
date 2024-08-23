from datetime import timedelta
from unittest import TestCase

from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from socialapp.users.tests.factories import UserFactory, QuestFactory, DailyQuestFactory


class TestUserModel(APITestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_quest_string(self):
        quest = QuestFactory()
        self.assertIn(quest.title, quest.__str__())

    def test_user_lvl_up_on_save(self):
        exp_to_lvl_2 = self.user.exp_to_next_level
        self.user.exp = exp_to_lvl_2 + 100
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.level, 2)
        self.assertEqual(self.user.exp, 100)

    def test_user_tokens_redeemed_false(self):
        self.assertEqual(self.user.tokens_redeemed(), False)

    def test_user_tokens_redeemed_true_today(self):
        DailyQuestFactory(user=self.user, redeemed=True)
        self.assertEqual(self.user.tokens_redeemed(), True)

    def test_user_tokens_redeemed_false_yesterday(self):
        DailyQuestFactory(user=self.user, created_at=timezone.now() - timedelta(days=1), redeemed=True)
        self.assertEqual(self.user.tokens_redeemed(), False)

    def test_user_redeem_from_quest(self):
        daily = DailyQuestFactory(user=self.user)
        self.user.redeem_from_quest(daily)
        self.assertEqual(self.user.points, 10)
        self.assertEqual(self.user.coins, 650)
        self.assertEqual(daily.redeemed, True)

    def test_user_redeem_from_attendance(self):
        coins = self.user.coins
        self.user.redeem_from_attendance()
        self.user.refresh_from_db()
        self.assertEqual(self.user.coins, coins + 15)
