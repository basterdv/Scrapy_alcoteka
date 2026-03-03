import time

import scrapy
from scrapy.loader import ItemLoader

from ..items import AlkotekaProjectItem
from ..url_parser import AlkotekaUrlMapper


class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka_spider'
    allowed_domains = ['alkoteka.com']
    city_uuid = '4a70f9e0-46ae-11e7-83ff-00155d026416'
    base_url = 'https://alkoteka.com'

    async def start(self):
        # Берем имя файла из настроек (по умолчанию 'url_categories.txt')
        filename = self.settings.get('URL_LIST_FILE', 'url_categories.txt')

        api_urls = AlkotekaUrlMapper.load_urls_from_file(filename)

        if not api_urls:
            self.logger.warning("Список URL пуст, парсинг не начнется.")
            return

        for api_url in api_urls:
            yield scrapy.Request(
                api_url,
                callback=self.parse_total,
                cb_kwargs={'api_url': api_url}
            )

    def parse_total(self, response, api_url):
        data = response.json()
        total = data.get('meta', {}).get('total')

        # Запрашиваем все товары этой категории одним списком
        category, full_api_url = AlkotekaUrlMapper.update_api_params(api_url, per_page=total)
        self.logger.info(f"Категория {category} содержит {total} товаров")

        # Переходим на страницу с товарами
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
            product_api_url = AlkotekaUrlMapper.get_detail_api_url(slug, self.city_uuid)

            yield scrapy.Request(
                product_api_url,
                callback=self.parse_product_detail,
                meta={'product_url': product_url}
            )

    def parse_product_detail(self, response):
        # Данные из детального API
        product_data = response.json()
        if not product_data.get('success'):
            self.logger.warning(f"Не удалось получить данные товара, ошибка: {product_data.get('error')}")
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
            f"{str(item.get('name'))},{str(item.get('filter_labels')[0]['title'])}"
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
