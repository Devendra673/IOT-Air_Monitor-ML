"""
Rate Limiting for API Endpoints
Prevents API abuse and ensures fair usage
"""

from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta
from collections import defaultdict
import threading

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, key, max_requests, time_window_seconds):
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier (IP or user ID)
            max_requests: Maximum number of requests allowed
            time_window_seconds: Time window in seconds
        
        Returns:
            tuple: (is_allowed, retry_after_seconds)
        """
        with self.lock:
            now = datetime.now()
            cutoff_time = now - timedelta(seconds=time_window_seconds)
            
            # Remove old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > cutoff_time
            ]
            
            # Check if under limit
            if len(self.requests[key]) < max_requests:
                self.requests[key].append(now)
                return True, 0
            else:
                # Calculate retry after
                oldest_request = min(self.requests[key])
                retry_after = (oldest_request + timedelta(seconds=time_window_seconds) - now).total_seconds()
                return False, int(retry_after) + 1
    
    def cleanup_old_entries(self, max_age_seconds=3600):
        """Remove entries older than max_age_seconds"""
        with self.lock:
            now = datetime.now()
            cutoff_time = now - timedelta(seconds=max_age_seconds)
            
            keys_to_remove = []
            for key, requests in list(self.requests.items()):
                # Filter old requests
                self.requests[key] = [
                    req_time for req_time in requests
                    if req_time > cutoff_time
                ]
                
                # Mark empty keys for removal
                if not self.requests[key]:
                    keys_to_remove.append(key)
            
            # Remove empty keys
            for key in keys_to_remove:
                del self.requests[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(max_requests=100, time_window=60, by_user=False):
    """
    Decorator for rate limiting endpoints
    
    Args:
        max_requests: Maximum number of requests allowed
        time_window: Time window in seconds
        by_user: If True, rate limit per user; if False, per IP
    
    Example:
        @rate_limit(max_requests=10, time_window=60)  # 10 requests per minute
        def my_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Determine rate limit key
            if by_user:
                from flask import session
                key = session.get('user_id', request.remote_addr)
            else:
                key = request.remote_addr
            
            # Check rate limit
            is_allowed, retry_after = rate_limiter.is_allowed(
                key, max_requests, time_window
            )
            
            if not is_allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again in {retry_after} seconds.',
                    'retry_after': retry_after
                }), 429
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

# Predefined rate limit decorators for common use cases
def rate_limit_strict(f):
    """Strict rate limit: 10 requests per minute"""
    return rate_limit(max_requests=10, time_window=60)(f)

def rate_limit_moderate(f):
    """Moderate rate limit: 30 requests per minute"""
    return rate_limit(max_requests=30, time_window=60)(f)

def rate_limit_relaxed(f):
    """Relaxed rate limit: 100 requests per minute"""
    return rate_limit(max_requests=100, time_window=60)(f)

def rate_limit_per_user(f):
    """Rate limit per authenticated user: 50 requests per minute"""
    return rate_limit(max_requests=50, time_window=60, by_user=True)(f)
