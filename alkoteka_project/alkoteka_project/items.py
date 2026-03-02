import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Identity


def process_metadata(blocks_list):
    """
    Выходной процессор.
    blocks_list придет как [ [block1, block2, ...] ] из-за loader.add_value('metadata', [blocks])
    """
    if not blocks_list or not isinstance(blocks_list[0], list):
        return {}

    blocks = blocks_list[0]
    metadata = {}

    for block in blocks:
        key = block.get('title')
        block_type = block.get('type')
        val = ""

        # Логика извлечения значения (как мы делали ранее)
        if block_type == 'select':
            v = block.get('values', {})
            val = v.get('name', '') if isinstance(v, dict) else ""
        elif block_type == 'range':
            val = f"{block.get('min')}{block.get('unit', '')}"

        if key and val:
            metadata[key] = val

    return metadata


def extract_brand(block):
    """Ищет бренд в массиве блоков"""
    if not isinstance(block, dict):
        return None

    if block.get('code') == 'brend':
        vals = block.get('values', {})
        if isinstance(vals, dict):
            return vals.get('name')
        elif isinstance(vals, list) and len(vals) > 0:
            return vals[0].get('name')
    return None  # Если это не блок бренда, возвращаем None (Scrapy его отфильтрует)


# def format_image_url(url):
#     return urljoin("https://alkoteka.com", url) if url else None

class AlkotekaProjectItem(scrapy.Item):
    timestamp = scrapy.Field(output_processor=TakeFirst())  # Дата и время сбора товара в формате timestamp.
    RPC = scrapy.Field(output_processor=TakeFirst())  # Уникальный код товара.
    url = scrapy.Field(output_processor=TakeFirst())  # Ссылка на страницу товара.
    title = scrapy.Field(output_processor=TakeFirst())  # Заголовок/название товара
    marketing_tags = scrapy.Field()  # Список маркетинговых тэгов
    brand = scrapy.Field(
        input_processor=MapCompose(extract_brand),
        output_processor=TakeFirst())
    section = scrapy.Field()
    price_data = scrapy.Field(output_processor=TakeFirst())
    stock = scrapy.Field(output_processor=TakeFirst()) # Есть товар в наличии в магазине или нет
    # Если есть возможность получить информацию о количестве оставшегося товара в наличии, иначе 0
    assets = scrapy.Field(output_processor=TakeFirst()) # Ссылка на основное изображение товара.
    metadata = scrapy.Field(
        input_processor=Identity(),  # Передаем список блоков как есть
        output_processor=process_metadata  # Превращаем список в словарь характеристик
    )
    variants = scrapy.Field(output_processor=TakeFirst()) # Кол-во вариантов у товара в карточке

    # yield {
    #     'timestamp': int(time.time()),  # Дата и время сбора товара в формате timestamp.
    #     'RPC': str(item.get('uuid')),  # Уникальный код товара.
    #     'url': product_url,  # Ссылка на страницу товара.
    #     'title':  f'{str(item.get('name'))},{str(item.get('filter_labels')[0]['title'])}', # Заголовок/название товара
    #     'marketing_tags': [],  # Список маркетинговых тэгов
    #     'brand': str(item.get('description_blocks')[2]['values'][0]['name']),  # Бренд товара
    #     'section': [  # Иерархия разделов
    #         item.get('category')['parent']['name'],
    #         item.get('category')['name']
    #     ],
    #     'price_data': {
    #         # 'current': float(product.get('price')),       # Цена со скидкой, если скидки нет то = original.
    #         # "original": float(product.get('prev_price')), # Оригинальная цена
    #         "sale_tag": 'sale_tag'  # Если есть скидка на товар то необходимо вычислить
    #         # процент скидки и записать формате:
    #         # "Скидка {discount_percentage}%"
    #     },
    #     "stock": {
    #         # "in_stock": bool((product.get('available'))),  # Есть товар в наличии в магазине или нет
    #         # "count": (product.get('quantity_total', 0))
    #         # Если есть возможность получить информацию о количестве оставшегося товара в наличии, иначе 0
    #     },
    #     "assets": {
    #         # "main_image": str(product.get('image_url')),  # Ссылка на основное изображение товара.
    #         "set_images": [],  # Список ссылок на все изображения товара
    #         "view360": [],  # Список ссылок на изображения в формате 360.
    #         "video": []  # Список ссылок на видео/видеообложки товара.
    #     },
    #     'metadata': {
    #         #                 '__description': item.get('description_blocks',  # Описание товара
    #         #                 "Артикул": item.get('vendor_code'),
    #         #                 "Код товара": str(),
    #         #                 "Цвет": str(),
    #         #                 'Объем': str(),
    #         #                 'Страна производитель': str(),
    #     },
    #     "variants": int()  # Кол-во вариантов у товара в карточке
    #
    # }
