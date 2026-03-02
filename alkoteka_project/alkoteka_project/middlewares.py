import os
import random
import base64
from urllib.parse import urlparse
from scrapy import signals


# useful for handling different item types with a single interface


# class AlkotekaProjectSpiderMiddleware:
#     def __init__(self, proxy_file):
#         self.proxy_file = proxy_file
#         self.proxies = self._load_proxies()
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         # Достаем путь к прокси из settings.py
#         s = cls(proxy_file=crawler.settings.get('PROXY_FILE', 'proxies.txt'))
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s
#          # return cls(proxy_file=crawler.settings.get('PROXY_FILE', 'proxies.txt'))
#
#     def _load_proxies(self):
#         if os.path.exists(self.proxy_file):
#             with open(self.proxy_file, 'r') as f:
#                 return [line.strip() for line in f if line.strip()]
#         return []
#
#     def process_spider_input(self, response, spider):
#         # Called for each response that goes through the spider
#         # middleware and into the spider.
#
#         # Should return None or raise an exception.
#         return None
#
#     def process_spider_output(self, response, result, spider):
#         # Called with the results returned from the Spider, after
#         # it has processed the response.
#
#         # Must return an iterable of Request, or item objects.
#         for i in result:
#             yield i
#
#     def process_spider_exception(self, response, exception, spider):
#         # Called when a spider or process_spider_input() method
#         # (from other spider middleware) raises an exception.
#
#         # Should return either None or an iterable of Request or item objects.
#         pass
#
#     # async def process_start(self, start):
#     #     # Called with an async iterator over the spider start() method or the
#     #     # matching method of an earlier spider middleware.
#     #     async for item_or_request in start:
#     #         yield item_or_request
#
#     def spider_opened(self, spider):
#         spider.logger.info("Spider opened: %s" % spider.name)
#
#     # def _load_proxies(self):
#     #     if os.path.exists(self.proxy_file):
#     #         with open(self.proxy_file, 'r') as f:
#     #             return [line.strip() for line in f if line.strip()]
#     #     return []
#     def process_request(self, request, spider):
#         # Теперь прокси будут подставляться в каждый запрос
#         if self.proxies:
#             proxy = random.choice(self.proxies)
#             request.meta['proxy'] = proxy
#         return None
#     # def process_request(self, request, spider):
#     #     if self.proxies:
#     #         request.meta['proxy'] = random.choice(self.proxies)


# class AlkotekaProjectDownloaderMiddleware:
#     # Not all methods need to be defined. If a method is not defined,
#     # scrapy acts as if the downloader middleware does not modify the
#     # passed objects.
#
#     @classmethod
#     def from_crawler(cls, crawler):
#         # This method is used by Scrapy to create your spiders.
#         s = cls()
#         crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
#         return s
#
#     def process_request(self, request, spider):
#         # Called for each request that goes through the downloader
#         # middleware.
#
#         # Must either:
#         # - return None: continue processing this request
#         # - or return a Response object
#         # - or return a Request object
#         # - or raise IgnoreRequest: process_exception() methods of
#         #   installed downloader middleware will be called
#         return None
#
#     def process_response(self, request, response, spider):
#         # Called with the response returned from the downloader.
#
#         # Must either;
#         # - return a Response object
#         # - return a Request object
#         # - or raise IgnoreRequest
#         return response
#
#     def process_exception(self, request, exception, spider):
#         # Called when a download handler or a process_request()
#         # (from other downloader middleware) raises an exception.
#
#         # Must either:
#         # - return None: continue processing this exception
#         # - return a Response object: stops process_exception() chain
#         # - return a Request object: stops process_exception() chain
#         pass
#
#     def spider_opened(self, spider):
#         spider.logger.info("Spider opened: %s" % spider.name)

class AlkotekaProjectDownloaderMiddleware:
    def __init__(self, crawler, proxy_file):
        self.crawler = crawler
        self.proxy_file = proxy_file
        self.proxies = self._load_proxies()

    # @classmethod
    # def from_crawler(cls, crawler):
    #     # Достаем путь к прокси из settings.py
    #     s = cls(proxy_file=crawler.settings.get('PROXY_FILE', 'proxies.txt'))
    #     crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
    #     return s

    @classmethod
    def from_crawler(cls, crawler):
        # Передаем crawler в __init__
        s = cls(crawler=crawler, proxy_file=crawler.settings.get('PROXY_FILE', 'proxies.txt'))
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def _load_proxies(self):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_path, self.proxy_file)

        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Добавляйте прокси ниже по одному на строку\n")
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            # Добавляем проверку startswith('#'), чтобы не пытаться парсить комментарии
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

    def process_request(self, request):
        if not self.proxies:
            return None

        proxy = random.choice(self.proxies)
        # Проверяем, есть ли в строке логин/пароль (формат http://user:pass@ip:port)
        parsed = urlparse(proxy)

        if parsed.username and parsed.password:
            # Создаем заголовок Proxy-Authorization
            auth = f"{parsed.username}:{parsed.password}"
            encoded_auth = base64.b64encode(auth.encode()).decode()
            request.headers['Proxy-Authorization'] = f'Basic {encoded_auth}'
            # В meta передаем только чистый адрес прокси без логина для надежности
            request.meta['proxy'] = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
        else:
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
