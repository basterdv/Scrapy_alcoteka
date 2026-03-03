import scrapy
import time
from itemloaders.processors import TakeFirst, MapCompose

def get_timestamp(value):
    return int(time.time())

def format_title(values, loader_context):
    """Склеивает название и доп. информацию (объем/цвет)"""
    item_name = values[0] if values else ""

    labels = loader_context.get('filter_labels', [])
    extra = next((l.get('title', '') for l in labels if l.get('filter') in ['obem', 'cvet']), '')
    return f"{item_name}, {extra}".strip(', ')

def extract_brand(description_blocks):
    """ Ищет бренд в массиве """
    if not isinstance(description_blocks, dict):
        return None

    if description_blocks.get('code') == 'brend':
        vals = description_blocks.get('values', {})
        if isinstance(vals, dict):
            return vals.get('name')
        elif isinstance(vals, list) and len(vals) > 0:
            return vals[0].get('name')
    return ''


class AlkotekaProjectItem(scrapy.Item):
    timestamp = scrapy.Field(                                       # Дата и время сбора товара в формате timestamp.
        input_processor=MapCompose(get_timestamp),
        output_processor=TakeFirst())
    RPC = scrapy.Field(output_processor=TakeFirst())                # Уникальный код товара.
    url = scrapy.Field(output_processor=TakeFirst())                # Ссылка на страницу товара.
    title = scrapy.Field(output_processor=format_title)             # Заголовок/название товара
    marketing_tags = scrapy.Field()                                 # Список маркетинговых тэгов
    brand = scrapy.Field(                                           # Бренд товара
        input_processor=MapCompose(extract_brand),
        output_processor=TakeFirst())
    section = scrapy.Field()                                        # Иерархия разделов
    price_data = scrapy.Field(output_processor=TakeFirst())         # "current" Цена со скидкой, если скидки нет то = original.
                                                                    # "original" Оригинальная цена.
                                                                    # "sale_tag" Если есть скидка на товар

    stock = scrapy.Field(output_processor=TakeFirst())              # "in_stock" Есть товар в наличии в магазине или нет.
                                                                    # "count" информацию о количестве оставшегося товара в наличии, иначе 0.

    assets = scrapy.Field(output_processor=TakeFirst())             # "main_image" Ссылка на основное изображение товара.
                                                                    # "set_images" Список ссылок на все изображения товара.
                                                                    # "view360" Список ссылок на изображения в формате 360.
                                                                    # "video" Список ссылок на видео/видеообложки товара.

    metadata = scrapy.Field(output_processor=TakeFirst())           # Описание товара
    variants = scrapy.Field(output_processor=TakeFirst())           # Кол-во вариантов у товара в карточке


