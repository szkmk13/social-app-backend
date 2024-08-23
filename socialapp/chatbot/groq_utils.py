import groq
from django.conf import settings


def get_content_and_rules(username) -> str:
    return f"""
[Context]
You are a member of socialapp web application, its purpose is to connect together, via meetings, bets and quests.
Also there is casino in the application with 2 games: high card and roulette.
Occasionally use emoticons, like: 👀, 💪, ☠.
You are talking with {username}


[Rules]
1. Your answers are cool. They consist of 2 sentences.
2. Be sarcastic when appropriate.
"""


class GroqClient:
    def __init__(self, *args, **kwargs):
        self.client = groq.Groq(api_key=settings.GROQ_API_KEY)

    def get_completion(self, chat_messages: list, username: str):
        system_message = {"role": "system", "content": get_content_and_rules(username)}
        completion = self.client.chat.completions.create(
            model="llama3-70b-8192", messages=[system_message] + chat_messages
        )
        message_content = completion.choices[0].message.content
        return message_content
