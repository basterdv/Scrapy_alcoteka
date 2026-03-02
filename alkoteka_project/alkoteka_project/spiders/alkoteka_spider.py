import time
import os
import re
import scrapy
from scrapy.loader import ItemLoader
from ..items import AlkotekaProjectItem


class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka_spider'
    allowed_domains = ['alkoteka.com']
    city_uuid = '4a70f9e0-46ae-11e7-83ff-00155d026416'
    base_url = 'https://alkoteka.com'

    # Входные данные
    # def _load_start_urls(self):
    #     # Находим путь к папке, где лежит САМ файл паука
    #     spider_dir = os.path.dirname(os.path.abspath(__file__))
    #     # Поднимаемся на 2 уровня вверх к корню проекта
    #     project_root = os.path.dirname(os.path.dirname(spider_dir))
    #     file_path = os.path.join(project_root, 'url_categories.txt')
    #
    #
    #     if not os.path.exists(file_path):
    #         self.logger.error("Файл url_categories.txt не найден!")
    #         return []
    #
    #     with open(file_path, 'r') as f:
    #         content = f.read()
    #         # Регулярка найдет все ссылки, начинающиеся на http
    #         urls = re.findall(r'https?://[^\s,]+', content)
    #         return [url.strip(',') for url in urls]
    def _load_start_urls(self):
        # Берем имя файла из настроек (по умолчанию 'url_categories.txt')
        filename = self.settings.get('URL_LIST_FILE', 'url_categories.txt')

        # Путь к корню проекта
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        file_path = os.path.join(project_root, filename)

        if not os.path.exists(file_path):
            self.logger.warning(f"Файл {filename} не найден. Создаю пустой файл.")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Вставьте ссылки на категории Alkoteka ниже\n")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Ищем только строки, похожие на URL, игнорируя комментарии
            urls = re.findall(r'https?://alkoteka\.com/catalog/[^\s,]+', content)

            clean_urls = []
            for u in urls:
                u = u.strip().rstrip(',')
                # Простейшая валидация: ссылка должна содержать /catalog/
                if '/catalog/' in u:
                    clean_urls.append(u)

            self.logger.info(f"Найдено валидных категорий: {len(clean_urls)}")
            return list(set(clean_urls))  # Убираем дубликаты

    async def start(self):
        urls = self._load_start_urls()

        if not urls:
            self.logger.warning("Список URL пуст, парсинг не начнется.")
            return

        for url in urls:
            # Извлекаем slug категории из URL (последняя часть после /catalog/)
            cat_slug = url.split('/')[-1]
            probe_url = f'{self.base_url}/web-api/v1/product?city_uuid={self.city_uuid}&page=1&per_page=4&root_category_slug={cat_slug}'

            yield scrapy.Request(
                probe_url,
                callback=self.parse_total,
                cb_kwargs={'cat_slug': cat_slug}
            )

    def parse_total(self, response, cat_slug):
        data = response.json()
        total = data.get('meta', {}).get('total')

        # Запрашиваем все товары этой категории одним списком
        full_api_url = f'{self.base_url}/web-api/v1/product?city_uuid={self.city_uuid}&page=1&per_page={total}&root_category_slug={cat_slug}'

        yield scrapy.Request(
            full_api_url,
            callback=self.parse_listing,
        )

    def parse_listing(self, response):
        data = response.json()
        products = data.get('results', [])

        for p in products:
            slug = p.get('slug')
            product_url = p.get('product_url')
            # Запрос в персональное API товара за брендом и описанием
            detail_api_url = f"{self.base_url}/web-api/v1/product/{slug}?city_uuid={self.city_uuid}"
            yield scrapy.Request(
                detail_api_url,
                callback=self.parse_product_detail,
                meta={'product_url': product_url}
            )

    def parse_product_detail(self, response):
        # Данные из детального API
        product_data = response.json()
        if not product_data.get('success'):
            return

        item = product_data.get('results', {})
        blocks = item.get('description_blocks', [])

        product_url = response.meta.get('product_url')

        loader = ItemLoader(item=AlkotekaProjectItem(), response=response)

        # Базовые поля
        loader.add_value('timestamp', int(time.time()))
        loader.add_value('RPC', str(item.get('uuid')))
        loader.add_value('url', product_url)
        loader.add_value(
            'title',
            f'{str(item.get('name'))},{str(item.get('filter_labels')[0]['title'])}'
        )


        # Бренд
        loader.add_value('brand', blocks)

        # Вложенные словари
        curr = float(item.get('price') or 0)
        orig = float(item.get('old_price') or curr)

        loader.add_value('price_data', {
            "current": curr,
            "original": orig,
            "sale_tag": f"Скидка {int((1 - curr / orig) * 100)}%" if orig > curr else ""
        })

        loader.add_value('stock', {
            "in_stock": item.get('available', False),
            "count": item.get('quantity_total', 0)
        })



        # Изображения (полные ссылки)
        main_img = str(item.get('image_url'))
        # set_imgs = [urljoin("https://alkoteka.com", img) for img in item_api.get('images', [])]
        loader.add_value('assets', {
            "main_image": main_img,
            # "set_images": set_imgs or [main_img],
            "view360": [], "video": []
        })

        # Добавляем описание в уже сформированный metadata
        # if 'metadata' in item:
        #     item['metadata']['__description'] = product.get('description', '').strip()

        loader.add_value('variants', 1)

        yield loader.load_item()


