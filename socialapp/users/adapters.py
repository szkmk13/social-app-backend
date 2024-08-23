from __future__ import annotations

import typing

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest
    from socialapp.users.models import User


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request: HttpRequest) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def format_email_subject(self, subject):
        return subject

    def send_mail(self, template_prefix, email, context):
        ctx = {"email": email}
        ctx.update(context)
        if settings.PRODUCTION_ENVIRONMENT:
            if backend_reset_url := ctx.get("password_reset_url"):
                backend_reset_url = backend_reset_url.split("/")
                ctx["password_reset_url"] = (
                    settings.FRONTEND_URL + "/" + backend_reset_url[-2] + "/" + backend_reset_url[-1]
                )
        msg = self.render_mail(template_prefix, email, ctx)
        msg.send()

    def get_email_confirmation_url(self, request, emailconfirmation):
        """Constructs the email confirmation (activation) url.

        Note that if you have architected your system such that email
        confirmations are sent outside of the request context `request`
        can be `None` here.
        """

        if settings.PRODUCTION_ENVIRONMENT:
            url = settings.FRONTEND_URL
            return f"{url}/confirm-email/?key={emailconfirmation.key}"
        from allauth.account.internal import flows

        return flows.manage_email.get_email_verification_url(request, emailconfirmation)


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        """
        Populates user information from social provider info.

        See: https://docs.allauth.org/en/latest/socialaccount/advanced.html#creating-and-populating-user-instances
        """
        user = super().populate_user(request, sociallogin, data)
        if not user.name:
            if name := data.get("name"):
                user.name = name
            elif first_name := data.get("first_name"):
                user.name = first_name
                if last_name := data.get("last_name"):
                    user.name += f" {last_name}"
        return user
