from django.db import models
from django.contrib.auth.models import AbstractUser
from .valirations import validate_national_code

# Create your models here.

class User(AbstractUser):
    REQUIRED_FIELDS = []
    national_id = models.CharField(max_length=10,
                                   unique=True,
                                   null=True,
                                   blank=True,
                                   verbose_name="کد ملی",
                                   validators=[validate_national_code]
                                   )
