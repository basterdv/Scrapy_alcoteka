import time

import scrapy
from scrapy.loader import ItemLoader

from ..items import AlkotekaProjectItem
from ..url_parser import AlkotekaUrlMapper


class AlkotekaSpider(scrapy.Spider):
    name = 'alkoteka_spider'
    allowed_domains = ['alkoteka.com']

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
            product_api_url = AlkotekaUrlMapper.get_detail_api_url(slug)

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

        item_api  = product_data.get('results', {})
        description_blocks = item_api.get('description_blocks', [])

        product_url = response.meta.get('product_url')

        loader = ItemLoader(item=AlkotekaProjectItem(), response=response)
        loader.context['filter_labels'] = item_api.get('filter_labels', [])

        loader.add_value('timestamp', True)
        loader.add_value('RPC', str(item_api.get('uuid')))
        loader.add_value('url', product_url)
        loader.add_value('title', item_api.get('name'))

        # name = item_api.get('name', '')
        # # Ищем объем или цвет в метках для добавления в заголовок
        # extra_meta = ""
        # for label in item_api.get('filter_labels', []):
        #     if label.get('filter') in ['obem', 'cvet']:
        #         extra_meta = label.get('title', '')
        #         break
        #
        # full_title = f"{name}, {extra_meta}".strip(', ')
        # loader.add_value('title', full_title)

        tags = []
        if item_api.get('new'): tags.append('Новинка')
        if item_api.get('enogram'): tags.append('Энограмма')
        # Добавляем акции из price_details
        price_details = item_api.get('price_details') or []

        for detail in price_details:
            if isinstance(detail, dict):
                tag_text = detail.get('title')
                if tag_text:
                    tags.append(tag_text)

        loader.add_value('marketing_tags', list(set(tags)))

        loader.item['brand'] = ""
        loader.add_value('brand', description_blocks)

        sections = []
        category_data = item_api.get('category', {})
        if category_data.get('parent'):
            sections.append(category_data['parent'].get('name'))
        if category_data.get('name'):
            sections.append(category_data.get('name'))
        loader.add_value('section', sections)

        original = float(item_api.get('prev_price') or float(item_api.get('price')))
        current = float(item_api.get('price') or original)

        loader.add_value('price_data', {
            "current": current,
            "original": original,
            "sale_tag": f"Скидка {
            int((1 - current / original) * 100)}%" if original > current else ""
        })

        loader.add_value('stock', {
            "in_stock": item_api.get('available', False),
            "count": item_api.get('quantity_total', 0)
        })

        main_img = str(item_api.get('image_url'))

        loader.add_value('assets', {
            "main_image": main_img,
            "set_images": [item_api.get('image_url')],
            "view360": [],
            "video": []
        })

        metadata = {}
        # Извлекаем описание из text_blocks
        desc_list = [b.get('content', '') for b in item_api.get('text_blocks', []) if b.get('title') == 'Описание']
        metadata['__description'] = desc_list[0].replace('<br>\n', ' ').strip() if desc_list else ""

        for block in description_blocks:
            key = block.get('title')
            if not key: continue

            # Для типа select вытягиваем имена из списка values
            if block.get('type') == 'select':
                vals = [str(v.get('name')) for v in block.get('values', []) if v.get('name')]
                val_str = ", ".join(vals)
            # Для типа range (Объем, Крепость) берем число + единицу измерения
            else:
                v_min = block.get('min')
                unit = block.get('unit', '')
                val_str = f"{v_min}{unit}".strip() if v_min is not None else ""

            if val_str:
                metadata[key] = val_str

        loader.add_value('metadata', metadata)

        loader.add_value('variants', 1)

        yield loader.load_item()
