from .models import Dict
from django.contrib.auth.models import User
from .serializers import UserRegisterSerializer, DictListSerializer
from rest_framework import generics


class UserRegister(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer


class ShowFolderS(generics.RetrieveAPIView):
    pass


class DictList(generics.ListAPIView):
    serializer_class = DictListSerializer

    def get_queryset(self):
        queryset = Dict.objects.filter(user=self.request.user.id)


class AllFolders(generics.ListAPIView):
    pass
