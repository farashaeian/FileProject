from django.core.management.base import BaseCommand, CommandError
from count.models import Category, File, Dict
from django.contrib.auth.models import User
import os
from spellchecker import SpellChecker
from nltk.tokenize import word_tokenize
from zipfile import ZipFile
from count.serializers import UploadFileSerializer
from django.contrib.auth.hashers import make_password, check_password


class Command(BaseCommand):
    help = 'calculate folder info'

    def add_arguments(self, parser):
        parser.add_argument(
            'user',
            type=int,
            help="directory's owner id"
        )
        parser.add_argument(
            'password',
            type=str,
            help="user's password"
        )
        parser.add_argument(
            'directory',
            type=str,
            help="directory's name is taken then saves the directory's items and calculates text files parameters."
        )

    def extract_zip_file(self, zip_obj, user):
        with ZipFile(zip_obj.file, mode='r', allowZip64=True) as extracted_file:
            extract_path = 'Documents/uploaded_files/user_{0}/'.format(user.id)
            extracted_file.extractall(path=extract_path)
        extracted_file.close()
        # save the folder in DB
        category_obj_name = zip_obj.display_name.split('.')[0]
        category_obj_path = extract_path+'/'+category_obj_name
        category_obj = Category(
            path=category_obj_path,
            display_name=category_obj_name,
            user=user,
        )
        category_obj.save()

    def text_file_tokenize(self, file_path):
        opened_file = open(file_path, 'r')
        text = opened_file.read()
        opened_file.close()
        file_text = word_tokenize(text)
        return file_text

    def analyze_text_file(self, file_path, user):
        file_text = self.text_file_tokenize(file_path)
        analyze = {'new': 0, "duplicate": 0, "typo": 0}
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

    def save_folders(self, folder_list, user):
        for f in folder_list:
            last_slash_index = f.rindex('/')
            folder_father_path = f[:last_slash_index]
            folder_father_obj = Category.objects.get(path=folder_father_path)
            folder_name = f[(last_slash_index+1):]
            folder_obj = Category(
                path=f,
                display_name=folder_name,
                user=user,
                father=folder_father_obj
            )
            folder_obj.save()

    def save_files(self, file_list, user):
        for f in file_list:
            last_slash_index = f.rindex('/')
            file_category_path = f[:last_slash_index]
            file_category = Category.objects.get(path=file_category_path)
            file_name = f[(last_slash_index+1):]
            # analyze = UploadFileSerializer.analyze_text_file(f)
            analyze = self.analyze_text_file(f, user)
            file_obj = File(
                path=f,
                display_name=file_name,
                user=user,
                category=file_category,
                new=analyze['new'],
                duplicate=analyze['duplicate'],
                typo=analyze['typo']
            )
            file_obj.save()

    def be_directory(self, directory, user):
        # check directory existence:
        try:
            directory_obj = Category.objects.get(
                display_name=directory,
                father=None,
                user=user
            )
            directory_path = directory_obj.path
            # Avoid saving existing information:
            condition = Category.objects.filter(father=directory_obj) or File.objects.filter(category=directory_obj)
            if condition:
                raise CommandError("This directory's items has been saved")

            file_list = []
            folder_list = []
            for root, dirs, files in os.walk(directory_path):
                for d in dirs:
                    folder_list.append(os.path.join(root, d))
                for f in files:
                    file_list.append(os.path.join(root, f))

            self.save_folders(folder_list, user)
            self.save_files(file_list, user)
        except Category.DoesNotExist:
            raise CommandError('The category does not exist')

    def handle(self, *args, **kwargs):
        directory = kwargs['directory']
        entry_password = make_password(kwargs['password'])
        # check user existence:
        try:
            user = User.objects.get(id=kwargs['user'])
            if check_password(entry_password, user.password):
                raise CommandError('Th password is wrong')
        except User.DoesNotExist:
            raise CommandError('The user does not exist')
        # check the entry type (zip file or directory):
        if directory.endswith('.zip'):
            # directory contains a zipfile name and it exists in DB
            try:
                zip_obj = File.objects.get(
                    display_name=directory,
                    category=None,
                    user=user
                )
                # directory contains a zipfile name & it exists in DB & has been extracted
                try:
                    directory_obj = Category.objects.get(
                        display_name=directory.split('.')[0],
                        father=None,
                        user=user
                    )
                    self.be_directory(directory_obj.display_name, user)
                # directory contains a zipfile name & it exists in DB but has not been extracted
                except Category.DoesNotExist:
                    self.extract_zip_file(zip_obj, user)
                    directory_obj = Category.objects.get(
                        display_name=directory.split('.')[0],
                        father=None,
                        user=user
                    )
                    self.be_directory(directory_obj.display_name, user)
            except File.DoesNotExist:
                raise CommandError('The zip file does not exist.upload & extract it then call the method')
        else:
            self.be_directory(directory, user)
