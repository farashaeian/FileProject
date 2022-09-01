from .models import File, Category, Dict, Status
from celery import shared_task
from zipfile import ZipFile
import os
from nltk.tokenize import word_tokenize
from spellchecker import SpellChecker
from celery import Celery
from django.contrib.auth.models import User


def celery_extract_zip_file(zip_file_obj, user):
    with ZipFile(zip_file_obj.file, mode='r', allowZip64=True) as extracted_file:
        current_user_id = user.id
        extract_path = 'Documents/uploaded_files/user_{0}/'.format(current_user_id)
        extracted_file.extractall(path=extract_path)
    extracted_file.close()


def celery_find_folders(root_folder_path):
    folder_list = []
    for root, dirs, files in os.walk(root_folder_path):
        for d in dirs:
            folder_list.append(os.path.join(root, d))
    return folder_list


def celery_find_files(root_folder_path):
    file_list = []
    for root, dirs, files in os.walk(root_folder_path):
        for f in files:
            file_list.append(os.path.join(root, f))
    return file_list


def celery_text_file_tokenize(file_path):
    opened_file = open(file_path, 'r')
    text = opened_file.read()
    opened_file.close()
    file_text = word_tokenize(text)
    return file_text


def celery_analyze_text_file(file_path, user):
    file_text = celery_text_file_tokenize(file_path)
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


def celery_save_folders(folder_list, user):
    for f in folder_list:
        last_slash_index = f.rindex('/')
        folder_father_path = f[:last_slash_index]
        folder_father_obj = Category.objects.get(path=folder_father_path)
        folder_name = f[(last_slash_index + 1):]
        folder_obj = Category(
            path=f,
            display_name=folder_name,
            user=user,
            father=folder_father_obj
        )
        folder_obj.save()


def celery_save_files(file_list, user):
    for f in file_list:
        last_slash_index = f.rindex('/')
        file_category_path = f[:last_slash_index]
        file_category = Category.objects.get(path=file_category_path)
        file_name = f[(last_slash_index + 1):]
        analyze = celery_analyze_text_file(f, user)
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

# ? is below line correct?
app = Celery(
    'FileProject',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@shared_task()
def unzip(zip_file_obj_path, user_id):
    try:
        zip_file_obj = File.objects.get(path=zip_file_obj_path)
        user = User.objects.get(id=user_id)
        try:
            celery_extract_zip_file(zip_file_obj, user)
            # save root folder in DB:
            root_folder_name = zip_file_obj.displayname.split('.')[0]
            root_folder_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
                user.id, root_folder_name
            )
            root_folder_obj = Category(
                path=root_folder_path,
                display_name=root_folder_name,
                user=user
            )
            root_folder_obj.save()

            folder_list = celery_find_folders(root_folder_path)
            file_list = celery_find_files(root_folder_path)
            celery_save_folders(folder_list, user)
            celery_save_files(file_list, user)
            # successful_status = Status(user=user, successful=True)
            # successful_status.save()
            extracted_folder = Category.objects.get(path=root_folder_path)
            return {"message": "successful Process"}
        except Category.DoesNotExist:
            # unsuccessful_status = Status(user=user)
            # unsuccessful_status.save()
            zip_file_obj.delete()
            return {"message": "Unsuccessful Process"}
    except File.DoesNotExist:
        return {"message": "The Zip File Is Not Available!"}

"""
app = Celery('FileProject', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')


@app.task
def unzip(zip_file_obj, user):
    celery_extract_zip_file(zip_file_obj, user)
"""
