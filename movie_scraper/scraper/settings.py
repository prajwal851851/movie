# scraper/scraper/settings.py

import os
import sys
import django
# Add to scraper/scraper/settings.py
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
# Path to your Django project's settings file
DJANGO_PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_scrape.settings")
django.setup()

# Scrapy settings
BOT_NAME = 'scraper'

SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'

# Obey robots.txt rules - set to False for testing
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests
CONCURRENT_REQUESTS = 8

# Configure a delay for requests (in seconds)
DOWNLOAD_DELAY = 2

# Add user agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 50,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
}

# Configure item pipelines
ITEM_PIPELINES = {
   'scraper.pipelines.DjangoItemPipeline': 300,
}

# Enable and configure HTTP caching (for development)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 401, 403, 404]

# Set log level
LOG_LEVEL = 'INFO'

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]




DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # or your database path
        'OPTIONS': {
            'timeout': 20,  # Increase timeout to 20 seconds
            'check_same_thread': False,  # Allow multi-threaded access
        },
        'ATOMIC_REQUESTS': True,  # Wrap each request in a transaction
    }
}

# Additionally, add these settings to help with concurrency:

# Reduce the number of database connections
CONN_MAX_AGE = 0  # Close database connections after each request

# Add connection poo