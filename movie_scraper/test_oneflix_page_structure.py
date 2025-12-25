# test_oneflix_page_structure.py
"""
Diagnostic tool to see what's actually on a 1Flix movie page
This helps debug why the spider isn't finding server buttons
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

def analyze_1flix_page(movie_url):
    """Analyze the structure of a 1Flix movie page"""
    
    print(f"\n{'='*80}")
    print(f"🔍 1FLIX PAGE STRUCTURE ANALYZER")
    print(f"{'='*80}")
    print(f"URL: {movie_url}\n")
    
    # Setup Chrome (NOT headless so you can see what's happening)
    chrome_options = Options()
    # Comment out headless to see the browser
    # chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("📥 Loading page...")
        driver.get(movie_url)
        time.sleep(8)  # Wait for everything to load
        
        print("✓ Page loaded\n")
        
        # Scroll to load dynamic content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        # Get title
        print("📽️  MOVIE INFORMATION")
        print("-" * 80)
        try:
            title = driver.find_element(By.CSS_SELECTOR, "h2.heading-name a, h1").text
            print(f"Title: {title}")
        except:
            print("Title: Could not extract")
        
        # Analyze server buttons
        print(f"\n🎮 SERVER BUTTONS ANALYSIS")
        print("-" * 80)
        
        # Method 1: data-linkid
        print("\n1️⃣  Checking for [data-linkid] elements...")
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, "[data-linkid]")
            if elements:
                print(f"   ✓ Found {len(elements)} elements with data-linkid")
                for i, elem in enumerate(elements[:5], 1):
                    text = elem.text.strip() or elem.get_attribute('title') or 'No text'
                    linkid = elem.get_attribute('data-linkid')
                    tag = elem.tag_name
                    print(f"   {i}. <{tag}> text='{text}' data-linkid='{linkid}'")
            else:
                print("   ✗ No [data-linkid] elements found")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Method 2: Server list items
        print("\n2️⃣  Checking for server list items...")
        selectors = [
            ".server-item",
            ".servers-list li",
            "ul.servers li",
            ".server-list li"
        ]
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   ✓ Found {len(elements)} elements with '{selector}'")
                    for i, elem in enumerate(elements[:3], 1):
                        text = elem.text.strip()[:50]
                        print(f"   {i}. {text}")
                    break
            except:
                continue
        else:
            print("   ✗ No server list items found")
        
        # Method 3: Any button/link with "server" or "cloud"
        print("\n3️⃣  Checking for buttons/links containing 'server' or 'cloud'...")
        try:
            elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'server') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'cloud')]")
            if elements:
                print(f"   ✓ Found {len(elements)} elements mentioning server/cloud")
                for i, elem in enumerate(elements[:5], 1):
                    text = elem.text.strip()[:50]
                    tag = elem.tag_name
                    print(f"   {i}. <{tag}> {text}")
            else:
                print("   ✗ No elements found")
        except Exception as e:
            print(f"   ✗ Error: {e}")
        
        # Check for iframes
        print(f"\n📺 IFRAME ANALYSIS")
        print("-" * 80)
        
        iframe_selectors = [
            "iframe",
            "iframe#iframe-embed",
            "iframe[src*='embed']",
            "iframe[src*='player']",
            ".player-container iframe"
        ]
        
        for selector in iframe_selectors:
            try:
                iframes = driver.find_elements(By.CSS_SELECTOR, selector)
                if iframes:
                    print(f"\n✓ Found {len(iframes)} iframe(s) with '{selector}'")
                    for i, iframe in enumerate(iframes, 1):
                        src = iframe.get_attribute('src') or 'No src'
                        print(f"   {i}. {src[:80]}...")
            except:
                continue
        
        # Print page source snippet
        print(f"\n📄 PAGE SOURCE ANALYSIS")
        print("-" * 80)
        
        page_source = driver.page_source.lower()
        
        keywords = ['data-linkid', 'server', 'upcloud', 'megacloud', 'vidcloud', 'iframe', 'embed', 'player']
        print("\nKeyword occurrences in page source:")
        for keyword in keywords:
            count = page_source.count(keyword)
            status = "✓" if count > 0 else "✗"
            print(f"   {status} '{keyword}': {count} times")
        
        # Save HTML to file for inspection
        print(f"\n💾 Saving page HTML...")
        with open('1flix_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("   ✓ Saved to: 1flix_page_debug.html")
        
        # Interactive mode
        print(f"\n{'='*80}")
        print("🔍 BROWSER WINDOW IS OPEN")
        print("   You can now inspect the page manually")
        print("   Press Enter when ready to close...")
        print(f"{'='*80}")
        input()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n✓ Browser closed")

if __name__ == "__main__":
    # Test with a failing movie from your logs
    test_url = "https://1flix.to/movie/watch-ordinary-justice-140583"
    
    print("\n" + "="*80)
    print("This tool will:")
    print("  1. Open the movie page in a visible browser")
    print("  2. Analyze all possible server button locations")
    print("  3. Check for iframes")
    print("  4. Save the HTML for inspection")
    print("  5. Let you manually inspect before closing")
    print("="*80)
    
    input("\nPress Enter to start analysis...")
    
    analyze_1flix_page(test_url)
    
    print("\n" + "="*80)
    print("✓ Analysis complete!")
    print("  - Check the console output above")
    print("  - Review 1flix_page_debug.html in your text editor")
    print("  - Look for patterns we can use in the spider")
    print("="*80)