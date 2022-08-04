from django.urls import path
from .views import UserRegister, UploadFile, ShowFolder

urlpatterns = [
    path('user_register/', UserRegister.as_view(), name='user_register'),
    path('upload_file/', UploadFile.as_view(), name='upload_file'),
    path('show_folder/<pk>/', ShowFolder.as_view(), name='show_folder'),
]
