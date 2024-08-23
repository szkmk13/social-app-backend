import json

from rest_framework import serializers

from socialapp.bingo.models import Bingo, BingoField
from socialapp.utils import DetailException


class BingoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bingo
        fields = ["id", "order", "date", "completed"]


class BingoChangeFieldSerializer(serializers.Serializer):
    field_name = serializers.CharField()

    def validate(self, attrs):
        field_name = attrs.get("field_name")
        field_name = field_name.lower()
        if field_name not in BingoField.objects.values_list("name", flat=True):
            raise DetailException("Field name is not valid")
        if self.context["bingo"].check_field(field_name):
            raise DetailException("You got this field already")
        return attrs
