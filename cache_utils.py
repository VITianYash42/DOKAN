import time
from functools import wraps
from flask import request

class SimpleCache:
    def __init__(self):
        self.store = {}

    def get(self, key):
        if key in self.store:
            data, expires_at = self.store[key]
            if time.time() < expires_at:
                return data
            else:
                del self.store[key]
        return None

    def set(self, key, value, ttl_seconds):
        expires_at = time.time() + ttl_seconds
        self.store[key] = (value, expires_at)

    def invalidate_all(self):
        """Clear the entire cache."""
        self.store.clear()

    def cached(self, ttl=60):
        """Decorator for Flask routes."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Create a specific cache key based on path and query string
                cache_key = request.full_path
                
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    # Optional: Log hit
                    # print(f"Cache HIT for {cache_key}")
                    return cached_value
                
                # Compute value
                response = f(*args, **kwargs)
                
                # Cache it
                self.set(cache_key, response, ttl)
                # Optional: Log miss
                # print(f"Cache MISS for {cache_key}")
                
                return response
            return decorated_function
        return decorator
