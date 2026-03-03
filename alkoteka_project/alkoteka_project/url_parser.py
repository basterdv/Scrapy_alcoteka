import os
import re

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class AlkotekaUrlMapper:
    """Класс для преобразования URL и  URL_API.
        BASE_API_URL - базовый URL API
        CITY_UUID - UUID города, для которого нужно получить каталог
        CATEGORY_PREFIX - префикс для подкатегорий (в API они называются 'options[categories][]')
    """

    BASE_API_URL = "https://alkoteka.com"
    CITY_UUID = "4a70f9e0-46ae-11e7-83ff-00155d026416"
    CATEGORY_PREFIX = "options-categories_"

    @classmethod
    def load_urls_from_file(cls, file_path):
        """
        Загружает URL из файла, валидирует их и преобразует в API ссылки.
        Возвращает список уникальных API URL.
        """
        if not os.path.exists(file_path):
            # Создаем пустой файл, если его нет
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Вставьте ссылки на категории Alkoteka ниже\n")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Ищем URL каталога
            web_urls = re.findall(r'https?://alkoteka\.com/catalog/[^\s,]+', content)

            api_urls = []
            for url in web_urls:
                # Преобразовывает в URL API
                api_url = cls.url_to_api(url)
                if api_url:
                    api_urls.append(api_url)

            # Возвращаем уникальный список
            return list(set(api_urls))

    @classmethod
    def url_to_api(cls, web_url, page=1, per_page=20):
        """Преобразовывает обычные URL каталога в URL API.

            пример использования:
            api_url = AlkotekaUrlMapper.map_to_api("https://alkoteka.com/")
        """
        # Разбираем путь URL (убираем пустые части и слово 'catalog')
        path = urlparse(web_url).path
        parts = [p for p in path.split('/') if p and p != 'catalog']

        params = {
            'city_uuid': cls.CITY_UUID,
            'page': page,
            'per_page': per_page
        }

        if not parts:
            return None

        # Первый элемент
        params['root_category_slug'] = parts[0]

        # Если есть второй элемент, проверяем на наличие фильтра подкатегории
        if len(parts) > 1:
            for part in parts[1:]:
                if cls.CATEGORY_PREFIX in part:
                    # Извлекаем слаг
                    cat_slug = part.replace(cls.CATEGORY_PREFIX, "")
                    params['options[categories][]'] = cat_slug

        # Собираем URL API.
        query_string = urlencode(params, safe='[]')
        return f"{cls.BASE_API_URL}/web-api/v1/product?{query_string}"

    @staticmethod
    def update_api_params(api_url, per_page=None, page=None):
        """
        Принимает API URL и меняет в нем per_page или page,
        сохраняя все остальные параметры (фильтры, категории).

        Пример использования:
            старый_url = "https://alkoteka.com/web-api/v1/product?city_uuid=..."
            новый_url = AlkotekaUrlMapper.update_api_params(старый_url, per_page=50)
        """
        parsed_url = urlparse(api_url)
        # Разбираем query-string в словарь
        params = parse_qs(parsed_url.query)

        # Извлекаем категорию для возврата (сначала из фильтра, если нет — из корня)
        # parse_qs возвращает списки, поэтому берем [0]
        category_list = params.get('options[categories][]') or params.get('root_category_slug')
        category = category_list[0] if category_list else "unknown"

        # Обновляем per_page, если передано
        if per_page is not None:
            params['per_page'] = [per_page]

        # Обновляем page, если передано
        if page is not None:
            params['page'] = [page]

        # Собираем параметры обратно. Старая часть URL остается неизменной.
        new_query = urlencode(params, doseq=True, safe='[]')

        # Возвращаем обновленный URL API
        return category, urlunparse(parsed_url._replace(query=new_query))

    @classmethod
    def get_detail_api_url(cls, product_slug, city_uuid=None):
        """
        Формирует URL для получения данных конкретного товара по его slug.
        Результат: https://alkoteka.com/web-api/v1/product/eddu-grey-rok_43968?city_uuid=...
        """
        uuid = city_uuid if city_uuid else cls.CITY_UUID
        # Формируем путь: базовый API + / + slug товара
        return f"{cls.BASE_API_URL}/web-api/v1/product/{product_slug}?city_uuid={uuid}"
