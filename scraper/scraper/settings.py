# movie_project/scraper/scraper/settings.py

import os
import sys
import django

# Path to your Django project's settings file
DJANGO_PROJECT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "movie_scrape.settings")
django.setup()

# Item Pipelines
ITEM_PIPELINES = {
   'scraper.pipelines.DjangoItemPipeline': 300,
}