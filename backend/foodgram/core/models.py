from django.contrib.auth.models import AbstractUser
from django.core.validators import validate_email
from django.db import models

from .constants import CustomUserLimits


class CustomUser(AbstractUser):
    """Кастомная модель пользователя"""
    username = models.CharField(
        unique=True,
        db_index=True,
        max_length=CustomUserLimits.MAX_LEN_NAME,
        verbose_name='Логин',
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
        db_index=True,
        max_length=CustomUserLimits.MAX_LEN_EMAIL,
        verbose_name='Электронная почта',
        validators=[validate_email,]
    )
    is_subscribed = models.BooleanField(
        default=False,
        verbose_name='Подписка на автора',
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
        return self.first_name
