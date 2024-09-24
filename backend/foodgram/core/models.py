from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.core.validators import EmailValidator, RegexValidator
from django.db import models

from .constants import CustomUserLimits


class CustomUser(AbstractUser, PermissionsMixin):
    """Кастомная модель пользователя"""
    username = models.CharField(
        unique=True,
        db_index=True,
        max_length=CustomUserLimits.MAX_LEN_NAME,
        verbose_name='Логин',
        validators=[RegexValidator(
            regex=r'^[\w.@+-]+\Z',
            message='Имя пользователя содержит недопустимые символы.'),
        ],
    )
    password = models.CharField(
        max_length=255,
        verbose_name='Пароль',
    )
    first_name = models.CharField(
        max_length=CustomUserLimits.MAX_LEN_NAME,
        verbose_name='Имя пользователя',
    )
    last_name = models.CharField(
        max_length=CustomUserLimits.MAX_LEN_NAME,
        verbose_name='Фамилия',
    )
    email = models.EmailField(
        unique=True,
        max_length=CustomUserLimits.MAX_LEN_EMAIL,
        verbose_name='Электронная почта',
        validators=[EmailValidator,]
    )
    avatar = models.ImageField(
        upload_to='users/images/',
        blank=True,
        null=True,
        default=None,
        verbose_name='Аватар'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [first_name, last_name, username, email, password]

    class Meta:
        ordering = ('id',)
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
