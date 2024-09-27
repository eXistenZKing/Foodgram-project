import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Tag

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Loading tags from data in json'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='tags.json', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        path_to_data = os.path.join(DATA_ROOT, options['filename'])

        try:
            with open(path_to_data, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for tag in data:
                    Tag.objects.get_or_create(
                        name=tag["name"],
                        slug=tag["slug"]
                    )
        except FileNotFoundError:
            return (self.stdout.write(
                self.style.ERROR(f'Файл {path_to_data} отсутствует.')))
        except Exception:
            raise Exception(self.stdout.write(self.style.ERROR(
                'Произошла ошибка при загрузке тэгов в БД:')))

        self.stdout.write(
            self.style.SUCCESS('Список тэгов успешно загружен в БД.')
        )
