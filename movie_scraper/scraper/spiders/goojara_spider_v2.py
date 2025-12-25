"""
Goojara spider with infinite scroll detection and comprehensive movie extraction.
FIXED VERSION - Corrects pagination, duplicate checking, and URL pattern matching logic.
"""
import scrapy
from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from scraper.items import MovieItem  # Assuming MovieItem is defined in scraper.items
import time
import re
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_scrape.settings')
django.setup()

from streaming.models import Movie, StreamingLink  # Assuming these are your Django models

class GoojaraSpiderFixed(scrapy.Spider):
    name = 'goojara_fixed'
    allowed_domains = ['goojara.to', 'ww1.goojara.to', 'supernova.to']

    # Start with the main listing page
    start_urls = ['https://ww1.goojara.to/watch-movies']

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'CONCURRENT_REQUESTS': 1,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'COOKIES_ENABLED': True,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [403, 500, 502, 503, 504, 522, 524, 408, 429],
    }

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        # Connect spider lifecycle signals
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        """
        Initialize Selenium WebDriver when the spider opens.
        This method is connected to the `signals.spider_opened` signal.
        """
        self.logger.info('Initializing Selenium WebDriver...')

        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # Run Chrome in headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        # Bypass automation detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            # Install and use ChromeDriverManager for automatic driver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            # Further bypass automation detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.set_page_load_timeout(30)  # Set page load timeout
            self.logger.info('✓ Selenium WebDriver initialized')
        except Exception as e:
            self.logger.error(f'Failed to initialize Selenium: {e}')
            raise

    def spider_closed(self, spider):
        """
        Close the Selenium WebDriver when the spider closes.
        This method is connected to the `signals.spider_closed` signal.
        """
        if hasattr(self, 'driver'):
            self.driver.quit()
            self.logger.info('Selenium WebDriver closed')

    def __init__(self, limit=200, max_pages=50, rescrape_broken=True, scroll_attempts=10, *args, **kwargs):
        """
        Initialize the spider with custom parameters.

        Args:
            limit (int): Maximum number of movies to scrape.
            max_pages (int): Maximum number of pages to crawl.
            rescrape_broken (bool): Whether to re-scrape movies with previously broken links.
            scroll_attempts (int): Number of times to scroll down to load content.
        """
        super().__init__(*args, **kwargs)
        self.limit = int(limit)
        self.max_pages = int(max_pages)
        self.scroll_attempts = int(scroll_attempts)
        self.rescrape_broken = rescrape_broken
        self.count = 0  # Counter for scraped movies
        self.seen_urls = set()  # To track URLs processed in the current scrape session

        # Duplicate checking logic: Load existing movies from the database
        self.existing_movie_urls = set()  # Stores URLs of movies already in the DB
        self.broken_link_movies = set()  # Stores URLs of movies with broken streaming links
        self._load_existing_movies()

    def _load_existing_movies(self):
        """
        Loads existing movie URLs and broken link movie URLs from the Django database.
        This is part of the duplicate checking logic.
        """
        try:
            # Get all source URLs from the Movie model
            existing_movies = Movie.objects.all().values('source_url')
            for movie in existing_movies:
                if movie['source_url']:
                    self.existing_movie_urls.add(movie['source_url'])

            # If rescrape_broken is True, find movies with at least one inactive streaming link
            if self.rescrape_broken:
                broken_links = StreamingLink.objects.filter(
                    is_active=False
                ).values_list('movie__source_url', flat=True).distinct()
                self.broken_link_movies = set(broken_links)

            self.logger.info(f'Loaded {len(self.existing_movie_urls)} existing movies from database.')
            self.logger.info(f'Found {len(self.broken_link_movies)} movies with broken links to re-scrape.')

        except Exception as e:
            self.logger.warning(f'Could not load existing movies from database: {e}')

    def parse(self, response):
        """
        The main parsing method that handles initial page loading, infinite scrolling,
        pagination, and queuing movie detail page requests.
        """
        self.logger.info(f'{"="*70}')
        self.logger.info(f'Starting comprehensive scrape from: {response.url}')
        self.logger.info(f'{"="*70}')

        try:
            # Use Selenium to load the page as it uses JavaScript for content loading
            self.driver.get(response.url)
            time.sleep(5)  # Give the page time to load initially

            # Check for common blocking patterns
            if '403' in self.driver.title or 'Access Denied' in self.driver.page_source:
                self.logger.error('⚠ Access Denied or blocked by server. Stopping scrape.')
                return

            page_number = 1
            consecutive_empty_pages = 0  # Track consecutive pages with no NEW movies to scrape

            # Infinite scroll and pagination loop
            while self.count < self.limit and page_number <= self.max_pages:
                self.logger.info(f'\n{"*"*70}')
                self.logger.info(f'SCRAPING PAGE {page_number}')
                self.logger.info(f'Current URL: {self.driver.current_url}')
                self.logger.info(f'{"*"*70}')

                # Call helper to extract all movie links by scrolling
                movies_on_page = self._extract_all_movies_with_scroll()

                if not movies_on_page:
                    self.logger.warning(f'⚠ No movie links found on page {page_number}.')
                    consecutive_empty_pages += 1

                    # If we've hit 3 consecutive empty pages, assume we've reached the end
                    if consecutive_empty_pages >= 3:
                        self.logger.info('Found 3 consecutive pages with no movies. Assuming end of content.')
                        break

                    # Try to navigate to next page anyway
                    if not self._navigate_to_next_page():
                        self.logger.info(f'Could not navigate to next page. Stopping.')
                        break
                    page_number += 1
                    continue

                # Reset consecutive empty pages counter since we found movies
                consecutive_empty_pages = 0

                self.logger.info(f'✓ Found {len(movies_on_page)} unique movie links on page {page_number}')

                # Process the extracted movie links
                new_count = 0
                skip_count = 0
                already_seen_count = 0

                for movie_link in movies_on_page:
                    if self.count >= self.limit:
                        self.logger.info(f'✓ Reached scrape limit of {self.limit} movies.')
                        return

                    full_url = response.urljoin(movie_link)

                    # Skip if this URL has already been seen in this scraping session
                    if full_url in self.seen_urls:
                        already_seen_count += 1
                        continue

                    # FIXED DUPLICATE CHECKING LOGIC:
                    # Skip only if the movie exists in DB AND it's not marked for re-scraping
                    should_skip = (
                        full_url in self.existing_movie_urls and
                        full_url not in self.broken_link_movies
                    )

                    if should_skip:
                        self.logger.debug(f'Skipping existing movie: {movie_link}')
                        skip_count += 1
                        continue

                    self.seen_urls.add(full_url)  # Mark as seen for this session
                    new_count += 1
                    self.count += 1

                    status = "🔄 Re-scrape" if full_url in self.broken_link_movies else "🆕 New"
                    self.logger.info(f'{status} [{self.count}/{self.limit}]: {movie_link}')

                    # Yield a Scrapy Request to parse the individual movie page
                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_movie,
                        dont_filter=True  # Allow re-requesting if needed
                    )

                self.logger.info(f'Page {page_number} Summary: {new_count} movies queued, {skip_count} skipped (exists in DB), {already_seen_count} already processed in this session')
                self.logger.info(f'Total movies processed so far: {self.count}')

                # FIXED: Only increment consecutive_empty_pages if we found NO movies to queue
                if new_count == 0:
                    consecutive_empty_pages += 1
                    self.logger.info(f'No new movies to scrape on page {page_number}. (Consecutive empty: {consecutive_empty_pages}/3)')
                else:
                    consecutive_empty_pages = 0  # Reset counter

                # Try to navigate to the next page
                if not self._navigate_to_next_page():
                    self.logger.info(f'Could not find or navigate to the next page after page {page_number}. Stopping.')
                    break

                page_number += 1
                time.sleep(3)  # Wait between page navigations

            self.logger.info(f'\n{"="*70}')
            self.logger.info(f'✓ Comprehensive scrape finished. Queued {self.count} movies from {page_number} pages.')
            self.logger.info(f'{"="*70}')

        except Exception as e:
            self.logger.error(f'An error occurred during the main parsing process: {e}')
            import traceback
            self.logger.error(traceback.format_exc())

    def _extract_all_movies_with_scroll(self):
        """
        Infinite scroll detection: Scrolls the page multiple times to load all
        dynamically loaded movie links.

        Returns:
            list: A list of unique movie links found on the page.
        """
        all_movie_links = set()
        all_found_links = []  # For debugging

        # Attempt to scroll multiple times to ensure all content is loaded
        for scroll_num in range(self.scroll_attempts):
            # Get current page source after scrolling
            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=self.driver.current_url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )

            # Extract all potential links from the current page source
            current_page_links = sel_response.css('a::attr(href)').getall()

            # FIXED: More flexible movie link pattern matching
            # Movie URLs follow the pattern: /m followed by 5-6 alphanumeric characters
            # Examples: /mMG6zJ, /mDJXjL, /mdne8R, /mllenX
            before_count = len(all_movie_links)
            
            for link in current_page_links:
                if link:
                    # Store for debugging
                    if scroll_num == 0 and len(all_found_links) < 20:
                        all_found_links.append(link)
                    
                    # Clean the link (remove query parameters and fragments)
                    clean_link = link.split('?')[0].split('#')[0].strip()
                    
                    # Match movie links: /m followed by 5-6 alphanumeric characters
                    # Using a more flexible pattern
                    if re.match(r'^/m[a-zA-Z0-9]{5,6}$', clean_link):
                        all_movie_links.add(clean_link)
                    # Also try matching full URLs
                    elif 'goojara.to/m' in clean_link:
                        # Extract just the path part
                        match = re.search(r'goojara\.to(/m[a-zA-Z0-9]{5,6})(?:[/?#]|$)', clean_link)
                        if match:
                            all_movie_links.add(match.group(1))

            after_count = len(all_movie_links)
            new_links_found = after_count - before_count

            if scroll_num == 0:
                self.logger.info(f'Initial load: found {after_count} movie links.')
                # Debug: Show first few links found (if any)
                if after_count > 0:
                    sample_links = list(all_movie_links)[:5]
                    self.logger.info(f'✓ Sample movie links: {sample_links}')
                else:
                    # Debug: Show what links were actually found (for troubleshooting)
                    self.logger.warning(f'⚠ No movie links matched pattern!')
                    self.logger.warning(f'Sample of all links found on page: {all_found_links[:10]}')
                    # Show pattern we're looking for
                    self.logger.info(f'Looking for pattern: /m[a-zA-Z0-9]{{5,6}}')
            elif new_links_found > 0:
                self.logger.info(f'Scroll {scroll_num}/{self.scroll_attempts}: Found {new_links_found} new links (Total: {after_count}).')

            # Perform the scroll action
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Pause to allow new content to load

            # Optimization: If no new links are found after a few scrolls, stop scrolling.
            if new_links_found == 0 and scroll_num >= 3:
                self.logger.info(f'No new content detected after {scroll_num} scrolls. Stopping scroll attempts.')
                break

        # Scroll back to the top of the page after finishing scrolls
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        return list(all_movie_links)

    def _navigate_to_next_page(self):
        """
        Pagination logic: Attempts to find and click the "Next" page button.
        It tries multiple common selectors for the next page link/button.

        Returns:
            bool: True if navigation to a new page was successful, False otherwise.
        """
        try:
            current_url = self.driver.current_url

            # Extract current page number from URL if present
            current_page_match = re.search(r'[?&]p=(\d+)', current_url)
            current_page_num = int(current_page_match.group(1)) if current_page_match else 1

            # Try direct URL manipulation first (most reliable for paginated sites)
            if '?p=' in current_url:
                next_page_url = re.sub(r'([?&])p=\d+', r'\1p=' + str(current_page_num + 1), current_url)
            elif '?' in current_url:
                next_page_url = current_url + '&p=' + str(current_page_num + 1)
            else:
                next_page_url = current_url + '?p=' + str(current_page_num + 1)

            self.logger.info(f'Attempting direct navigation to: {next_page_url}')
            self.driver.get(next_page_url)
            time.sleep(4)  # Increased wait time

            new_url = self.driver.current_url
            
            # Verify we actually moved to a new page
            if new_url != current_url:
                # Double-check the page has content
                html = self.driver.page_source
                if len(html) > 1000:  # Basic check that page loaded
                    self.logger.info(f'✓ Navigated to next page: {new_url}')
                    return True
                else:
                    self.logger.warning('Page loaded but appears empty')
                    return False

            # If direct URL manipulation didn't work, try clicking next button
            self.logger.info('Direct navigation failed, trying to find Next button...')

            # Common XPATH and CSS selectors for "Next" page links/buttons
            next_page_selectors = [
                ("xpath", "//a[contains(text(), 'Next')]"),
                ("xpath", "//a[contains(text(), '»')]"),
                ("xpath", "//a[contains(@class, 'next')]"),
                ("xpath", "//button[contains(text(), 'Next')]"),
                ("xpath", "//a[@rel='next']"),
                ("xpath", "//li[contains(@class, 'next')]/a"),
                ("xpath", "//a[contains(@aria-label, 'Next')]"),
                ("xpath", "//a[contains(@title, 'Next')]"),
                ("css", "a[href*='?p=']"),  # Any link with page parameter
            ]

            for selector_type, selector in next_page_selectors:
                try:
                    # Find all elements matching the selector
                    if selector_type == "xpath":
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for next_btn in elements:
                        # Check if the element is visible and enabled
                        if not next_btn.is_displayed() or not next_btn.is_enabled():
                            continue

                        # Further check for 'disabled' attributes in class or parent's class
                        class_attr = next_btn.get_attribute('class') or ''
                        parent_class = next_btn.find_element(By.XPATH, '..').get_attribute('class') or ''

                        if 'disabled' in class_attr.lower() or 'disabled' in parent_class.lower():
                            continue

                        # Scroll the button into view for better interaction
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                        time.sleep(1)

                        current_url_before_click = self.driver.current_url
                        next_btn.click()  # Click the next page button
                        time.sleep(4)  # Wait for the new page to load

                        # Check if the URL has actually changed
                        new_url = self.driver.current_url
                        if new_url != current_url_before_click:
                            self.logger.info(f'✓ Navigated to next page via button: {new_url}')
                            return True

                except (NoSuchElementException, Exception) as e:
                    # If an element is not found or interaction fails, try the next selector
                    continue

            self.logger.info('Could not find a clickable "Next" page button.')
            return False

        except Exception as e:
            self.logger.error(f'Error during navigation to next page: {e}')
            return False

    def parse_movie(self, response):
        """
        Parses an individual movie detail page to extract movie information
        and streaming links.
        """
        self.logger.info(f'Parsing movie detail page: {response.url}')

        try:
            # Use Selenium to get the most up-to-date page source, as it might redirect or load dynamic elements
            self.driver.get(response.url)
            time.sleep(3)

            html = self.driver.page_source
            sel_response = HtmlResponse(
                url=response.url,
                body=html.encode('utf-8'),
                encoding='utf-8'
            )

            # Extract basic movie information
            movie_id_from_url = response.url.split('/')[-1] if response.url.split('/')[-1] else ''
            imdb_id = f'goojara_{movie_id_from_url}' # Create a unique ID for this source

            title_element = sel_response.css('h1')
            title_text = title_element.css('::text').get()

            title = 'Unknown Title'
            year = None
            if title_text:
                # Try to parse title and year (e.g., "Movie Title (2023)")
                title_match = re.match(r'(.+?)\s*\((\d{4})\)', title_text.strip())
                if title_match:
                    title = title_match.group(1).strip()
                    year = int(title_match.group(2))
                else:
                    title = title_text.strip()

            # Extract synopsis - assuming it's the text immediately following the h1 tag
            synopsis = title_element.xpath('./following-sibling::text()').get()
            synopsis = synopsis.strip() if synopsis else ''

            # Extract poster URL
            poster_img_tag = sel_response.css('img')
            poster_src = poster_img_tag.css('::attr(src)').get()
            poster_url = response.urljoin(poster_src) if poster_src else ''

            # Find streaming link elements
            # The selector 'a[href*="/go.php"]' targets links that likely lead to streaming endpoints.
            stream_links_elements = sel_response.css('a[href*="/go.php"]')

            if not stream_links_elements:
                self.logger.warning(f'No streaming link elements found for movie: "{title}" ({response.url})')
                # Still yield the movie even without streaming links
                item = MovieItem()
                item['source_site'] = 'goojara.to'
                item['source_url'] = response.url
                item['imdb_id'] = imdb_id
                item['title'] = title
                item['year'] = year
                item['synopsis'] = synopsis
                item['poster_url'] = poster_url
                item['stream_url'] = ''
                item['server_name'] = 'Unknown'
                item['quality'] = 'Unknown'
                item['language'] = 'EN'
                yield item
                return

            # Organize links by server type (e.g., 'wootly', 'dood')
            server_links_map = {'wootly': [], 'dood': [], 'other': []} # Example servers, adjust based on actual site

            for link_elem in stream_links_elements:
                link_text = link_elem.css('::text').get()
                link_href = link_elem.css('::attr(href)').get()

                if not link_text or not link_href:
                    continue

                text_lower = link_text.lower()

                if 'dood' in text_lower:
                    server_links_map['dood'].append((link_href, link_text, 'Dood'))
                elif 'wootly' in text_lower:
                    server_links_map['wootly'].append((link_href, link_text, 'Wootly'))
                else:
                    # Catch other servers
                    server_links_map['other'].append((link_href, link_text, 'Other'))

            # Process each found streaming link
            all_valid_streaming_links = []
            movie_detail_page_url = self.driver.current_url # Store current URL to return later

            for server_type, links_data in server_links_map.items():
                for link_href, link_text, server_name in links_data:
                    try:
                        quality = self._extract_quality(link_text) # Helper to get video quality
                        full_redirect_url = response.urljoin(link_href)

                        # Navigate to the redirect URL to get the final stream URL
                        self.driver.get(full_redirect_url)
                        time.sleep(5) # Wait for the redirect and potential ad/player load

                        final_stream_url = self.driver.current_url

                        # Validate the final URL to ensure it's a valid stream link
                        # This checks for common indicators of error pages or non-stream URLs
                        invalid_patterns = ['goojara.to', '404', 'error', 'ads'] # Add any other known invalid patterns
                        is_valid = (
                            final_stream_url and
                            len(final_stream_url) > 20 and # Basic length check
                            not any(p in final_stream_url.lower() for p in invalid_patterns)
                        )

                        if is_valid:
                            all_valid_streaming_links.append({
                                'url': final_stream_url,
                                'server': server_name,
                                'quality': quality,
                                'language': 'EN' # Assuming English, can be determined if available
                            })
                        else:
                            self.logger.warning(f'Invalid stream URL found for {server_name} ({title}): {final_stream_url}')

                        # Return to the movie detail page to process the next link
                        self.driver.get(movie_detail_page_url)
                        time.sleep(2)

                    except Exception as e:
                        self.logger.warning(f'Failed to process link for {server_name} ({title}): {e}')
                        # Attempt to return to the movie detail page even if an error occurred
                        try:
                            self.driver.get(movie_detail_page_url)
                            time.sleep(2)
                        except:
                            pass # If returning fails, just log and continue

            # Yield MovieItem for each valid streaming link found
            if all_valid_streaming_links:
                for stream_link in all_valid_streaming_links:
                    item = MovieItem()
                    item['source_site'] = 'goojara.to'
                    item['source_url'] = response.url # The URL of the movie detail page on Goojara
                    item['imdb_id'] = imdb_id
                    item['title'] = title
                    item['year'] = year
                    item['synopsis'] = synopsis
                    item['poster_url'] = poster_url
                    item['stream_url'] = stream_link['url']
                    item['server_name'] = stream_link['server']
                    item['quality'] = stream_link['quality']
                    item['language'] = stream_link['language']

                    self.logger.info(f'✓ Yielding movie: "{title}" ({stream_link["server"]} - {stream_link["quality"]})')
                    yield item
            else:
                self.logger.warning(f'No valid streaming links found for movie: "{title}" ({response.url})')
                # Still yield the movie even without valid streaming links
                item = MovieItem()
                item['source_site'] = 'goojara.to'
                item['source_url'] = response.url
                item['imdb_id'] = imdb_id
                item['title'] = title
                item['year'] = year
                item['synopsis'] = synopsis
                item['poster_url'] = poster_url
                item['stream_url'] = ''
                item['server_name'] = 'Unknown'
                item['quality'] = 'Unknown'
                item['language'] = 'EN'
                yield item

        except Exception as e:
            self.logger.error(f'Error parsing movie page {response.url}: {e}')

    def _extract_quality(self, link_text):
        """
        Helper method to extract video quality (e.g., HD, 720p, SD) from the text
        associated with a streaming link.

        Args:
            link_text (str): The text content of the link element.

        Returns:
            str: The detected quality string.
        """
        if not link_text:
            return 'SD' # Default to SD if no text is available

        text_upper = link_text.upper()
        if 'HD' in text_upper or '1080' in text_upper:
            return 'HD'
        elif '720' in text_upper:
            return '720p'
        elif 'DVD' in text_upper:
            return 'DVD'
        # Add more conditions if other quality indicators are found (e.g., '4K', '2160')
        return 'SD' # Default if no specific quality found
