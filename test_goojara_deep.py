"""
Deep investigation of Goojara to find more movie discovery methods
"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

def analyze_homepage(driver):
    """Analyze homepage structure in detail"""
    print("\n" + "="*60)
    print("ANALYZING HOMEPAGE STRUCTURE")
    print("="*60)
    
    driver.get('https://ww1.goojara.to/')
    time.sleep(5)
    
    # Get all text content
    body_text = driver.find_element(By.TAG_NAME, 'body').text
    print(f"\nPage text preview (first 500 chars):\n{body_text[:500]}")
    
    # Find navigation elements
    nav_elements = driver.find_elements(By.TAG_NAME, 'nav')
    print(f"\nNavigation elements found: {len(nav_elements)}")
    
    # Find all unique link patterns
    links = driver.find_elements(By.TAG_NAME, 'a')
    all_hrefs = [link.get_attribute('href') for link in links if link.get_attribute('href')]
    
    # Categorize links
    patterns = {
        'movie_detail': [],
        'search': [],
        'filter': [],
        'other': []
    }
    
    for href in all_hrefs:
        if re.search(r'/m[a-zA-Z0-9]{5,7}$', href):
            patterns['movie_detail'].append(href)
        elif 'search' in href.lower() or 'query' in href.lower():
            patterns['search'].append(href)
        elif any(x in href for x in ['filter', 'sort', 'genre', 'year', 'category']):
            patterns['filter'].append(href)
        else:
            patterns['other'].append(href)
    
    print(f"\nLink patterns found:")
    for pattern, urls in patterns.items():
        unique = list(set(urls))
        print(f"  {pattern}: {len(unique)} unique URLs")
        if unique and pattern != 'other':
            for url in unique[:5]:
                print(f"    - {url}")
    
    # Check for search functionality
    search_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="search"], input[name*="search"], input[placeholder*="search"]')
    print(f"\nSearch inputs found: {len(search_inputs)}")
    
    # Look for buttons/menus
    buttons = driver.find_elements(By.TAG_NAME, 'button')
    print(f"Buttons found: {len(buttons)}")
    
    # Check page source for API calls or data
    page_source = driver.page_source
    api_patterns = re.findall(r'(api|fetch|ajax|load)["\']?\s*:\s*["\']([^"\']+)', page_source, re.IGNORECASE)
    if api_patterns:
        print(f"\nPotential API endpoints found:")
        for pattern in api_patterns[:5]:
            print(f"  - {pattern}")

def test_search(driver):
    """Test if search functionality works"""
    print("\n" + "="*60)
    print("TESTING SEARCH FUNCTIONALITY")
    print("="*60)
    
    driver.get('https://ww1.goojara.to/')
    time.sleep(3)
    
    # Try to find and use search
    try:
        search_inputs = driver.find_elements(By.CSS_SELECTOR, 'input[type="search"], input[name*="search"], input[placeholder*="Search"]')
        if search_inputs:
            search_input = search_inputs[0]
            search_input.send_keys('action')
            time.sleep(2)
            
            # Try to submit
            search_input.submit()
            time.sleep(3)
            
            # Check results
            links = driver.find_elements(By.TAG_NAME, 'a')
            movie_links = [l.get_attribute('href') for l in links if l.get_attribute('href') and re.search(r'/m[a-zA-Z0-9]{5,7}$', l.get_attribute('href'))]
            print(f"✓ Search executed, found {len(set(movie_links))} movie links")
        else:
            print("✗ No search input found")
    except Exception as e:
        print(f"✗ Search failed: {e}")

def test_scroll_loading(driver):
    """Test if scrolling loads more content"""
    print("\n" + "="*60)
    print("TESTING INFINITE SCROLL")
    print("="*60)
    
    driver.get('https://ww1.goojara.to/')
    time.sleep(3)
    
    # Get initial movie count
    links = driver.find_elements(By.TAG_NAME, 'a')
    initial_movies = len([l for l in links if l.get_attribute('href') and re.search(r'/m[a-zA-Z0-9]{5,7}$', l.get_attribute('href'))])
    print(f"Initial movies: {initial_movies}")
    
    # Scroll down multiple times
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        links = driver.find_elements(By.TAG_NAME, 'a')
        current_movies = len([l for l in links if l.get_attribute('href') and re.search(r'/m[a-zA-Z0-9]{5,7}$', l.get_attribute('href'))])
        print(f"After scroll {i+1}: {current_movies} movies")
        
        if current_movies > initial_movies:
            print("✓ Infinite scroll detected!")
            return True
    
    print("✗ No infinite scroll detected")
    return False

def discover_movie_urls(driver):
    """Try to discover more movie URLs through various methods"""
    print("\n" + "="*60)
    print("DISCOVERING MORE MOVIE URLS")
    print("="*60)
    
    all_movies = set()
    
    # Method 1: Try different page numbers
    print("\nMethod 1: Testing pagination...")
    for page in range(1, 11):
        try:
            url = f'https://ww1.goojara.to/?page={page}'
            driver.get(url)
            time.sleep(2)
            
            links = driver.find_elements(By.TAG_NAME, 'a')
            movies = [l.get_attribute('href') for l in links if l.get_attribute('href') and re.search(r'/m[a-zA-Z0-9]{5,7}$', l.get_attribute('href'))]
            new_movies = set(movies) - all_movies
            all_movies.update(movies)
            
            print(f"  Page {page}: {len(new_movies)} new movies (total: {len(all_movies)})")
            
            if len(new_movies) == 0 and page > 2:
                print(f"  No new movies found, stopping at page {page}")
                break
        except Exception as e:
            print(f"  Page {page} failed: {e}")
            break
    
    # Method 2: Try browsing by first letter
    print("\nMethod 2: Testing alphabetical browsing...")
    for letter in ['a', 'b', 'c', 't', 'm']:
        try:
            url = f'https://ww1.goojara.to/browse/{letter}'
            driver.get(url)
            time.sleep(2)
            
            links = driver.find_elements(By.TAG_NAME, 'a')
            movies = [l.get_attribute('href') for l in links if l.get_attribute('href') and re.search(r'/m[a-zA-Z0-9]{5,7}$', l.get_attribute('href'))]
            new_movies = set(movies) - all_movies
            all_movies.update(movies)
            
            print(f"  Letter '{letter}': {len(new_movies)} new movies")
        except Exception as e:
            print(f"  Letter '{letter}' failed: {e}")
    
    return all_movies

def main():
    print("Starting deep Goojara investigation...")
    driver = setup_driver()
    
    try:
        analyze_homepage(driver)
        test_search(driver)
        has_scroll = test_scroll_loading(driver)
        all_movies = discover_movie_urls(driver)
        
        print("\n" + "="*60)
        print("FINAL SUMMARY")
        print("="*60)
        print(f"Total unique movies discovered: {len(all_movies)}")
        print(f"Infinite scroll: {'Yes' if has_scroll else 'No'}")
        
        if all_movies:
            print("\nSample discovered movies:")
            for movie in list(all_movies)[:10]:
                print(f"  - {movie}")
        
    finally:
        driver.quit()
    
    print("\nDeep investigation complete!")

if __name__ == '__main__':
    main()
