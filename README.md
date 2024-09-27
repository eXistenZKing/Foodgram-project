# Проект Фудграм
Фудграм — проект, цель которого дать возможность пользователям создавать и хранить рецепты на онлайн-платформе. Кроме того, можно скачать список продуктов, необходимых для приготовления блюда, просмотреть рецепты друзей и добавить любимые рецепты в список избранных.

## 1. Настройка
### 1.1 Репозиторий

Проект имеет следующую структуру:
- `backend` - папка для кода Backend приложения (Django)
- `docs` - папка со спецификациями API
- `frontend` - папка для кода Frontend приложения
- `infra` - папка для настроек приложений и файлов развертывания инфраструктуры для локальной отладки
- `nginx` - папка с конфигурациями nginx
- `postman_collection` - папка с коллекцией postman
- `docker-compose.production.yml` - настройки для развёртывания приложения для продакшена
- `setup.cfg` - настройки для `flake8` и `isort`

### 1.2 Настройка после клонирования репозитория

После клонирования репозитория устанавливаем и настраиваем виртуальное окружение:

<details>
<summary>
Виртуальное окружение для backend
</summary>

1. Переходим в папку `/backend/foodgram`
2. Устанавливаем и активируем виртуальное окружение
    - Для linux/mac:
      ```shell
      python3.11 -m venv venv
      source .venv/bin/activate
      ```
    - Для Windows:
      ```shell
      python -m venv venv
      source venv\Scripts\activate
      ```
    В начале командной строки должно появиться название виртуальног окружения `(venv)`
3. Обновляем менеджер пакетов `pip` (по желанию)
    ```shell
    python -m pip install --upgrade pip
    ```
4. Устанавливаем зависимости
    ```shell
    pip install -r requirements.txt
    ```
</details>

## 2. Запуск приложения локально.

1. Создать `.env` на основе `infra/.env.example` Указав валидные данные для подключения.

      ```ini
      SECRET_KEY=django-secret-key
      DEBUG=True
      POSTGRES_USER=foodgram_user
      POSTGRES_PASSWORD=foodgram_password
      POSTGRES_DB=foodgram
      DB_HOST=db
      DB_PORT=5432
      ALLOWED_HOSTS=example.com 127.0.0.1 localhost
      BASE_URL=https://example.com

      ```
2. В настройках Django приложения `setting.py` закоментировать настройки для БД на основе PostgreSQL и раскоментировать настройки для SQLite, при необходимости. Или закоментировать в docker compose контейнер с db.
3. Находясь в папке `infra` выполните команду `docker compose up`.
4. По адресу http://localhost будет доступен проект, а по адресу http://localhost/api/docs/ — спецификацию API.

