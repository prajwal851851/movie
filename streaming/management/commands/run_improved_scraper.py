# streaming/management/commands/run_improved_scraper.py
import os
import sys
import django
from django.core.management.base import BaseCommand
import importlib

# Path Setup
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
            choices=['archive', 'makemovies', 'goojara', 'goojara_v2','sflix', 'oneflix_ultimate', 'oneflix_network', 'tmdb_vidsrc', 'tmdb_vidsrc_v2', 'all'],
            help='Which spider to run (archive, makemovies, goojara, goojara_v2, m4uhd, oneflix_ultimate, oneflix_network, tmdb_vidsrc, or all)'
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
        parser.add_argument(
            '--api-key',
            type=str,
            default=None,
            help='TMDB API key (required for tmdb_vidsrc spider)'
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

        goojara_v2_module = importlib.import_module('scraper.spiders.goojara_spider_v2')
        GoojaraSpiderV2 = goojara_v2_module.GoojaraSpiderFixed

        # Import 1Flix spiders
        oneflix_module = importlib.import_module('scraper.spiders.oneflix_ultimate')
        OneFlixUltimateSpider = oneflix_module.OneFlixUltimateSpider
        
        oneflix_network_module = importlib.import_module('scraper.spiders.oneflix_network_capture')
        OneflixNetworkCaptureSpider = oneflix_network_module.OneflixNetworkCaptureSpider
        
        # FIX: Corrected the class name to match the definition in sflix_spider.py
        sflix_module = importlib.import_module('scraper.spiders.sflix_spider')
        SflixSpider = sflix_module.SflixSpider
        
        # Import TMDB-VidSrc spider
        tmdb_module = importlib.import_module('scraper.spiders.tmdb_vidsrc_spider')
        TmdbVidsrcSpider = tmdb_module.TmdbVidsrcSpider

        tmdb_v2_module = importlib.import_module('scraper.spiders.tmdb_vidsrc_spider_v2')
        TmdbVidsrcSpiderV2 = tmdb_v2_module.TmdbVidsrcSpiderV2

        #m4uhd_module = importlib.import_module('scraper.spiders.m4uhd_spider')
        #M4uhdSpider = m4uhd_module.M4uhdSpider

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

            if spider_choice == 'sflix' or spider_choice == 'all':
                self.stdout.write('Adding sflix spider...')
                # FIX: Updated the variable name here to be consistent
                process.crawl(SflixSpider, limit=limit, max_pages=max_pages)

            if spider_choice == 'goojara_v2':
                self.stdout.write('Adding Goojara V2 spider (Multi-Server + Smart Scraping)...')
                process.crawl(GoojaraSpiderV2, limit=limit, max_pages=max_pages, rescrape_broken=True)

            if spider_choice == 'oneflix_ultimate' or spider_choice == 'all':
                self.stdout.write('Adding 1Flix Ultimate spider (UpCloud/MegaCloud/VidCloud)...')
                process.crawl(OneFlixUltimateSpider, limit=limit, max_pages=max_pages)
            
            if spider_choice == 'oneflix_network':
                self.stdout.write('Adding 1Flix Network Capture spider (Advanced URL Extraction)...')
                process.crawl(OneflixNetworkCaptureSpider, limit=limit, max_pages=max_pages)
            
            if spider_choice == 'tmdb_vidsrc':
                api_key = options.get('api_key') or '9c179ef2342597bccad54c238061343e'
                self.stdout.write('Adding TMDB-VidSrc spider (API-based, no scraping)...')
                process.crawl(TmdbVidsrcSpider, api_key=api_key, limit=limit, max_pages=max_pages)

            if spider_choice == 'tmdb_vidsrc_v2':
                api_key = options.get('api_key') or '9c179ef2342597bccad54c238061343e'
                self.stdout.write('Adding TMDB-VidSrc Spider V2 (High Detail + Metadata)...')
                process.crawl(TmdbVidsrcSpiderV2, api_key=api_key, limit=limit, max_pages=max_pages)

            self.stdout.write(self.style.SUCCESS('\nStarting crawl...'))
            process.start()

            self.stdout.write(self.style.SUCCESS('\n✓ Scraping completed!'))
            self.stdout.write('Run "python manage.py runserver" and check http://localhost:8000/')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            import traceback
            self.stdout.write(traceback.format_exc())