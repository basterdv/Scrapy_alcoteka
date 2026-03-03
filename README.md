# Alkoteka Scraper 
Скрепер для сбора данных о товарах с сайта **Alkoteka**. Работает через внутреннее API сайта, поддерживает автоматическую ротацию прокси и расчет бизнес-метрик (скидки, форматирование метаданных).

# Структура
````
alkoteka_project/        <-- Корень проекта
├── scrapy.cfg               # Конфиг Scrapy
├── url_categories.txt       # Файл со ссылками
├── proxies.txt              # Файл с прокси
└── alkoteka_project/        # Папка с кодом
    ├── __init__.py
    ├── items.py
    ├── middlewares.py
    ├── pipelines.py
    ├── settings.py
    ├── url_parser.py
    └── spiders/
        ├── __init__.py
        └── alkoteka_spider.py
````

## Основные возможности
- **API-First**: Данные собираются напрямую из JSON-ответов сервера, что быстрее и стабильнее парсинга HTML.
- **Smart Proxy**: Middleware автоматически подгружает список бесплатных прокси через API ProxyScrape и чистит "мертвые" IP в процессе работы.
- **Metadata Processor**: Динамическая сборка всех характеристик товара (Крепость, Объем, Страна и т.д.) в единый словарь.
- **Title Formatting**: Автоматическая склейка названия товара с его характеристиками (цвет/объем).

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com
   cd alkoteka_project
   
2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Для Linux/Mac
   .venv\Scripts\activate     # Для Windows

3. Установите зависимости:
   ```bash   
   pip install scrapy requests
   
## Запуск
   ```bash 
   cd alkoteka_project        
   scrapy crawl alkoteka_spider -O result.json
```

## Структура выходных данных
### Результат сохраняется в формате JSON со следующими полями:
- timestamp: Время сбора (Unix).
- RPC: Уникальный ID товара.
- title: Название (с учетом объема).
- brand: Бренд товара.
- marketing_tags: Список акций и новинок.
- price_data: Объект с ценами (current, original, sale_tag).
- stock: Наличие и количество.
- metadata: Все технические характеристики и описание.