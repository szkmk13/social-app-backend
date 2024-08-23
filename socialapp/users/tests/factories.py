from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from socialapp.users.models import User, Quest, DailyQuest


class UserFactory(DjangoModelFactory):
    username = Faker("user_name")

    class Meta:
        model = User


class QuestFactory(DjangoModelFactory):
    title = Faker("sentence")
    description = Faker("paragraph")
    duration = Faker("time_delta")

    class Meta:
        model = Quest


class DailyQuestFactory(DjangoModelFactory):
    quest = SubFactory(QuestFactory)
    user = SubFactory(UserFactory)

    class Meta:
        model = DailyQuest
