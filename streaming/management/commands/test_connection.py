# streaming/management/commands/test_connection.py
import requests
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Test connection to target websites'

    def handle(self, *args, **options):
        sites = [
            'https://makmoviestreaming.com/movie/',
            'https://fawesome.tv/movies'
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for site in sites:
            self.stdout.write(f'\nTesting: {site}')
            try:
                response = requests.get(site, headers=headers, timeout=10)
                self.stdout.write(f'Status Code: {response.status_code}')
                self.stdout.write(f'Content Length: {len(response.text)} characters')
                
                # Check for common indicators
                if 'movie' in response.text.lower():
                    self.stdout.write(self.style.SUCCESS('✓ Page contains "movie" text'))
                
                if '<a' in response.text:
                    link_count = response.text.count('<a')
                    self.stdout.write(self.style.SUCCESS(f'✓ Found approximately {link_count} links'))
                
                # Save sample for inspection
                filename = f"sample_{site.split('/')[2]}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(response.text[:10000])  # First 10k chars
                self.stdout.write(f'Saved sample to: {filename}')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))