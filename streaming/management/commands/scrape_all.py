# streaming/management/commands/scrape_all_sites.py
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
    help = 'Run all movie spiders to scrape all configured sites'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sites',
            nargs='+',
            default=['movietreasures', 'fmovies', 'makemovies', 'fawesome', 'simple_movies'],
            help='List of sites to scrape (default: movietreasures fmovies makemovies fawesome simple_movies)'
        )

    def handle(self, *args, **options):
        sites = options['sites']
        
        self.stdout.write(f"Starting spiders for: {', '.join(sites)}")
        
        try:
            # Get Scrapy settings
            settings = get_project_settings()
            settings.set('ROBOTSTXT_OBEY', False)
            settings.set('LOG_LEVEL', 'INFO')
            settings.set('CONCURRENT_REQUESTS', 1)
            settings.set('DOWNLOAD_DELAY', 3)
            
            process = CrawlerProcess(settings)
            
            # Import spiders
            from scraper.spiders.movietreasures_spider import MovieTreasuresSpider
            from scraper.spiders.fmovies_spider import FmoviesSpider
            from scraper.spiders.makemovies_selenium_spider import MakemoviesSeleniumSpider
            from scraper.spiders.fawesome_spider import FawesomeSpider
            from scraper.spiders.simple_movie_spider import SimpleMovieSpider
            
            # Add spiders to process
            if 'movietreasures' in sites:
                process.crawl(MovieTreasuresSpider)
                self.stdout.write('Added MovieTreasures spider')
            
            if 'fmovies' in sites:
                process.crawl(FmoviesSpider)
                self.stdout.write('Added FMovies spider')
            
            if 'makemovies' in sites:
                process.crawl(MakemoviesSeleniumSpider)
                self.stdout.write('Added MakMovies spider')
            
            if 'fawesome' in sites:
                process.crawl(FawesomeSpider)
                self.stdout.write('Added FAwesome spider')
            
            if 'simple_movies' in sites:
                process.crawl(SimpleMovieSpider)
                self.stdout.write('Added Simple Movies spider')
            
            # Start all spiders
            self.stdout.write(self.style.SUCCESS('\nStarting all spiders...'))
            process.start()
            
            self.stdout.write(
                self.style.SUCCESS(f"\nSuccessfully completed scraping from {len(sites)} sites.")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())