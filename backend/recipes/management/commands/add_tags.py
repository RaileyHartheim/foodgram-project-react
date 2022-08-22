import csv

from django.core.management.base import BaseCommand

from recipes.models import Tag

SUCCESS_MSG = 'Тэги выгружены.'
FAILURE_MSG = 'Выгрузка тэгов прошла неудачно.'


TAGS = [
    ['Завтрак', '#CDDC39', 'breakfast'],
    ['Обед', '#FF9800', 'dinner'],
    ['Ужин', '#FFEB3B', 'supper'],
    ['Супы и бульоны', '#F44336', 'soups'],
    ['Основные блюда', '#3F51B5', 'maindishes'],
    ['Салаты', '#009688', 'salads'],
    ['Закуски', '#9C27B0', 'starters'],
    ['Десерты', '#E91E63', 'desserts'],
    ['Напитки', '#4CAF50', 'drinks'],
    ['Соусы', '#795548', 'sauces']
]


class Command(BaseCommand):
    help = 'Загрузка тэгов'

    def handle(self, *args, **kwargs):
        try:
            with open('data/tags.csv', 'r', encoding='UTF-8') as file:
                for row in csv.reader(file):
                    Tag.objects.get_or_create(
                        name=row[0], color=row[1], slug=row[2]
                    )
            self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
        except Exception:
            self.stdout.write(self.style.ERROR(FAILURE_MSG))
