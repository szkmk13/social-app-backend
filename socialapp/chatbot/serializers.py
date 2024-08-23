from rest_framework import serializers

from socialapp.chatbot.models import Chat


class ChatListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ["id", "created_at"]


class ChatAskSerializer(serializers.Serializer):
    message = serializers.JSONField(
        help_text='json in following format: [{"role":"user","content": "first message '
        'content"}], then you just append with this OBJECT (not list) the '
        "response you get from this endpoint."
    )


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = "__all__"
        read_only_fields = ["user"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        attrs["user"] = self.context["request"].user
        return attrs
