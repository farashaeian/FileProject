from django.urls import path
from . import views

urlpatterns = [
    path('user_register/', views.UserRegister.as_view(), name='user_register'),
]
