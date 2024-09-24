import os

from django.core.management.base import BaseCommand
from core.models import CustomUser as User


class Command(BaseCommand):
    help = 'Create a superuser'

    def handle(self, *args, **options):
        User.objects.create_superuser(
            first_name='Дмитрий',
            last_name='Admin',
            username='foodgram_admin',
            email='foodgram_admin@gmail.com',
            password=os.getenv('SUPERUSER_PASS', ''),
            is_staff=True,
            is_superuser=True
        )
