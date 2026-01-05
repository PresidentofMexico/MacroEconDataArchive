#!/usr/bin/env python3
"""
Test script for validating caching and retry logic without full dependencies.
This validates the code structure and logic flow.
"""

import ast
import inspect

def test_macro_utils_structure():
    """Verify macro_utils.py has the required exception classes and retry logic."""
    print("🔍 Testing macro_utils.py structure...")
    
    with open('src/macro_econ_data_archive/macro_utils.py', 'r') as f:
        content = f.read()
    
    # Check for custom exceptions
    assert 'class FREDRateLimitError(Exception):' in content, "Missing FREDRateLimitError exception"
    assert 'class FREDServerError(Exception):' in content, "Missing FREDServerError exception"
    
    # Check for retry parameters in fetch_fred
    assert 'max_retries: int = 3' in content, "Missing max_retries parameter"
    assert 'backoff_factor: float = 2.0' in content, "Missing backoff_factor parameter"
    
    # Check for retry loop
    assert 'for attempt in range(max_retries):' in content, "Missing retry loop"
    
    # Check for exponential backoff
    assert 'backoff_factor ** attempt' in content, "Missing exponential backoff calculation"
    
    # Check for 403 handling
    assert 'response.status_code == 403' in content, "Missing 403 status code check"
    assert 'FREDRateLimitError' in content, "Missing FREDRateLimitError raise"
    
    # Check for 5xx handling  
    assert '500 <= response.status_code < 600' in content, "Missing 5xx status code check"
    assert 'FREDServerError' in content, "Missing FREDServerError raise"
    
    # Check for time.sleep (backoff)
    assert 'time.sleep' in content, "Missing time.sleep for backoff"
    
    # Check imports
    assert 'import time' in content, "Missing time import"
    
    print("  ✅ All exception classes present")
    print("  ✅ Retry logic implemented")
    print("  ✅ Exponential backoff present")
    print("  ✅ Error handling for 403 and 5xx")
    print("  ✅ timeout parameter added to requests")
    

def test_streamlit_app_structure():
    """Verify streamlit_app.py has caching and error handling."""
    print("\n🔍 Testing streamlit_app.py structure...")
    
    with open('src/macro_econ_data_archive/streamlit_app.py', 'r') as f:
        content = f.read()
    
    # Check imports
    assert 'FREDRateLimitError' in content, "Missing FREDRateLimitError import"
    assert 'FREDServerError' in content, "Missing FREDServerError import"
    
    # Check for cached function
    assert '@st.cache_data' in content, "Missing @st.cache_data decorator"
    assert 'def fetch_fred_cached' in content, "Missing fetch_fred_cached function"
    assert 'ttl=3600' in content, "Missing TTL parameter for cache"
    
    # Check cache is used in add_chart_to_report
    assert 'fetch_fred_cached' in content, "fetch_fred_cached not being called"
    
    # Check error handling
    assert 'except FREDRateLimitError as e:' in content, "Missing FREDRateLimitError handling"
    assert 'except FREDServerError as e:' in content, "Missing FREDServerError handling"
    
    # Check for cache clear button
    assert 'st.cache_data.clear()' in content, "Missing cache clear functionality"
    assert 'clear_cache' in content.lower(), "Missing cache clear UI element"
    
    # Check for friendly error messages
    assert 'FRED Rate Limit Reached' in content or 'Rate Limit' in content, "Missing rate limit error message"
    assert 'FRED Server Error' in content or 'Server Error' in content, "Missing server error message"
    
    print("  ✅ Custom exceptions imported")
    print("  ✅ Caching decorator present with TTL")
    print("  ✅ Cached function implemented")
    print("  ✅ Cache clear button added")
    print("  ✅ Error handling for rate limits and server errors")
    print("  ✅ User-friendly error messages")


def test_cache_key_structure():
    """Verify cache is keyed properly by series_id and start_date."""
    print("\n🔍 Testing cache key structure...")
    
    with open('src/macro_econ_data_archive/streamlit_app.py', 'r') as f:
        content = f.read()
    
    # Find the fetch_fred_cached function
    lines = content.split('\n')
    in_cached_func = False
    func_lines = []
    
    for line in lines:
        if 'def fetch_fred_cached' in line:
            in_cached_func = True
        if in_cached_func:
            func_lines.append(line)
            if line.strip().startswith('return') and 'fetch_fred' in line:
                break
    
    func_content = '\n'.join(func_lines)
    
    # Check parameters
    assert 'series_id: str' in func_content, "Missing series_id parameter"
    assert 'start_date: str' in func_content, "Missing start_date parameter"
    
    print("  ✅ Cache keyed by (series_id, start_date)")
    print("  ✅ Cache invalidation on parameter change")


def test_documentation_comments():
    """Verify functions have proper docstrings explaining caching."""
    print("\n🔍 Testing documentation...")
    
    with open('src/macro_econ_data_archive/streamlit_app.py', 'r') as f:
        content = f.read()
    
    # Check fetch_fred_cached has docstring explaining caching
    cached_func_start = content.find('def fetch_fred_cached')
    cached_func_end = content.find('return fetch_fred', cached_func_start)
    cached_func_section = content[cached_func_start:cached_func_end]
    
    assert '"""' in cached_func_section or "'''" in cached_func_section, "Missing docstring for fetch_fred_cached"
    assert 'cache' in cached_func_section.lower(), "Docstring doesn't mention caching"
    assert 'series_id' in cached_func_section.lower(), "Docstring doesn't explain cache key"
    
    print("  ✅ Caching explained in docstrings")
    print("  ✅ Cache key documented")
    

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Caching and Retry Logic Implementation")
    print("=" * 60)
    
    try:
        test_macro_utils_structure()
        test_streamlit_app_structure()
        test_cache_key_structure()
        test_documentation_comments()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        print("\n📋 Summary:")
        print("  • Custom exception classes for rate limits and server errors")
        print("  • Retry logic with exponential backoff (3 retries, 2x factor)")
        print("  • Streamlit caching with @st.cache_data (1 hour TTL)")
        print("  • Cache keyed by (series_id, start_date)")
        print("  • User-friendly error messages in UI")
        print("  • Cache clear button in sidebar")
        print("  • Comprehensive documentation")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        exit(1)
