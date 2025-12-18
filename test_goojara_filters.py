"""
Test Goojara filter pages to find more movies
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

def test_filter_page(driver, url, name):
    """Test filter pages and extract category links"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        driver.get(url)
        time.sleep(5)
        
        # Get all links
        links = driver.find_elements(By.TAG_NAME, 'a')
        all_hrefs = [link.get_attribute('href') for link in links if link.get_attribute('href')]
        
        # Find movie links
        movie_links = [href for href in all_hrefs if href and re.search(r'/m[a-zA-Z0-9]{5,7}$', href)]
        
        # Find category/filter links
        category_links = [href for href in all_hrefs if href and not re.search(r'/m[a-zA-Z0-9]{5,7}$', href) and 'goojara.to' in href]
        
        print(f"✓ Page loaded")
        print(f"  Movie links: {len(set(movie_links))}")
        print(f"  Category links: {len(set(category_links))}")
        
        # Show unique category patterns
        unique_categories = set(category_links)
        if unique_categories:
            print(f"\n  Category URLs found:")
            for cat in sorted(unique_categories)[:20]:
                print(f"    - {cat}")
        
        return list(set(movie_links)), list(unique_categories)
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return [], []

def test_category_urls(driver, category_urls):
    """Test discovered category URLs to find movies"""
    print(f"\n{'='*60}")
    print("TESTING CATEGORY URLS FOR MOVIES")
    print('='*60)
    
    all_movies = set()
    working_urls = []
    
    for url in category_urls[:30]:  # Test first 30
        try:
            driver.get(url)
            time.sleep(3)
            
            links = driver.find_elements(By.TAG_NAME, 'a')
            movie_links = [l.get_attribute('href') for l in links if l.get_attribute('href') and re.search(r'/m[a-zA-Z0-9]{5,7}$', l.get_attribute('href'))]
            
            unique_movies = set(movie_links)
            new_movies = unique_movies - all_movies
            
            if new_movies:
                all_movies.update(new_movies)
                working_urls.append(url)
                print(f"✓ {url}")
                print(f"  Found {len(new_movies)} new movies (total: {len(all_movies)})")
            
        except Exception as e:
            print(f"✗ {url}: {e}")
    
    return all_movies, working_urls

def main():
    print("Testing Goojara filter pages...")
    driver = setup_driver()
    
    all_discovered_movies = set()
    all_working_urls = []
    
    # Test filter pages
    filter_pages = [
        ('https://ww1.goojara.to/watch-trends-year', 'Year Trends'),
        ('https://ww1.goojara.to/watch-trends-genre', 'Genre Trends'),
        ('https://ww1.goojara.to/watch-trends', 'General Trends'),
    ]
    
    all_category_urls = []
    
    for url, name in filter_pages:
        movies, categories = test_filter_page(driver, url, name)
        all_discovered_movies.update(movies)
        all_category_urls.extend(categories)
    
    # Remove duplicates
    unique_category_urls = list(set(all_category_urls))
    print(f"\n{'='*60}")
    print(f"Total unique category URLs discovered: {len(unique_category_urls)}")
    print('='*60)
    
    # Test category URLs
    if unique_category_urls:
        category_movies, working_urls = test_category_urls(driver, unique_category_urls)
        all_discovered_movies.update(category_movies)
        all_working_urls.extend(working_urls)
    
    # Summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print('='*60)
    print(f"Total unique movies discovered: {len(all_discovered_movies)}")
    print(f"Working category URLs: {len(all_working_urls)}")
    
    if all_working_urls:
        print("\nWorking URLs to use in spider:")
        for url in all_working_urls[:20]:
            print(f"  '{url}',")
    
    driver.quit()
    print("\nFilter page investigation complete!")

if __name__ == '__main__':
    main()
