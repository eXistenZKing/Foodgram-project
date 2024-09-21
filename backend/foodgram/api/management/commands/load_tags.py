import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from recipes.models import Tag

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Loading tags from data in json'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='tags.json', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        try:
            with open(os.path.join(DATA_ROOT, options['filename']), 'r',
                      encoding='utf-8') as f:
                data = json.load(f)
                for tag in data:
                    try:
                        Tag.objects.create(name=tag["name"],
                                           slug=tag["slug"])
                    except IntegrityError:
                        print(f'Тэг {tag["name"]} '
                              f'{tag["slug"]} '
                              f'уже есть в базе')

        except FileNotFoundError:
            raise CommandError('Файл отсутствует в директории data')
