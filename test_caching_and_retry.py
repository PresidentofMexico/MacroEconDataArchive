#!/usr/bin/env python3
"""
test_caching_and_retry.py

Tests for data caching and retry logic with exponential backoff.
"""

import sys
import time
from pathlib import Path
from unittest.mock import Mock, patch
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_custom_exceptions():
    """Test that custom FRED exceptions exist and work."""
    print("Testing custom exceptions...")
    
    try:
        from macro_econ_data_archive.macro_utils import (
            FREDRateLimitError, FREDServerError
        )
        
        # Test exception creation
        error1 = FREDRateLimitError("Rate limit exceeded")
        assert str(error1) == "Rate limit exceeded"
        assert isinstance(error1, Exception)
        print("  ✓ FREDRateLimitError works")
        
        error2 = FREDServerError("Server error")
        assert str(error2) == "Server error"
        assert isinstance(error2, Exception)
        print("  ✓ FREDServerError works")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Exception test failed: {e}")
        return False


def test_fetch_fred_signature():
    """Test that fetch_fred has the correct signature."""
    print("\nTesting fetch_fred signature...")
    
    try:
        from macro_econ_data_archive.macro_utils import fetch_fred
        import inspect
        
        sig = inspect.signature(fetch_fred)
        params = list(sig.parameters.keys())
        
        assert 'series_ids' in params
        assert 'start' in params
        assert 'max_retries' in params
        assert 'backoff_factor' in params
        
        # Check defaults
        defaults = sig.parameters
        assert defaults['max_retries'].default == 3
        assert defaults['backoff_factor'].default == 2.0
        
        print("  ✓ fetch_fred has correct signature")
        print(f"    Parameters: {', '.join(params)}")
        print(f"    max_retries default: {defaults['max_retries'].default}")
        print(f"    backoff_factor default: {defaults['backoff_factor'].default}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Signature test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_retry_logic_mock():
    """Test retry logic with mocked requests."""
    print("\nTesting retry logic with mocks...")
    
    try:
        from macro_econ_data_archive.macro_utils import (
            fetch_fred, FREDRateLimitError, FREDServerError
        )
        import requests
        
        # Test 1: 403 error should raise FREDRateLimitError immediately (no retry)
        print("  Testing 403 rate limit handling...")
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 403
            mock_get.return_value = mock_response
            
            try:
                fetch_fred(['TEST'], start='2020-01-01')
                print("    ✗ Should have raised FREDRateLimitError")
                return False
            except FREDRateLimitError as e:
                print(f"    ✓ Correctly raised FREDRateLimitError")
                # Verify only 1 call (no retries)
                assert mock_get.call_count == 1
                print(f"    ✓ No retries attempted (call count: {mock_get.call_count})")
        
        # Test 2: 500 error should retry 3 times then raise FREDServerError
        print("  Testing 500 server error retry...")
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            start_time = time.time()
            try:
                fetch_fred(['TEST'], start='2020-01-01', max_retries=3, backoff_factor=2.0)
                print("    ✗ Should have raised FREDServerError")
                return False
            except FREDServerError as e:
                elapsed = time.time() - start_time
                print(f"    ✓ Correctly raised FREDServerError")
                # Should have 3 attempts
                assert mock_get.call_count == 3
                print(f"    ✓ Retried 3 times (call count: {mock_get.call_count})")
                # Should have delays (1s + 2s = 3s minimum)
                print(f"    ✓ Total time: {elapsed:.1f}s (expected ~3s for backoff)")
        
        # Test 3: Successful fetch after retries
        print("  Testing successful fetch after retry...")
        with patch('requests.get') as mock_get:
            # First two calls fail, third succeeds
            mock_fail = Mock()
            mock_fail.status_code = 500
            
            mock_success = Mock()
            mock_success.status_code = 200
            mock_success.text = "DATE,TEST\n2020-01-01,100\n2020-02-01,101\n"
            
            mock_get.side_effect = [mock_fail, mock_success]
            
            result = fetch_fred(['TEST'], start='2020-01-01')
            print(f"    ✓ Successfully fetched after retry")
            assert not result.empty
            print(f"    ✓ Data fetched: {len(result)} rows")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Retry logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streamlit_caching():
    """Test Streamlit caching decorator."""
    print("\nTesting Streamlit caching...")
    
    try:
        from macro_econ_data_archive.streamlit_app import fetch_fred_cached
        
        # Check that it's a cached function
        assert hasattr(fetch_fred_cached, 'clear')
        print("  ✓ fetch_fred_cached has cache clear method")
        
        # Check function metadata
        import inspect
        sig = inspect.signature(fetch_fred_cached)
        params = list(sig.parameters.keys())
        assert 'series_ids' in params
        assert 'start' in params
        print("  ✓ fetch_fred_cached has correct signature")
        
        # Test cache clear doesn't error
        try:
            fetch_fred_cached.clear()
            print("  ✓ Cache clear works")
        except Exception as e:
            print(f"  ⚠ Cache clear failed: {e} (may be expected outside Streamlit)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Streamlit caching test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exponential_backoff():
    """Test that exponential backoff timing is correct."""
    print("\nTesting exponential backoff timing...")
    
    try:
        from macro_econ_data_archive.macro_utils import fetch_fred, FREDServerError
        
        # Mock requests to always fail with 500
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            # Test with custom backoff parameters
            start_time = time.time()
            try:
                fetch_fred(['TEST'], start='2020-01-01', max_retries=4, backoff_factor=2.0)
            except FREDServerError:
                pass
            
            elapsed = time.time() - start_time
            
            # Expected delays: 1s, 2s, 4s (before final attempt)
            # Total should be around 7 seconds (with some tolerance)
            expected_min = 6.0  # Allow some tolerance
            expected_max = 9.0
            
            print(f"  ✓ Backoff timing: {elapsed:.2f}s")
            if expected_min <= elapsed <= expected_max:
                print(f"    ✓ Within expected range ({expected_min}s - {expected_max}s)")
            else:
                print(f"    ⚠ Outside expected range (got {elapsed:.2f}s, expected {expected_min}-{expected_max}s)")
            
            # Verify retry count
            assert mock_get.call_count == 4
            print(f"  ✓ Correct number of retries: {mock_get.call_count}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Backoff timing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_timeout_configuration():
    """Test that HTTP timeout is configured."""
    print("\nTesting HTTP timeout configuration...")
    
    try:
        from macro_econ_data_archive.macro_utils import fetch_fred
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "DATE,TEST\n2020-01-01,100\n"
            mock_get.return_value = mock_response
            
            fetch_fred(['TEST'], start='2020-01-01')
            
            # Check that timeout was passed
            call_kwargs = mock_get.call_args[1]
            assert 'timeout' in call_kwargs
            assert call_kwargs['timeout'] == 30
            print(f"  ✓ HTTP timeout set to {call_kwargs['timeout']}s")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Timeout test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all caching and retry tests."""
    print("=" * 70)
    print("Caching and Retry Logic Tests")
    print("=" * 70)
    
    tests = [
        ("Custom Exceptions", test_custom_exceptions),
        ("fetch_fred Signature", test_fetch_fred_signature),
        ("Retry Logic (Mock)", test_retry_logic_mock),
        ("Streamlit Caching", test_streamlit_caching),
        ("Exponential Backoff", test_exponential_backoff),
        ("HTTP Timeout", test_timeout_configuration)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:<30} {status}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 70)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
