from django.urls import path
from .views import UserRegister, UploadFile, ShowFolder, DictList, CeleryUploadFile, UpdateTaskStatus

urlpatterns = [
    path('user_register/', UserRegister.as_view(), name='user_register'),
    path('upload_file/', UploadFile.as_view(), name='upload_file'),
    path('show_folder/<pk>/', ShowFolder.as_view(), name='show_folder'),
    path('my_dict/', DictList.as_view(), name='my_dict'),
    path('celery_upload_file/', CeleryUploadFile.as_view(), name='celery_upload_file'),
    path('update_task_status/', UpdateTaskStatus.as_view(), name='update_task_status'),
]
