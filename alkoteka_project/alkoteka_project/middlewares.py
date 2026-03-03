import os
import random

import requests
from scrapy import signals


class AlkotekaProjectDownloaderMiddleware:
    def __init__(self, crawler, proxy_file):
        self.crawler = crawler
        self.proxy_file = proxy_file
        self.proxies = self._load_proxies()

    @classmethod
    def from_crawler(cls, crawler):
        # Передаем crawler в __init__
        s = cls(crawler=crawler, proxy_file=crawler.settings.get('PROXY_FILE', 'proxies.txt'))
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def _load_proxies(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_path, self.proxy_file)
        proxies = []

        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Добавляйте прокси ниже по одному на строку\n")
            return []
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Добавляем проверку startswith('#'), чтобы не пытаться парсить комментарии
                proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]


        # Добавляем бесплатные прокси
        try:
            # Запрашиваем 50 свежих HTTP прокси
            api_url = "https://api.proxyscrape.com"
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                free_proxies = [f"http://{p.strip()}" for p in response.text.split('\n') if p.strip()]
                proxies.extend(free_proxies)
        except Exception as e:
            self.crawler.spider.logger.error(f"Ошибка загрузки бесплатных прокси: {e}")

        return list(set(proxies))

    def process_request(self, request, spider):  # Добавлен аргумент spider
        if not self.proxies:
            return None

        proxy = random.choice(self.proxies)
        request.meta['proxy'] = proxy
        return None


    def process_response(self, request, response, ):
        return response

    def process_exception(self, request, exception, ):
        pass

    def spider_opened(self):
        self.crawler.spider.logger.info(f"Proxies loaded: {len(self.proxies)}")

    # def spider_opened(self, spider):
    #     spider.logger.info(f"Spider {spider.name} opened. Proxies loaded: {len(self.proxies)}")
