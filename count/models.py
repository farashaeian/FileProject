from django.db import models
from django.contrib.auth.models import User
from django_celery_results.models import TaskResult
from django.core.validators import FileExtensionValidator


class Category(models.Model):
    path = models.CharField(max_length=255, blank=False, null=False)
    display_name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_category')
    father = models.ForeignKey('self', on_delete=models.CASCADE, null=True)


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'Documents/uploaded_files/user_{0}/{1}'.format(instance.user.id, filename)


class File(models.Model):
    file = models.FileField(upload_to=user_directory_path)
    # an argument for file field if just zip files will be saved:
    # validators=[FileExtensionValidator(['zip', 'txt'], "Uploaded File Is Not Zipped!")]
    path = models.CharField(max_length=255, null=True)
    display_name = models.CharField(max_length=255, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_file')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)  # nullable for zip
    task_id = models.CharField(max_length=255, null=True)  # nullable for all except of zip
    new = models.IntegerField(default=0)
    duplicate = models.IntegerField(default=0)
    typo = models.IntegerField(default=0)


class Dict(models.Model):
    word = models.CharField(max_length=255, blank=False, null=False)
    number = models.IntegerField(blank=False, null=False, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Status(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=255, null=True)
    status = models.CharField(max_length=50, null=True)
    result = models.TextField(null=True)
    date_done = models.TimeField(null=True)

