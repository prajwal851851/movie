#!/usr/bin/env python3
"""
Quick test script to verify the regex pattern matches Goojara movie URLs correctly.
Run this to confirm the pattern is working before deploying the spider.
"""

import re

def test_movie_url_pattern():
    """Test that the regex pattern correctly matches Goojara movie URLs."""
    
    # Real movie URLs from the Goojara website
    test_urls = [
        '/mMG6zJ',  # Five Nights at Freddy's 2
        '/mDJXjL',  # Nuremberg
        '/mdne8R',  # Springsteen
        '/mllenX',  # Sisu: Road to Revenge
        '/mOeAXp',  # Now You See Me
        '/mabeR1',  # Wake Up Dead Man
        '/mLRq84',  # The Running Man
        '/m5QvXN',  # Die My Love
        '/mJRNdk',  # Dog Patrol
        '/m2a0rz',  # Anemone
        '/mrARxJ',  # My Secret Santa
        '/myPGE2',  # Oh. What. Fun.
        '/mvpeQz',  # The Family McMullen
        '/mjPear',  # TRON: Ares
        '/m76rWj',  # Predator: Badlands
        '/m06Av4',  # The Age of Disclosure
        '/mZDwdm',  # The Family Plan 2
        '/mabeRR',  # Bugonia
        '/mLRq8w',  # Playdate
        '/m5QvX5',  # One Battle After Another
    ]
    
    # URLs that should NOT match (false positives)
    non_movie_urls = [
        '/',              # Home
        '/watch-movies',  # Category page
        '/watch-series',  # Series page
        '/m',             # Too short
        '/movie',         # Wrong pattern
        '/m12345',        # Only 5 digits (but should match!)
        '/m123456789',    # Too long
    ]
    
    # The corrected pattern: /m followed by 5-6 alphanumeric characters
    pattern = r'^/m[a-zA-Z0-9]{5,6}$'
    
    print("="*70)
    print("TESTING MOVIE URL PATTERN")
    print("="*70)
    print(f"\nPattern: {pattern}\n")
    
    print("-"*70)
    print("Testing VALID movie URLs (should all match):")
    print("-"*70)
    
    passed = 0
    failed = 0
    
    for url in test_urls:
        match = re.match(pattern, url)
        status = "✅ PASS" if match else "❌ FAIL"
        print(f"{status} | {url} | Length after /m: {len(url[2:])}")
        if match:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResult: {passed} passed, {failed} failed out of {len(test_urls)} URLs")
    
    print("\n" + "-"*70)
    print("Testing NON-movie URLs (should NOT match):")
    print("-"*70)
    
    false_positives = 0
    true_negatives = 0
    
    for url in non_movie_urls:
        match = re.match(pattern, url)
        # For non-movie URLs, we want NO match
        if not match:
            status = "✅ PASS (correctly rejected)"
            true_negatives += 1
        else:
            status = "❌ FAIL (false positive)"
            false_positives += 1
        
        print(f"{status} | {url}")
    
    print(f"\nResult: {true_negatives} correctly rejected, {false_positives} false positives")
    
    print("\n" + "="*70)
    if failed == 0 and false_positives == 0:
        print("🎉 ALL TESTS PASSED! The pattern is working correctly.")
        print("="*70)
        return True
    else:
        print("⚠️  SOME TESTS FAILED! Please review the pattern.")
        print("="*70)
        return False

if __name__ == "__main__":
    success = test_movie_url_pattern()
    exit(0 if success else 1)
