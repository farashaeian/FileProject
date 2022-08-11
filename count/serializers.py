from .models import Dict, File, Category
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from zipfile import is_zipfile, ZipFile
import os
# from zipfile import Path
# path.is_dir(self)
import re


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
            (ZipFile(self.context['request'].data['file']).filename).split('.')[0]

        )  # os.path.splitext(self.context['request'].data['file'])[0]
        for root, dirs, files in os.walk(root):
            for d in dirs:
                folder_list.append(os.path.join(root, d))
        return folder_list

    def find_files(self):
        file_list = []
        current_user_id = self.context.get('request').user.id
        root = 'Documents/uploaded_files/user_{0}/{1}'.format(
            current_user_id,
            (ZipFile(self.context['request'].data['file']).filename).split('.')[0]
        )
        for root, dirs, files in os.walk(root):
            for f in files:
                file_list.append(os.path.join(root, f))
        return file_list

    def create(self, validated_data):
        self.extract_zip_file()
        folder_list_obj = []
        file_list_obj = []
        folder_list = self.find_folders()
        file_list = self.find_files()
        # save the root folder
        root = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.context.get('request').user.id,
            (ZipFile(self.context['request'].data['file']).filename).split('.')[0]
        )
        root_folder_obj = Category(
            name=root,
            user=validated_data['user']
        )
        root_folder_obj.save()
        for f in folder_list:
            # !!have to change the name saving for folders!!
            # !!save the single name of folder not the path instead of the name!!
            # !!find solution for name duplication and querying father id!!
            last_slash_index = f.rindex('/')
            folder_father_name = f[:last_slash_index]
            folder_father_obj = Category.objects.filter(name=folder_father_name).last()
            folder_obj = Category(
                name=f,
                user=validated_data['user'],
                father=folder_father_obj
            )
            folder_obj.save()
            folder_list_obj.append(folder_obj)
        folders = [Category(**item) for item in validated_data]
        Category.objects.bulk_create(folders)
        for f in file_list:
            last_slash_index = f.rindex('/')
            file_category_name = f[:last_slash_index]
            file_category = Category.objects.find(name=file_category_name)
            file_obj = File(
                path=f,
                user=validated_data['user'],
                category=file_category
            )
            file_list_obj.append(file_obj)
        files = [File(**item) for item in validated_data]
        return File.objects.bulk_create(files)


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
