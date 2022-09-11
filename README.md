## Foodgram (продуктовый помощник)
![Foodgram workflow](https://github.com/RaileyHartheim/foodgram-project-react/actions/workflows/foodgram_workflow.yml/badge.svg)
## Описание проекта

Foodgram - сайт, предназначенный для обмена рецептами. Он позволяет:
- публиковать собственные рецепты;
- добавлять рецепты других пользователей в избранное;
- подписываться на других пользователей, чтобы отслеживать их рецепты;
- фильтровать имеющиеся рецепты по тэгам;
- наполнять "Список покупок" рецептами, чтобы выгрузить .pdf-файл со всеми необходимыми ингредиентами для их приготовления.


Бэкенд реализован на Django 3.2.10 и Django REST Framework 3.12.4.


Сайт временно доступен по адресу http://158.160.4.128/recipes

## Установка проекта
Все нижеперечисленные команды указаны для терминала bash
### Алгоритм действий
- Перейти в директорию, в которой будет располагаться папка проекта, и клонировать репозиторий:
```
git clone https://github.com/RaileyHartheim/foodgram-project-react
cd foodgram-project-react/infra/
```
- Создать файл .env в папке infra и заполнить его следующими данными:
```
SECRET_KEY=<секретный ключ для проекта Django>
DB_ENGINE='django.db.backends.postgresql'
DB_NAME=<имя базы данных>
POSTGRES_USER=<имя администратора базы данных>
POSTGRES_PASSWORD=<пароль администратора>
DB_HOST=db
DB_PORT=5432
```
- Собрать контейнеры:
```
sudo docker-compose up -d --build
```
- Выполнить следующие команды:
```
docker-compose exec -T backend python manage.py collectstatic --no-input
docker-compose exec -T backend python manage.py migrate
```
- При необходимости выгрузить ингредиенты и тэги:
```
sudo docker-compose exec -T backend python manage.py add_ingredients
sudo docker-compose exec -T backend python manage.py add_tags
```
- Создать суперпользователя:
```
sudo docker-compose exec backend python manage.py createsuperuser
```

- После завершения работы остановить и удалить контейнеры:
```
sudo docker-compose down -v
```
## Документация к API
Доступна по следующему адресу после запуска сервера (адрес указан для dev-режима)
```
http://127.0.0.1/api/docs/
```
## Над проектом работала
- [Юлия Кажаева](https://github.com/RaileyHartheim)