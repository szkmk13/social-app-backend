from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from socialapp.chatbot.groq_utils import GroqClient
from socialapp.chatbot.models import Chat
from socialapp.chatbot.serializers import ChatSerializer, ChatListSerializer, ChatAskSerializer


@extend_schema(tags=["chatbot"])
class ChatBotViewSet(viewsets.GenericViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def get_serializer_class(self):
        if self.action == "list":
            return ChatListSerializer
        if self.action in ["ask", "talk"]:
            return ChatAskSerializer

        return ChatSerializer

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)  # type: ignore[misc]

    @extend_schema(summary="Talk to rozpalony")
    @action(detail=False, methods=["POST"])
    def talk(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        chat_messages = serializer.validated_data["message"]
        client = GroqClient()
        response = client.get_completion(chat_messages, username=request.user.username)
        chat_messages.append({"role": "assistant", "content": response})
        return Response(chat_messages)
