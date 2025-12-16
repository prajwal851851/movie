# streaming/management/commands/scrape_target.py
import os
import sys
import django
from django.core.management.base import BaseCommand

# --- Path Setup ---
# Get the absolute path to the directory containing this command file
DJANGO_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get the path to the Scrapy project directory
SCRAPY_PROJECT_PATH = os.path.join(DJANGO_PROJECT_ROOT, 'scraper')

# Add both the Django root and the Scrapy project path to sys.path
# This ensures all modules can be found
if SCRAPY_PROJECT_PATH not in sys.path:
    sys.path.append(SCRAPY_PROJECT_PATH)
if DJANGO_PROJECT_ROOT not in sys.path:
    sys.path.append(DJANGO_PROJECT_ROOT)

# --- Django Setup ---
# Set the Django settings module. Make sure 'movie_scrape' matches your project name.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_scrape.settings")
django.setup()

# --- Import Scrapy settings ---
from scraper.settings import USER_AGENT, ITEM_PIPELINES, ROBOTSTXT_OBEY, DOWNLOAD_DELAY
from scrapy.crawler import CrawlerProcess
from scrapy.utils.misc import load_object


class Command(BaseCommand):
    help = 'Run a specific spider to scrape a target site'

    def add_arguments(self, parser):
        parser.add_argument('spider_name', type=str, help='The name of the spider to run (e.g., makemovies, fawesome)')

    def handle(self, *args, **options):
        spider_name = options['spider_name']

        # The spider 'name' is defined inside the spider file
        if spider_name not in ['makemovies', 'fawesome']:
            self.stdout.write(self.style.ERROR(f"Invalid spider name: {spider_name}"))
            return

        self.stdout.write(f"Starting spider: {spider_name}")
        
        try:
            # --- The Fix ---
            # Instead of letting Scrapy guess the project, we tell it directly.
            # We manually create a settings object from your scraper's settings.py.
            process = CrawlerProcess({
                'USER_AGENT': USER_AGENT,
                'ITEM_PIPELINES': ITEM_PIPELINES,
                # Add any other settings from scraper.settings.py that are essential
                'ROBOTSTXT_OBEY': ROBOTSTXT_OBEY,
                'DOWNLOAD_DELAY': DOWNLOAD_DELAY,
            })
            
            # Dynamically load the spider class
            spider_class = load_object(f'scraper.spiders.{spider_name}.{spider_name.capitalize()}Spider')
            process.crawl(spider_class)
            
            # This will block until the spider is finished
            process.start()
            
            self.stdout.write(self.style.SUCCESS(f"Successfully ran the '{spider_name}' spider."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc()) # Print full error for debugging