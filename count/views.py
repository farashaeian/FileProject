from .models import Dict, File
from django.contrib.auth.models import User
from .serializers import UserRegisterSerializer, DictListSerializer,\
    ShowFolderSerializer, UploadFileSerializer
from rest_framework import generics
from . permissions import LoggedInUserPermission
from rest_framework.permissions import IsAuthenticated


class UserRegister(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer


class UploadFile(generics.CreateAPIView):
    queryset = File.objects.all()
    serializer_class = UploadFileSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super(UploadFile, self).get_serializer_context()
        context.update({"request": self.request})
        return context


class ShowFolder(generics.RetrieveAPIView):
    """"correct this API"""
    # queryset = File.objects.all()
    serializer_class = ShowFolderSerializer
    # permission_classes = [LoggedInUserPermission]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = File.objects.filter(user=self.request.user.id)
        return queryset


class DictList(generics.ListAPIView):
    serializer_class = DictListSerializer

    def get_queryset(self):
        queryset = Dict.objects.filter(user=self.request.user.id).order_by('-number')
        return queryset
        # ? you can put order_by value in model's Meta class ordering field(is it better?)
        # ? in our case above solution can make mistake in our result?


class AllFolders(generics.ListAPIView):
    pass
