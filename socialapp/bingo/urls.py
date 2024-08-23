from rest_framework import routers

from socialapp.bingo.views import BingoViewSet

from django.urls import path, include

from socialapp.bingo.views import BingoGetOrCreateAPIView

router = routers.DefaultRouter()
router.register("", BingoViewSet)


urlpatterns = [
    path("bingo/", BingoGetOrCreateAPIView.as_view(), name="bingo"),
    path("bingos/", include(router.urls), name="bingo"),
]
