# streaming/management/commands/run_improved_scraper.py
import os
import sys
import django
from django.core.management.base import BaseCommand
import importlib

# Path Setup
# Ensure DJANGO_PROJECT_ROOT points to the repository root (one level higher)
# so the top-level `scraper` package (d:\movie_scrape\scraper) is importable.
DJANGO_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SCRAPY_PROJECT_PATH = os.path.join(DJANGO_PROJECT_ROOT, 'movie_scraper')

if SCRAPY_PROJECT_PATH not in sys.path:
    sys.path.insert(0, SCRAPY_PROJECT_PATH)
if DJANGO_PROJECT_ROOT not in sys.path:
    sys.path.insert(0, DJANGO_PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_scrape.settings")
django.setup()

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

class Command(BaseCommand):
    help = 'Run improved movie scrapers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--spider',
            type=str,
            default='archive',
            choices=['archive', 'makemovies', 'goojara', 'm4uhd', 'all'],
            help='Which spider to run (archive, makemovies, goojara, m4uhd, or all)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=30,
            help='Maximum number of movies to scrape'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            default=5,
            help='Maximum number of pages to scrape per URL (for pagination support)'
        )

    def handle(self, *args, **options):
        spider_choice = options['spider']
        limit = options['limit']
        max_pages = options['max_pages']
        
        self.stdout.write(self.style.SUCCESS(f'Starting {spider_choice} spider(s)...'))
        
        # Import spiders after paths are set
        working_archive_module = importlib.import_module('scraper.spiders.working_archive_spider')
        WorkingArchiveSpider = working_archive_module.WorkingArchiveSpider
        improved_makemovies_module = importlib.import_module('scraper.spiders.improved_makemovies_spider')
        ImprovedMakemoviesSpider = improved_makemovies_module.ImprovedMakemoviesSpider
        goojara_module = importlib.import_module('scraper.spiders.goojara_spider')
        GoojaraSpider = goojara_module.GoojaraSpider
        m4uhd_module = importlib.import_module('scraper.spiders.m4uhd_spider')
        M4uhdSpider = m4uhd_module.M4uhdSpider
        
        try:
            settings = get_project_settings()
            settings.set('ROBOTSTXT_OBEY', False)
            settings.set('LOG_LEVEL', 'INFO')
            settings.set('CONCURRENT_REQUESTS', 2)
            settings.set('DOWNLOAD_DELAY', 2)
            settings.set('ITEM_PIPELINES', {
                'scraper.pipelines.DjangoItemPipeline': 300,
            })
            
            process = CrawlerProcess(settings)
            
            if spider_choice == 'archive' or spider_choice == 'all':
                self.stdout.write('Adding Archive.org spider...')
                process.crawl(WorkingArchiveSpider, limit=limit)
            
            if spider_choice == 'makemovies' or spider_choice == 'all':
                self.stdout.write('Adding Makemovies spider...')
                process.crawl(ImprovedMakemoviesSpider, limit=limit)
            
            if spider_choice == 'goojara' or spider_choice == 'all':
                self.stdout.write('Adding Goojara spider...')
                process.crawl(GoojaraSpider, limit=limit, max_pages=max_pages)
            
            if spider_choice == 'm4uhd' or spider_choice == 'all':
                self.stdout.write('Adding M4uHD spider...')
                process.crawl(M4uhdSpider, limit=limit)
            
            self.stdout.write(self.style.SUCCESS('\nStarting crawl...'))
            process.start()
            
            self.stdout.write(self.style.SUCCESS('\n✓ Scraping completed!'))
            self.stdout.write('Run "python manage.py runserver" and check http://localhost:8000/')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())