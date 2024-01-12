from django.db import models
from django.contrib.auth.models import AbstractBaseUser,BaseUserManager
import uuid

# Create your models here.



class MyAccountManager(BaseUserManager):
  def create_user(self,first_name,last_name,email,phone_number,password=None):
    if not email:
      raise ValueError('user must have an email address')
    
    
    user=self.model(
      email=self.normalize_email(email),
      phone_number=phone_number,
      first_name=first_name,
      last_name=last_name,
    )
    user.set_password(password)
    user.save(using=self._db)
    return user

  def create_superuser(self,first_name,last_name,email,username,password):
   user=self.create_user(
    email=self.normalize_email(email),
    username=username,
    password=password,
    first_name=first_name,
    last_name=last_name,
  )

   user.is_admin=True
   user.is_active=True
   user.is_staff=True
   user.is_superadmin=True
   user.save(using=self._db)
   return user

class UserAccountManager(BaseUserManager):
    def create_user_account(self, first_name,last_name, email, phone_number, password=None):
        if not email:
            raise ValueError('User must have an email address')
        if not phone_number:
            raise ValueError('User must have a phone number')

        user = self.model(
            email = self.normalize_email(email),
            first_name = first_name,
            last_name=last_name,

            phone_number = phone_number
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
class Account(AbstractBaseUser):
  first_name = models.CharField(max_length=50)
  last_name = models.CharField(max_length=50)
  username = models.CharField(max_length=50)
  email=models.EmailField(max_length=100,unique=True)
  phone_number=models.CharField(max_length=50)
  
  #required
  date_joined=models.DateTimeField(auto_now_add=True)
  last_login=models.DateTimeField(auto_now_add=True)
  is_admin=models.BooleanField(default=False)
  is_staff=models.BooleanField(default=False)
  is_active=models.BooleanField(default=False)
  is_superadmin=models.BooleanField(default=False)

  USERNAME_FIELD='email'
  REQUIRED_FIELDS=['phone_number','first_name','last_name']
  

  objects=MyAccountManager()

  def __str__(self):
    return self.email
  
  def has_perm(self,perm,obj=None):
    return self.is_admin
  
  def has_module_perms(self,add_label):
    return True
  

class AccountUser(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
   
    email=models.EmailField(max_length=100,unique=True)
    phone_number=models.CharField(max_length=50)
    session = models.CharField(max_length=255, blank=True, null=True)

    #     Required
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number', 'password']

    objects = UserAccountManager()

    class Meta:
        verbose_name = 'user account'
        verbose_name_plural = 'user accounts'

    def __str__(self):
        return self.first_name


class Profile(models.Model):
    user = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='profile')
  
    otp = models.CharField(max_length=100, null=True, blank=True)
    uid = models.CharField(default=f'{uuid.uuid4}',max_length=200)