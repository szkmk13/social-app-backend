from dj_rest_auth.registration.views import RegisterView, ResendEmailVerificationView
from dj_rest_auth.views import PasswordChangeView, PasswordResetConfirmView, PasswordResetView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularSwaggerView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from socialapp.users.views import SocialappConfirmEmailView

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    # API AUTH
    path("api/", include("config.api_router")),
    path("api/auth/register/", RegisterView.as_view(), name="rest_register"),
    # path('api/auth/verify-email/', VerifyEmailView.as_view(), name='rest_verify_email'),
    path("api/auth/resend-email/", ResendEmailVerificationView.as_view(), name="rest_resend_email"),
    path(
        "api/auth/account-confirm-email/<str:key>/",
        SocialappConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),
    path(
        "account-email-verification-sent/",
        TemplateView.as_view(),
        name="account_email_verification_sent",
    ),
    # PASSWORD RESET
    path(
        "api/auth/password/reset/confirm/<int:id>/<str:key>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("api/auth/password/change/", PasswordChangeView.as_view(), name="rest_password_change"),
    path("api/auth/password/reset/", PasswordResetView.as_view(), name="rest_password_reset"),
    # TOKEN
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # DOCS
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    # STATICS
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
