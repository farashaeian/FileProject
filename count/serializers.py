from .models import Dict, File, Category
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from zipfile import is_zipfile, ZipFile, Path
# path.is_dir(self)
import os
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
        # !! move the extraction code to the proper place !!
        with ZipFile(attrs['file'], mode='r', allowZip64=True) as extracted_file:
            current_user_id = self.context.get('request').user.id
            extract_path = 'Documents/uploaded_files/user_{0}/'.format(current_user_id)
            extracted_file.extractall(path=extract_path)
        extracted_file.close()
        return attrs

    def create(self, validated_data):
        folder_list = []
        file_list = []
        current_user_id = self.context.get('request').user.id
        root = 'Documents/uploaded_files/user_{0}/{1}'.format(
            current_user_id,
            validated_data['file']
        )
        for root, dirs, files in os.walk(root):
            for d in dirs:
                folder_list.append(os.path.join(root, d))
            for f in files:
                file_list.append(os.path.join(root, f))
        for f in file_list:
            category_value = re.search("^[/].*[/].*[.]txt$", f)
            current_user = self.context.get('request').user
            # !! change the file field value !!
            file_obj = File(
                file=f,
                user=current_user,
                category=category_value[0]
            )
            file_obj.save()
            return file_obj


"""
    def create(self, validated_data):
        with ZipFile(validated_data['file'], mode='r', allowZip64=True) as extracted_file:
            # extracted_file.extractall()
            extracted_file_items = extracted_file.namelist()
            for item in extracted_file_items:

                if item.endswith('.txt'):
                    file_obj = File(
                        file=validated_data['item']
                    )
                    file_obj.save()
                    return file_obj

                if item.endswith('/'):
                    category_obj = Category(
                        name=validated_data['item']
                    )
                    category_obj.save()
                    return category_obj
        extracted_file.close()"""


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
