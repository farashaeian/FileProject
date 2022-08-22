from . import models
from celery import shared_task
from zipfile import is_zipfile, ZipFile


def celery_extract_zip_file(zip_file_obj, user):
    with ZipFile(zip_file_obj.file, mode='r', allowZip64=True) as extracted_file:
        current_user_id = user.id
        extract_path = 'Documents/uploaded_files/user_{0}/'.format(current_user_id)
        extracted_file.extractall(path=extract_path)
    extracted_file.close()


@shared_task()
def unzip(zip_file_obj, user):
    celery_extract_zip_file(zip_file_obj, user)


"""
from celery import Celery

app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def add(x, y):
    return x + y
"""