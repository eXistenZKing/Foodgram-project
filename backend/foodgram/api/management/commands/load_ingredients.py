import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient

DATA_ROOT = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Loading ingredients from data in json'

    def add_arguments(self, parser):
        parser.add_argument('filename', default='ingredients.json', nargs='?',
                            type=str)

    def handle(self, *args, **options):
        path_to_data = os.path.join(DATA_ROOT, options['filename'])

        try:
            with open(path_to_data, 'r', encoding='utf-8') as f:
                data = json.load(f)
                Ingredient.objects.bulk_create(
                    [
                        Ingredient(
                            name=ingredient['name'],
                            measurement_unit=ingredient[
                                "measurement_unit"]
                        )
                        for ingredient in data
                    ], ignore_conflicts=True
                )
        except FileNotFoundError:
            return (self.stdout.write(
                self.style.ERROR(f'Файл {path_to_data} отсутствует.')))
        except Exception:
            raise Exception(self.stdout.write(self.style.ERROR(
                'Произошла ошибка при загрузке ингредиентов в БД:')))

        self.stdout.write(
            self.style.SUCCESS('Список ингредиентов успешно загружен в БД.')
        )
