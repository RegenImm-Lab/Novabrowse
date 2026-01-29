#!/usr/bin/env python
# coding: utf-8
"""
NCBI Cache Module using diskcache
Provides transparent caching for NCBI Entrez requests
"""

import hashlib
from io import StringIO, BytesIO
from functools import wraps
from typing import Callable, Optional
import diskcache

# Global cache instance
_cache: Optional[diskcache.Cache] = None

def init_cache(cache_dir: str = "ncbi_cache", 
               size_limit_mb: int = 500,
               enabled: bool = True) -> diskcache.Cache:
    """
    Initialize the global cache instance.
    
    Args:
        cache_dir: Directory to store cache files
        size_limit_mb: Maximum size of the cache in megabytes
        enabled: Whether caching is enabled
    """
    global _cache
    if enabled:
        _cache = diskcache.Cache(
            cache_dir,
            size_limit=size_limit_mb * 1024 * 1024,
            eviction_policy='least-recently-used'
        )
    else:
        _cache = None
    return _cache

def get_cache() -> Optional[diskcache.Cache]:
    """Get the global cache instance, creating it if necessary."""
    global _cache
    if _cache is None:
        init_cache()
    return _cache

def make_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """
    Generate a unique cache key for the request.
    Includes relevant Entrez global settings for uniqueness.
    """
    from Bio import Entrez
    
    cache_parts = [func_name]
    
    # Include relevant global Entrez settings that might affect results
    global_settings = {
        'email': getattr(Entrez, 'email', None),
        'api_key': getattr(Entrez, 'api_key', None),
        'tool': getattr(Entrez, 'tool', None),
    }
    cache_parts.append(str(sorted(global_settings.items())))
    
    # Add positional arguments
    for arg in args:
        if hasattr(arg, '__dict__'):
            cache_parts.append(str(sorted(arg.__dict__.items())))
        else:
            cache_parts.append(str(arg))
    
    # Add keyword arguments (sorted for consistency)
    cache_parts.append(str(sorted(kwargs.items())))

    # Generate hash
    cache_string = "|".join(cache_parts)

    return hashlib.md5(cache_string.encode()).hexdigest()

def detect_format(data: bytes, kwargs: dict) -> str:
    """
    Detect the format of the response data.
    
    Returns:
        Format string: 'fasta', 'text', or 'xml'
    """
    # Check rettype/retmode in kwargs
    rettype = kwargs.get('rettype', '').lower()
    retmode = kwargs.get('retmode', '').lower()
    
    if rettype == 'fasta':
        return 'fasta'
    elif retmode == 'xml':
        return 'xml'
    elif retmode == 'text':
        return 'text'
    
    # Try to detect from content
    try:
        sample = data[:1000] if isinstance(data, bytes) else data[:1000].encode()
        sample_str = sample.decode('utf-8', errors='ignore').strip()
        
        if sample_str.startswith('>'):
            return 'fasta'
        elif sample_str.startswith('<?xml') or sample_str.startswith('<'):
            return 'xml'
    except:
        pass
    
    return 'xml'  # Default

def cache_ncbi_request(func: Callable) -> Callable:
    """
    Decorator to cache NCBI Entrez requests.
    
    This decorator intercepts calls to Entrez functions and:
    1. Checks if the result is cached
    2. Returns cached result if available
    3. Otherwise makes the actual request and caches it
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        cache = get_cache()
        
        # If cache is disabled, just call the function
        if cache is None:
            return func(*args, **kwargs)
        
        # Generate cache key
        func_name = func.__name__
        cache_key = make_cache_key(func_name, args, kwargs)
        
        # Try to get from cache
        cached_entry = cache.get(cache_key)
        
        if cached_entry is not None:
            # Cache hit - return appropriate IO object
            data = cached_entry['data']
            format_type = cached_entry['format']
            
            # Log cache hit
            description = _make_description(func_name, kwargs)
            print(f"Using cached data for {description}")
            
            if format_type in ('fasta', 'text'):
                return StringIO(data.decode('utf-8') if isinstance(data, bytes) else data)
            else:
                return BytesIO(data if isinstance(data, bytes) else data.encode('utf-8'))
        
        # Cache miss - make actual request
        response = func(*args, **kwargs)
        
        # Read and store the response
        if hasattr(response, 'read'):
            response_data = response.read()
            if isinstance(response_data, str):
                response_data = response_data.encode('utf-8')
        else:
            response_data = str(response).encode('utf-8')
        
        # Detect format and store in cache
        data_format = detect_format(response_data, kwargs)
        cache[cache_key] = {
            'data': response_data,
            'format': data_format
        }
        
        # Return appropriate IO object
        if data_format in ('fasta', 'text'):
            return StringIO(response_data.decode('utf-8'))
        else:
            return BytesIO(response_data)
    
    return wrapper

def _make_description(func_name: str, kwargs: dict) -> str:
    """Create a human-readable description of the request."""
    description = f"{func_name}"
    
    if 'db' in kwargs:
        description += f" from {kwargs['db']}"
    
    if 'term' in kwargs:
        term = kwargs['term']
        term_preview = term[:100] + "..." if len(term) > 100 else term
        description += f": {term_preview}"
    elif 'id' in kwargs:
        id_str = str(kwargs['id'])
        if len(id_str) > 50:
            id_str = id_str[:47] + "..."
        description += f": {id_str}"
    
    return description

def apply_cache_to_entrez():
    """
    Monkey-patch the Bio.Entrez module to use cached versions.
    Call this once at the beginning of your script.
    """
    from Bio import Entrez
    
    # Store original functions
    if not hasattr(Entrez, '_original_esearch'):
        Entrez._original_esearch = Entrez.esearch
        Entrez._original_efetch = Entrez.efetch
    
    # Apply decorator to the functions
    Entrez.esearch = cache_ncbi_request(Entrez._original_esearch)
    Entrez.efetch = cache_ncbi_request(Entrez._original_efetch)
    
    print("NCBI request caching enabled")

def disable_cache_for_entrez():
    """Restore original Entrez functions without caching."""
    from Bio import Entrez
    
    if hasattr(Entrez, '_original_esearch'):
        Entrez.esearch = Entrez._original_esearch
        Entrez.efetch = Entrez._original_efetch
        print("NCBI request caching disabled")

def clear_cache():
    """Clear all cached data."""
    cache = get_cache()
    if cache is not None:
        cache.clear()
        print("Cache cleared")
