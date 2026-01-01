# scraper/spiders/sflix_spider.py
import scrapy
from scrapy import signals
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
    start_urls = ["https://sflix.ps/home"]  # Use /home page which has movie listings

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 2,
        "CONCURRENT_REQUESTS": 1,
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        
        # Initialize Selenium WebDriver
        spider.logger.info('Initializing Selenium WebDriver for Sflix spider...')
        
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # Bypass automation detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            service = Service(ChromeDriverManager().install())
            spider.driver = webdriver.Chrome(service=service, options=options)
            # Further bypass automation detection
            spider.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            spider.driver.set_page_load_timeout(30)
            spider.logger.info('✓ Selenium WebDriver initialized successfully')
        except Exception as e:
            spider.logger.error(f'Failed to initialize Selenium: {e}')
            raise
        
        # Connect spider close signal to cleanup driver
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        """
        Close the Selenium WebDriver when the spider closes.
        This method is connected to the `signals.spider_closed` signal.
        """
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info('Selenium WebDriver closed')


    def parse(self, response):
        """Parse the main page to extract movie links."""
        self.logger.info(f'🔍 Parsing main page: {response.url}')
        
        try:
            self.driver.get(response.url)
            self.logger.info('⏳ Waiting for page to load...')
            time.sleep(8)  # Increased wait time for JavaScript to load
            
            # Scroll down to trigger lazy loading
            self.logger.info('📜 Scrolling page to load more content...')
            for i in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Scroll back to top
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            html = self.driver.page_source
            sel = HtmlResponse(url=response.url, body=html, encoding="utf-8")
            
            # Try multiple selectors to find movie links
            links = []
            
            # Try different possible selectors
            selectors = [
                'a[href*="/movie/"]::attr(href)',
                'a[href*="/tv/"]::attr(href)',
                'a.film-poster-ahref::attr(href)',
                'a.item::attr(href)',
                '.flw-item a::attr(href)',
                '.film_list-wrap .film-poster a::attr(href)',
            ]
            
            for selector in selectors:
                found = sel.css(selector).getall()
                if found:
                    self.logger.info(f'✓ Found {len(found)} links with selector: {selector}')
                    links.extend(found)
            
            # Remove duplicates
            links = list(set(links))
            
            self.logger.info(f'📊 Total unique links found: {len(links)}')
            
            if not links:
                self.logger.warning('⚠️ No movie links found! Saving page source for debugging...')
                # Save the HTML for debugging
                debug_file = 'd:/movie_scrape/debug_sflix_page.html'
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                self.logger.info(f'💾 Page source saved to: {debug_file}')
                return
            
            # Limit to first 200 links
            for link in links[:200]:
                full_url = response.urljoin(link)
                self.logger.info(f'➡️ Queueing: {full_url}')
                yield scrapy.Request(
                    full_url,
                    callback=self.parse_movie,
                    dont_filter=True,
                )
                
        except Exception as e:
            self.logger.error(f'❌ Error in parse: {e}', exc_info=True)

    def parse_movie(self, response):
        """Parse individual movie page to extract streaming information."""
        self.logger.info(f'🎬 Parsing movie page: {response.url}')
        
        try:
            self.driver.get(response.url)
            self.logger.info('⏳ Waiting for movie page to load...')
            time.sleep(8)
            
            # Scroll to trigger any lazy-loaded iframes
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)

            html = self.driver.page_source
            sel = HtmlResponse(url=response.url, body=html, encoding="utf-8")

            item = MovieItem()
            item["source_site"] = "sflix"
            item["source_url"] = response.url
            item["imdb_id"] = "sflix_" + response.url.split("/")[-1]

            # Extract title and clean it
            title = sel.css("h1::text, h2.heading-name::text, .title::text, title::text").get()
            if title:
                title = title.strip()
                # Remove "Watch ... full HD on SFlix Free" wrapper
                if "Watch" in title and "full HD on SFlix Free" in title:
                    # Extract the actual movie name and year
                    import re
                    match = re.search(r'Watch (.+?) (\d{4}) full HD', title)
                    if match:
                        title = match.group(1).strip()
                        year = match.group(2)
                    else:
                        # Fallback: just remove the wrapper text
                        title = title.replace("Watch ", "").replace(" full HD on SFlix Free", "").strip()
                        year = None
                else:
                    year = None
            else:
                title = "Unknown"
                year = None
            
            item["title"] = title
            item["year"] = year
            
            self.logger.info(f'📝 Title: {item["title"]} ({year})')
            
            # Extract poster URL
            poster_selectors = [
                ".film-poster img::attr(src)",
                ".detail_page-watch img::attr(src)",
                "img.film-poster-img::attr(src)",
                "meta[property='og:image']::attr(content)",
                ".dp-i-c-poster img::attr(src)",
            ]
            
            poster_url = None
            for selector in poster_selectors:
                poster_url = sel.css(selector).get()
                if poster_url:
                    self.logger.info(f'✓ Found poster with selector: {selector}')
                    break
            
            if poster_url:
                item["poster_url"] = response.urljoin(poster_url)
                self.logger.info(f'🖼️ Poster URL: {item["poster_url"][:60]}...')
            else:
                item["poster_url"] = ""
                self.logger.warning(f'⚠️ No poster found for: {item["title"]}')
            
            # Extract synopsis
            synopsis_selectors = [
                ".description::text",
                ".film-description::text",
                "meta[property='og:description']::attr(content)",
                ".dp-i-content .description::text",
            ]
            
            synopsis = None
            for selector in synopsis_selectors:
                synopsis = sel.css(selector).get()
                if synopsis:
                    break
            
            item["synopsis"] = synopsis.strip() if synopsis else ""

            # Try multiple selectors for iframe, but filter out tracking iframes
            iframe_selectors = [
                "iframe#iframe-embed::attr(src)",
                ".watch-iframe iframe::attr(src)",
                "#embed-player iframe::attr(src)",
                "#player iframe::attr(src)",
                "iframe[src*='embed']::attr(src)",
                "iframe",  # Fallback: get all iframes and filter
            ]
            
            # Domains to exclude (tracking/analytics iframes)
            excluded_domains = [
                'sharethis.com',
                'cloudflare',
                'google',
                'facebook',
                'twitter',
                'analytics',
                'ads',
                'advert',
            ]
            
            iframe = None
            for selector in iframe_selectors:
                if selector == "iframe":
                    # Get all iframes and filter
                    all_iframes = sel.css("iframe::attr(src)").getall()
                    for iframe_url in all_iframes:
                        # Skip if it's a tracking iframe
                        if any(domain in iframe_url.lower() for domain in excluded_domains):
                            continue
                        # Skip if it's too short or looks like a placeholder
                        if len(iframe_url) < 10 or iframe_url.startswith('about:'):
                            continue
                        iframe = iframe_url
                        self.logger.info(f'✓ Found iframe (filtered): {iframe[:100]}...')
                        break
                else:
                    iframe = sel.css(selector).get()
                    if iframe:
                        # Check if it's not a tracking iframe
                        if not any(domain in iframe.lower() for domain in excluded_domains):
                            self.logger.info(f'✓ Found iframe with selector: {selector}')
                            break
                        else:
                            iframe = None  # Reset and try next selector
                
                if iframe:
                    break

            if not iframe:
                self.logger.warning(f'⚠️ No iframe found for: {item["title"]} ({response.url})')
                return

            iframe = response.urljoin(iframe)
            self.logger.info(f'🔗 Iframe URL: {iframe}')

            # Detect server type
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
            elif "vidsrc" in low:
                server = "VidSrc"

            item["stream_url"] = iframe
            item["server_name"] = server
            item["quality"] = "HD"
            item["language"] = "EN"
            
            self.logger.info(f'✅ Scraped: {item["title"]} | Server: {server}')
            yield item
            
        except Exception as e:
            self.logger.error(f'❌ Error parsing movie {response.url}: {e}', exc_info=True)

