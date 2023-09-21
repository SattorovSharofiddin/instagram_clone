import random
from datetime import timedelta, datetime

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db.models import CharField, ImageField, EmailField, ForeignKey, CASCADE, DateTimeField, BooleanField

from shared.models import BaseModel

ORDINARY_USER, MANAGER, ADMIN = ('ordinary_user', 'manager', 'admin')
VIA_EMAIL, VIA_PHONE = ('via_email', 'via_phone')
NEW, CODE_VERIFIED, DONE, PHOTO_STEP = ('new', 'code_verified', 'done', 'photo_step')


class User(AbstractUser):
    USER_ROLES = (
        (ORDINARY_USER, ORDINARY_USER),
        (MANAGER, MANAGER),
        (ADMIN, ADMIN),
    )
    AUTH_TYPE_CHOICES = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE),
    )
    AUTH_STATUS = (
        (NEW, NEW),
        (CODE_VERIFIED, CODE_VERIFIED),
        (DONE, DONE),
        (PHOTO_STEP, PHOTO_STEP),
    )
    user_roles = CharField(max_length=31, choices=USER_ROLES, default=ORDINARY_USER)
    auth_type = CharField(max_length=31, choices=AUTH_TYPE_CHOICES)
    auth_status = CharField(max_length=31, choices=AUTH_STATUS, default=NEW)
    email = EmailField(null=True, blank=True, unique=True)
    phone_number = CharField(max_length=13, null=True, blank=True, unique=True)
    photo = ImageField(upload_to='user_photos/', null=True, blank=True,
                       validators=[FileExtensionValidator(['jpg', 'jpeg', 'png', 'heic', 'heif'])])

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def create_verify_code(self, verify_type):
        code = "".join([str(random.randint(0, 10000) % 10) for _ in range(4)])
        UserConfirmation.objects.create(code=code, verify_type=verify_type, user_id=self.id)
        return code


PHONE_EXPIRE = 2
EMAIL_EXPIRE = 5


class UserConfirmation(BaseModel):
    TYPE_CHOICES = (
        (VIA_EMAIL, VIA_EMAIL),
        (VIA_PHONE, VIA_PHONE),
    )
    code = CharField(max_length=4)
    verify_type = CharField(max_length=31, choices=TYPE_CHOICES)
    user = ForeignKey(User, CASCADE, related_name='verify_codes')
    expiration_time = DateTimeField(null=True)
    is_confirmed = BooleanField(default=False)

    def __str__(self):
        return str(self.user.__str__())

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expiration_time = datetime.now() + timedelta(
                minutes=EMAIL_EXPIRE if self.verify_type == VIA_EMAIL else PHONE_EXPIRE)
        super(UserConfirmation, self).save(*args, **kwargs)
