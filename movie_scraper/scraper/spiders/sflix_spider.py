# scraper/spiders/sflix_spider.py
import scrapy
import time
import re
import os
import django

from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from scraper.items import MovieItem

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_scrape.settings")
django.setup()

from streaming.models import Movie


class SflixSpider(scrapy.Spider):
    name = "sflix"
    allowed_domains = ["sflix.ps", "sflix.to", "sflix.se"]
    start_urls = ["https://sflix.ps/"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS": 1,
    }

    def spider_opened(self, spider):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

    def spider_closed(self, spider):
        self.driver.quit()

    def parse(self, response):
        self.driver.get(response.url)
        time.sleep(5)

        html = self.driver.page_source
        sel = HtmlResponse(url=response.url, body=html, encoding="utf-8")

        links = sel.css('a[href*="/movie/"]::attr(href)').getall()

        for link in links[:200]:
            yield scrapy.Request(
                response.urljoin(link),
                callback=self.parse_movie,
                dont_filter=True,
            )

    def parse_movie(self, response):
        self.driver.get(response.url)
        time.sleep(5)

        html = self.driver.page_source
        sel = HtmlResponse(url=response.url, body=html, encoding="utf-8")

        item = MovieItem()
        item["source_site"] = "sflix"
        item["source_url"] = response.url
        item["imdb_id"] = "sflix_" + response.url.split("/")[-1]

        title = sel.css("h1::text").get()
        item["title"] = title.strip() if title else "Unknown"

        # ─── EXTRACT EMBED IFRAME (THIS IS THE KEY FIX) ───
        iframe = sel.css("iframe::attr(src)").get()

        if not iframe:
            return

        iframe = response.urljoin(iframe)

        server = "Unknown"
        low = iframe.lower()
        if "upcloud" in low:
            server = "UpCloud"
        elif "megacloud" in low:
            server = "MegaCloud"
        elif "vidcloud" in low:
            server = "VidCloud"
        elif "akcloud" in low:
            server = "AkCloud"

        item["stream_url"] = iframe
        item["server_name"] = server
        item["quality"] = "HD"
        item["language"] = "EN"

        yield item
