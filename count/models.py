from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    father = models.OneToOneField('self', on_delete=models.CASCADE)


class File(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    new = models.IntegerField(blank=False, null=False, default=0)
    duplicate = models.IntegerField(blank=False, null=False, default=0)
    typo = models.IntegerField(blank=False, null=False, default=0)


class Dict(models.Model):
    word = models.CharField(max_length=255, blank=False, null=False)
    number = models.IntegerField(blank=False, null=False, default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)



