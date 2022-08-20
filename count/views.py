from .models import Dict, File, Category
from django.contrib.auth.models import User
from .serializers import UserRegisterSerializer, DictListSerializer,\
    ShowFolderSerializer, UploadFileSerializer
from rest_framework import generics, mixins
from . permissions import LoggedInUserPermission
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import os
from zipfile import is_zipfile, ZipFile


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
    queryset = Category.objects.all()
    serializer_class = ShowFolderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Category.objects.filter(user=self.request.user)
        return queryset

    def calculate_folder_info(self, sent_path):
        # content_list = os.listdir(requested_obj.path)
        # text_file_list = [f for f in content_list if f.endswith(".txt")]

        file_list = []
        for root, dirs, files in os.walk(sent_path):
            for f in files:
                file_list.append(os.path.join(root, f))

        analyze = {
            "display_name": "", "father": 0, 'new': 0, 'duplicate': 0, 'typo': 0
        }
        for f in file_list:
            file_obj = File.objects.get(path=f)
            analyze['new'] = analyze['new'] + file_obj.new
            analyze['duplicate'] = analyze['duplicate'] + file_obj.duplicate
            analyze['typo'] = analyze['typo'] + file_obj.typo
        root_obj = Category.objects.get(path=sent_path)
        analyze['display_name'] = root_obj.display_name
        if root_obj.father:
            analyze['father'] = root_obj.father.id
        else:
            analyze['father'] = ""

        return analyze

    def custom_response(self, obj, response_list):
        response_list.append(self.calculate_folder_info(obj.path))
        pre_content_list = os.listdir(obj.path)
        content_list = []
        # pre_content_list contains first level obj content's "names".
        for x in pre_content_list:
            if x.endswith('.txt'):
                content_list.append(File.objects.get(display_name=x, category=obj))
            else:
                content_list.append(Category.objects.get(display_name=x, father=obj))
        # content_list contains first level content's "objects".
        for y in content_list:
            if y.display_name.endswith('.txt'):
                analyze = {
                    "display_name": y.display_name,
                    "category": y.category.id,
                    "new": y.new,
                    "duplicate": y.duplicate,
                    "typo": y.typo
                }
                response_list.append(analyze)
            else:
                self.custom_response(y, response_list)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        response_list = []
        obj = Category.objects.get(id=self.kwargs['pk'])
        self.custom_response(obj, response_list)
        custom_response_data = response_list

        # custom_response_data = serializer.data
        # requested_obj = Category.objects.get(id=self.kwargs['pk'])
        # additional_data = self.calculate_folder_info(requested_obj)
        # custom_response_data['new'] = additional_data['new']
        # custom_response_data['duplicate'] = additional_data['duplicate']
        # custom_response_data['typo'] = additional_data['typo']

        return Response(custom_response_data)


class DictList(generics.ListAPIView):
    serializer_class = DictListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Dict.objects.filter(user=self.request.user).order_by('-number')
        return queryset
        # ? you can put order_by value in model's Meta class ordering field(is it better?)
        # ? in our case above solution can make mistake in our result?


class AllFolders(generics.ListAPIView):
    pass
