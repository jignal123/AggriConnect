from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin

class AbstractModelManager(models.Manager):
    """
    This Class is custom model manager for filtering Abstract Model data
    or overriding built in methods or defining own methods.
    ** Note: Only use the Fields which exists in all the inherited classes in the methods
     or Filters **
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted = False)

class AbstractClassForAll(models.Model):
    """
    This Class Is abstract class for all other classes so whichever fields are common in all classes
    will be added here. 
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    objects = AbstractModelManager() 
    class Meta:
        abstract = True

class Admin(AbstractBaseUser,PermissionsMixin,AbstractClassForAll):
    email = models.EmailField(max_length=150,unique=True)
    address = models.CharField(max_length=255,blank=True,null=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, default="")
    a_photo = models.ImageField(upload_to='admin/',blank=True,null=True)
    USERNAME_FIELD = 'email'