# streaming/management/commands/scrape_target.py
import os
import sys
import django
from django.core.management.base import BaseCommand

# --- Path Setup ---
DJANGO_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SCRAPY_PROJECT_PATH = os.path.join(DJANGO_PROJECT_ROOT, 'scraper')

if SCRAPY_PROJECT_PATH not in sys.path:
    sys.path.append(SCRAPY_PROJECT_PATH)
if DJANGO_PROJECT_ROOT not in sys.path:
    sys.path.append(DJANGO_PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_scrape.settings")
django.setup()

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

class Command(BaseCommand):
    help = 'Run a specific spider to scrape a target site'

    def add_arguments(self, parser):
        parser.add_argument('spider_name', type=str, help='The name of the spider to run (e.g., makemovies, fawesome)')

    def handle(self, *args, **options):
        spider_name = options['spider_name']

        if spider_name not in ['makemovies', 'fawesome']:
            self.stdout.write(self.style.ERROR(f"Invalid spider name: {spider_name}. Use 'makemovies' or 'fawesome'"))
            return

        self.stdout.write(f"Starting spider: {spider_name}")
        
        try:
            # Get Scrapy settings
            settings = get_project_settings()
            settings.set('ROBOTSTXT_OBEY', False)  # Disable robots.txt for testing
            settings.set('LOG_LEVEL', 'DEBUG')  # Enable debug logging
            settings.set('CONCURRENT_REQUESTS', 1)  # Slow down requests
            settings.set('DOWNLOAD_DELAY', 2)  # Add delay between requests
            
            process = CrawlerProcess(settings)
            
            # Import and crawl the spider
            if spider_name == 'makemovies':
                from scraper.spiders.makemovies_spider import MakemoviesSpider
                process.crawl(MakemoviesSpider)
            elif spider_name == 'fawesome':
                from scraper.spiders.fawesome_spider import FawesomeSpider
                process.crawl(FawesomeSpider)
            
            process.start()
            
            self.stdout.write(self.style.SUCCESS(f"Successfully ran the '{spider_name}' spider."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())