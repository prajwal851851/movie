"""
Test script to investigate Goojara site structure and find working URLs
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import re

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def test_url(driver, url, name):
    """Test if a URL works and find movie links"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        driver.get(url)
        time.sleep(3)
        
        # Get page source
        html = driver.page_source
        
        # Find all links
        links = driver.find_elements(By.TAG_NAME, 'a')
        all_hrefs = [link.get_attribute('href') for link in links if link.get_attribute('href')]
        
        # Filter for movie links (pattern: /mXXXXXX)
        movie_links = [href for href in all_hrefs if href and re.search(r'/m[a-zA-Z0-9]{5,7}$', href)]
        unique_movies = list(set(movie_links))
        
        print(f"✓ Page loaded successfully")
        print(f"  Total links: {len(all_hrefs)}")
        print(f"  Movie links found: {len(unique_movies)}")
        
        if unique_movies:
            print(f"  Sample movies:")
            for movie in unique_movies[:5]:
                print(f"    - {movie}")
        
        # Look for pagination links
        pagination_links = [href for href in all_hrefs if href and ('page=' in href or '/page/' in href)]
        if pagination_links:
            print(f"  Pagination found: {len(set(pagination_links))} unique page links")
            for page in list(set(pagination_links))[:3]:
                print(f"    - {page}")
        
        # Look for category/genre links
        category_links = [href for href in all_hrefs if href and any(x in href for x in ['/genre/', '/category/', '/year/', '/movies'])]
        if category_links:
            print(f"  Category links found: {len(set(category_links))}")
            for cat in list(set(category_links))[:10]:
                print(f"    - {cat}")
        
        return True, len(unique_movies)
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False, 0

def main():
    print("Starting Goojara site structure investigation...")
    driver = setup_driver()
    
    # Test different URL patterns
    test_urls = [
        ('https://ww1.goojara.to/', 'Homepage'),
        ('https://ww1.goojara.to/trending', 'Trending'),
        ('https://ww1.goojara.to/popular', 'Popular'),
        ('https://ww1.goojara.to/latest', 'Latest'),
        ('https://ww1.goojara.to/movies', 'Movies'),
        ('https://ww1.goojara.to/?page=2', 'Homepage Page 2'),
        ('https://goojara.to/', 'Main Domain'),
        ('https://goojara.to/trending', 'Main Domain Trending'),
        ('https://www.goojara.to/', 'WWW Domain'),
    ]
    
    results = []
    for url, name in test_urls:
        success, movie_count = test_url(driver, url, name)
        results.append((name, url, success, movie_count))
        time.sleep(2)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for name, url, success, count in results:
        status = "✓" if success else "✗"
        print(f"{status} {name}: {count} movies - {url}")
    
    driver.quit()
    print("\nInvestigation complete!")

if __name__ == '__main__':
    main()
