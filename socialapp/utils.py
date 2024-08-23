from rest_framework import status
from rest_framework.exceptions import APIException


class DetailException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "A server error occurred."

    def __init__(self, detail, field="detail", status_code=status.HTTP_400_BAD_REQUEST):
        if status_code is None:
            self.status_code = status.HTTP_400_BAD_REQUEST
        if detail is not None:
            self.detail = {field: detail}
        else:
            self.detail = {"detail": self.default_detail}
