from django.contrib import admin
from django.utils.html import format_html

from socialapp.chatbot.models import Chat


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "chat_history")

    def chat_history(self, obj):
        context = obj.context
        if not context:
            return "No chat history"
        result = ""
        for msg in context:
            result += f"<p>{msg['content']}</p>"
        return format_html(result)
