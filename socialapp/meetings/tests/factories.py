import factory
from factory import Faker, SubFactory
from factory.django import DjangoModelFactory

from socialapp.meetings.models import Meeting, Attendance, Place
from socialapp.users.models import User, Quest, DailyQuest
from socialapp.users.tests.factories import UserFactory


class PlaceFactory(DjangoModelFactory):
    name = Faker("name")

    class Meta:
        model = Place


class MeetingFactory(DjangoModelFactory):
    date = Faker("date")
    place = SubFactory(PlaceFactory)

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if not create or not extracted:
            # Simple build, or nothing to add, do nothing.
            return

        # Add the iterable of groups using bulk addition
        self.users.add(*extracted)

    class Meta:
        model = Meeting


class AttendanceFactory(DjangoModelFactory):
    user = SubFactory(UserFactory)
    meeting = SubFactory(MeetingFactory)

    class Meta:
        model = Attendance


class MeetingWith1UserFactory(UserFactory):
    att = factory.RelatedFactory(
        AttendanceFactory,
        factory_related_name="user",
    )
