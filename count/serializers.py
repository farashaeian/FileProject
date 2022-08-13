from .models import Dict, File, Category
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from zipfile import is_zipfile, ZipFile
import os
from rest_framework import status
from rest_framework.response import Response


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password']
        extra_kwargs = {
            'User.password': {
                'write_only': True
            }
        }

    def validate(self, attrs):
        attrs['password'] = make_password(attrs['password'])
        return attrs


class UploadFileSerializer(serializers.ModelSerializer):
    # def __init__(self, *args, **kwargs):
    #     current_user_id = self.context.get('request').user.id
    #     super().__init__(*args, **kwargs)

    user = serializers.PrimaryKeyRelatedField(
        default=serializers.CurrentUserDefault(),
        queryset=User.objects.all()
    )

    class Meta:
        model = File
        fields = ['file', 'user', 'category']
        read_only_fields = ['category']

    def validate(self, attrs):
        if not is_zipfile(attrs['file']):
            raise serializers.ValidationError("Uploaded File Is Not Zipped!")
        zip_file_name = ZipFile(attrs['file']).filename.split('.')[0]
        duplicate_file_name_condition = Category.objects.filter(display_name=zip_file_name)
        if duplicate_file_name_condition:
            raise serializers.ValidationError("Change The Zip File Name!")
        temporary_extraction = ZipFile(attrs['file'])
        zip_file_items = temporary_extraction.namelist()
        valid_item = True
        for item in zip_file_items:
            validation_condition = (item.endswith('/')) or (item.endswith(".txt"))
            if not validation_condition:
                valid_item = False
        if not valid_item:
            raise serializers.ValidationError("Invalid Items!")
        return attrs

    def extract_zip_file(self):
        with ZipFile(self.context['request'].data['file'], mode='r', allowZip64=True) as extracted_file:
            current_user_id = self.context.get('request').user.id
            extract_path = 'Documents/uploaded_files/user_{0}/'.format(current_user_id)
            extracted_file.extractall(path=extract_path)
        extracted_file.close()

    def find_folders(self):
        folder_list = []
        current_user_id = self.context.get('request').user.id
        root = 'Documents/uploaded_files/user_{0}/{1}'.format(
            current_user_id,
            ZipFile(self.context['request'].data['file']).filename.split('.')[0]

        )
        for root, dirs, files in os.walk(root):
            for d in dirs:
                folder_list.append(os.path.join(root, d))
        return folder_list

    def find_files(self):
        file_list = []
        current_user_id = self.context.get('request').user.id
        root = 'Documents/uploaded_files/user_{0}/{1}'.format(
            current_user_id,
            ZipFile(self.context['request'].data['file']).filename.split('.')[0]
        )
        for root, dirs, files in os.walk(root):
            for f in files:
                file_list.append(os.path.join(root, f))
        return file_list

    def create(self, validated_data):
        # serializer = self.get_serializer(data=self.context['request'].data)
        self.extract_zip_file()
        folder_list = self.find_folders()
        file_list = self.find_files()
        # save zip file
        zip_file_name = ZipFile(self.context['request'].data['file']).filename
        zip_file_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.context.get('request').user.id, zip_file_name
        )
        zip_file_obj = File(
            file=self.context['request'].data['file'],
            path=zip_file_path,
            display_name=zip_file_name,
            user=validated_data['user']
        )
        # zip_file_obj.save()
        # save the root folder
        root_folder_name = zip_file_name.split('.')[0]
        root = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.context.get('request').user.id, root_folder_name
        )
        root_folder_obj = Category(
            path=root,
            display_name=root_folder_name,
            user=validated_data['user']
        )
        root_folder_obj.save()

        for f in folder_list:
            last_slash_index = f.rindex('/')
            folder_father_path = f[:last_slash_index]
            folder_father_obj = Category.objects.get(path=folder_father_path)
            folder_name = f[(last_slash_index+1):]
            folder_obj = Category(
                path=f,
                display_name=folder_name,
                user=validated_data['user'],
                father=folder_father_obj
            )
            folder_obj.save()

        for f in file_list:
            last_slash_index = f.rindex('/')
            file_category_path = f[:last_slash_index]
            file_category = Category.objects.get(path=file_category_path)
            file_name = f[(last_slash_index+1):]
            file_obj = File(
                path=f,
                display_name=file_name,
                user=validated_data['user'],
                category=file_category
            )
            file_obj.save()
        # headers = self.get_success_headers(serializer.data)
        dict_response = {"error": False, "Title": "Success", "ico": "successIcon",
                         "message": "Successfully Be Extracted."}
        return Response(
            dict_response
        )


class ShowFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'


class DictListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dict
        fields = ['word', 'number']


class AllFoldersSerializer(serializers.ModelSerializer):
    pass
