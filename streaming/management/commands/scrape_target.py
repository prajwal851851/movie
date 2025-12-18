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
        parser.add_argument(
            'spider_name', 
            type=str, 
            help='The name of the spider to run (movietreasures, fmovies, makemovies, fawesome, simple_movies)'
        )

    def handle(self, *args, **options):
        spider_name = options['spider_name']

        valid_spiders = ['movietreasures', 'fmovies', 'makemovies', 'fawesome', 'simple_movies']
        if spider_name not in valid_spiders:
            self.stdout.write(
                self.style.ERROR(
                    f"Invalid spider name: {spider_name}. Valid options: {', '.join(valid_spiders)}"
                )
            )
            return

        self.stdout.write(f"Starting spider: {spider_name}")
        
        try:
            # Get Scrapy settings
            settings = get_project_settings()
            settings.set('ROBOTSTXT_OBEY', False)
            settings.set('LOG_LEVEL', 'INFO')
            settings.set('CONCURRENT_REQUESTS', 1)
            settings.set('DOWNLOAD_DELAY', 3)
            
            process = CrawlerProcess(settings)
            
            # Import and crawl the spider
            if spider_name == 'movietreasures':
                from scraper.spiders.movietreasures_spider import MovieTreasuresSpider
                process.crawl(MovieTreasuresSpider)
            elif spider_name == 'fmovies':
                from scraper.spiders.fmovies_spider import FmoviesSpider
                process.crawl(FmoviesSpider)
            elif spider_name == 'makemovies':
                from scraper.spiders.makemovies_selenium_spider import MakemoviesSeleniumSpider
                process.crawl(MakemoviesSeleniumSpider)
            elif spider_name == 'fawesome':
                from scraper.spiders.fawesome_spider import FawesomeSpider
                process.crawl(FawesomeSpider)
            elif spider_name == 'simple_movies':
                from scraper.spiders.simple_movie_spider import SimpleMovieSpider
                process.crawl(SimpleMovieSpider)
            
            process.start()
            
            self.stdout.write(
                self.style.SUCCESS(f"Successfully ran the '{spider_name}' spider.")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())