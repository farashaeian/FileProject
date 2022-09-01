from .models import Dict, File, Category
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from zipfile import is_zipfile, ZipFile
import os
from rest_framework import status
from rest_framework.response import Response
from nltk.tokenize import word_tokenize
from spellchecker import SpellChecker
from .tasks import unzip


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
        # !!! It is important that give the zip file name from the
        # uploaded zip file not the extracted folder. !!!
        zip_file_name = ZipFile(attrs['file']).filename
        duplicate_file_name_condition = File.objects.filter(
            display_name=zip_file_name,
            user=self.context.get('request').user
        )
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
        root_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            current_user_id,
            ZipFile(self.context['request'].data['file']).filename.split('.')[0]
        )
        for root, dirs, files in os.walk(root_path):
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

    def text_file_tokenize(self, file_path):
        opened_file = open(file_path, 'r')
        text = opened_file.read()
        opened_file.close()
        file_text = word_tokenize(text)
        return file_text

    def analyze_text_file(self, file_path):
        file_text = self.text_file_tokenize(file_path)
        analyze = {'new': 0, "duplicate": 0, "typo": 0}
        user = self.context.get('request').user
        for word in file_text:
            is_typo = SpellChecker().unknown([word])
            try:
                word_in_Dict = Dict.objects.get(word=word, user=user)
            except Dict.DoesNotExist:
                word_in_Dict = None
            if is_typo:
                # increase typo number in the file
                analyze['typo'] += 1
            elif word_in_Dict:
                # increase word number in the user dictionary
                new_word_number = word_in_Dict.number + 1
                word_in_Dict.number = new_word_number
                word_in_Dict.save()
                # increase word duplication in the file
                analyze['duplicate'] += 1
            else:
                # add new word to the user Dictionary
                new_word = Dict(
                    word=word,
                    number=1,
                    user=user
                )
                new_word.save()
                # increase new word number in the file
                analyze['new'] += 1
        return analyze

    def save_folders(self, folder_list):
        for f in folder_list:
            last_slash_index = f.rindex('/')
            folder_father_path = f[:last_slash_index]
            folder_father_obj = Category.objects.get(path=folder_father_path)
            folder_name = f[(last_slash_index+1):]
            folder_obj = Category(
                path=f,
                display_name=folder_name,
                user=self.context.get('request').user,
                father=folder_father_obj
            )
            folder_obj.save()

    def save_files(self, file_list):
        for f in file_list:
            last_slash_index = f.rindex('/')
            file_category_path = f[:last_slash_index]
            file_category = Category.objects.get(path=file_category_path)
            file_name = f[(last_slash_index+1):]
            analyze = self.analyze_text_file(f)
            file_obj = File(
                path=f,
                display_name=file_name,
                user=self.context.get('request').user,
                category=file_category,
                new=analyze['new'],
                duplicate=analyze['duplicate'],
                typo=analyze['typo']
            )
            file_obj.save()

    def create(self, validated_data):
        self.extract_zip_file()
        folder_list = self.find_folders()
        file_list = self.find_files()

        # save zip file
        # !!! It is important that give the zip file name from the
        # uploaded zip file not the extracted folder. !!!
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
        zip_file_obj.save()

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

        self.save_folders(folder_list)

        self.save_files(file_list)

        return Response(
            {"message": "Successfully Be Extracted."},
            status=status.HTTP_201_CREATED
        )

    def to_representation(self, instance):
        return {"message": "Successfully Be Extracted."}


class ShowFolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['display_name', 'father']


class DictListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dict
        fields = ['word', 'number']


class CeleryUploadFileSerializer(serializers.ModelSerializer):
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
        # !!! It is important that give the zip file name from the
        # uploaded zip file not the extracted folder. !!!
        zip_file_name = ZipFile(attrs['file']).filename
        duplicate_file_name_condition = File.objects.filter(
            display_name=zip_file_name,
            user=self.context.get('request').user
        )
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

    def create(self, validated_data):
        user = self.context.get('request').user
        zip_file = self.context['request'].data['file']
        # save zip file in DB:
        zip_file_name = ZipFile(zip_file).filename
        zip_file_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            user.id, zip_file_name
        )
        zipfile_obj = File(
            file=zip_file,
            path=zip_file_path,
            display_name=zip_file_name,
            user=user
        )
        zipfile_obj.save()
        # call celery.task:
        zip_file_obj = File.objects.get(path=zip_file_path)
        message = 0
        try:
            message = unzip.delay(zip_file_obj.path, user.id)
            return Response(status=status.HTTP_201_CREATED)
        except message == 0:
            zip_file_obj.delete()
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def to_representation(self, instance):
        try:
            user = self.context.get('request').user
            zip_file = self.context['request'].data['file']
            zip_file_name = ZipFile(zip_file).filename
            zip_file_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
                user.id, zip_file_name
            )
            zip_file_obj = File.objects.get(path=zip_file_path)
            return {"message": "The File Was Received."}
        except File.DoesNotExist:
            return {"message": "The File Was  Not Received!"}


class AllFoldersSerializer(serializers.ModelSerializer):
    pass
