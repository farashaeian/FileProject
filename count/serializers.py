from .models import Dict, File
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from zipfile import is_zipfile, ZipFile, Path


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
    class Meta:
        model = File
        fields = ['file']

    def validate(self, attrs):
        if not is_zipfile(attrs['file']):
            raise serializers.ValidationError("Uploaded File Is Not Zipped!")
        temporary_extraction = ZipFile(attrs['file'].name)
        zip_file_items = temporary_extraction.namelist()
        valid_item = True
        for item in zip_file_items:
            validation_condition = item is Path.is_dir() or item.endswith("*.txt")
            if not validation_condition:
                valid_item = False
        if not valid_item:
            raise serializers.ValidationError("Uploaded File Is Not Zipped!")
        return attrs


class ShowFolderSerializer(serializers.ModelSerializer):
    pass


class DictListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dict
        fields = ['word', 'number']


class AllFoldersSerializer(serializers.ModelSerializer):
    pass
