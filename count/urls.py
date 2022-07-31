from django.urls import path
from .views import UserRegister, UploadFile

urlpatterns = [
    path('user_register/', UserRegister.as_view(), name='user_register'),
    path('upload_file/', UploadFile.as_view(), name='upload_file'),
]
