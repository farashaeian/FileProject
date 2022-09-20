from .models import File, Category, Dict, Status
from celery import shared_task
from django.contrib.auth.models import User
from count import custom_methods


# ? does below line useful for shared_task?
# app = Celery(
#     'FileProject',
#     broker='redis://localhost:6379/0',
#     backend='redis://localhost:6379/0'
# )

@shared_task()
def unzip(zip_file_obj_path, user_id):
    try:
        zip_file_obj = File.objects.get(path=zip_file_obj_path)
        user = User.objects.get(id=user_id)
        try:
            custom_methods.extract_zip_file(zip_file_obj, user)
            # save root folder in DB:
            root_folder_name = zip_file_obj.display_name.split('.')[0]
            root_folder_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
                user.id, root_folder_name
            )
            root_folder_obj = Category(
                path=root_folder_path,
                display_name=root_folder_name,
                user=user
            )
            root_folder_obj.save()

            extracted_folder = Category.objects.get(path=root_folder_path)
            folder_list = custom_methods.find_folders(extracted_folder.path)
            file_list = custom_methods.find_files(extracted_folder.path)
            custom_methods.save_folders(folder_list, user)
            custom_methods.save_files(file_list, user)
            # successful_status = Status(user=user, successful=True)
            # successful_status.save()
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
