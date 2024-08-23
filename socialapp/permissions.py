from rest_framework.permissions import IsAuthenticated, SAFE_METHODS


class IsYouOrReadOnly(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj == request.user
