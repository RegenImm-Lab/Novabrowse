#!/usr/bin/env python
# coding: utf-8
"""
NCBI Cache Module with Decorator Support
Provides transparent caching for NCBI Entrez requests
"""

import hashlib
import json
import os
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional, Callable
from io import StringIO, BytesIO
import logging
from functools import wraps

class NCBICache:
    def __init__(self, cache_dir: str = "ncbi_cache", 
                 cache_duration_days: int = 30,
                 enabled: bool = True):
        """
        Initialize NCBI cache.
        
        Args:
            cache_dir: Directory to store cache files
            cache_duration_days: How long to keep cached data (in days)
            enabled: Whether caching is enabled
        """
        self.cache_dir = Path(cache_dir)
        self.cache_duration = cache_duration_days * 86400  # Convert to seconds
        self.enabled = enabled
        
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._init_cache_index()
    
    def _init_cache_index(self):
        """Initialize or load the cache index."""
        self.index_file = self.cache_dir / "cache_index.json"
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.cache_index = json.load(f)
            except:
                self.cache_index = {}
        else:
            self.cache_index = {}
    
    def _save_cache_index(self):
        """Save the cache index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(self.cache_index, f, indent=2)
    
    def _get_cache_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate a unique cache key for the request."""
        # Create a string representation of the function call
        cache_string = f"{func_name}"
        
        # Add positional arguments
        for arg in args:
            if hasattr(arg, '__dict__'):
                cache_string += str(arg.__dict__)
            else:
                cache_string += str(arg)
        
        # Add keyword arguments (sorted for consistency)
        for key in sorted(kwargs.keys()):
            cache_string += f"{key}={kwargs[key]}"
        
        # Generate hash
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data exists and is still valid."""
        if not self.enabled:
            return False
            
        if cache_key not in self.cache_index:
            return False
        
        cache_info = self.cache_index[cache_key]
        cache_file = self.cache_dir / cache_info['filename']
        
        if not cache_file.exists():
            return False
        
        # Check if cache has expired
        if time.time() - cache_info['timestamp'] > self.cache_duration:
            return False
        
        return True
    
    def get_cached_response(self, func_name: str, args: tuple, kwargs: dict) -> Optional[Any]:
        """
        Get cached response if available.
        
        Returns:
            Cached response as appropriate IO object or None if not cached
        """
        if not self.enabled:
            return None
            
        cache_key = self._get_cache_key(func_name, args, kwargs)
        
        if not self._is_cache_valid(cache_key):
            return None
        
        cache_info = self.cache_index[cache_key]
        cache_file = self.cache_dir / cache_info['filename']
        
        try:
            with open(cache_file, 'rb') as f:
                cache_entry = pickle.load(f)
            
            # Log cache hit
            logging.info(f"Cache hit for {func_name}: {cache_info['description']}")
            print(f"Using cached data for {func_name}: {cache_info['description']}")
            
            # Get the cached data and format type
            cached_data = cache_entry['data']
            data_format = cache_entry.get('format', 'unknown')
            
            # Return appropriate IO object based on format
            if data_format == 'fasta' or data_format == 'text':
                # FASTA and text formats need StringIO
                if isinstance(cached_data, bytes):
                    cached_data = cached_data.decode('utf-8')
                return StringIO(cached_data)
            else:
                # XML and other formats need BytesIO
                if isinstance(cached_data, str):
                    cached_data = cached_data.encode('utf-8')
                return BytesIO(cached_data)
                
        except Exception as e:
            logging.error(f"Error reading cache: {e}")
            return None
    
    def save_response(self, func_name: str, args: tuple, kwargs: dict, 
                     response_data: bytes, data_format: str, description: str = ""):
        """
        Save response to cache.
        
        Args:
            func_name: Name of the Entrez function
            args: Positional arguments
            kwargs: Keyword arguments
            response_data: Raw response data as bytes
            data_format: Format of the data (xml, fasta, text, etc.)
            description: Human-readable description of the request
        """
        if not self.enabled:
            return
        
        cache_key = self._get_cache_key(func_name, args, kwargs)
        filename = f"{cache_key}.pkl"
        cache_file = self.cache_dir / filename
        
        try:
            # Save response with format information
            cache_entry = {
                'data': response_data,
                'format': data_format
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_entry, f)
            
            # Update index
            self.cache_index[cache_key] = {
                'filename': filename,
                'timestamp': time.time(),
                'func_name': func_name,
                'format': data_format,
                'description': description or f"{func_name} request",
                'args_summary': self._summarize_args(args, kwargs)
            }
            self._save_cache_index()
            
            logging.info(f"Cached {func_name}: {description}")
            
        except Exception as e:
            logging.error(f"Error saving to cache: {e}")
    
    def _summarize_args(self, args: tuple, kwargs: dict) -> str:
        """Create a human-readable summary of arguments."""
        summary_parts = []
        
        # Common kwargs to include in summary
        if 'db' in kwargs:
            summary_parts.append(f"db={kwargs['db']}")
        if 'term' in kwargs:
            term = kwargs['term'][:50] + "..." if len(kwargs['term']) > 50 else kwargs['term']
            summary_parts.append(f"term={term}")
        if 'id' in kwargs:
            id_str = str(kwargs['id'])
            if len(id_str) > 50:
                id_str = id_str[:50] + "..."
            summary_parts.append(f"id={id_str}")
        
        return ", ".join(summary_parts) if summary_parts else "No args"
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear cache files.
        
        Args:
            older_than_days: Only clear files older than this many days.
                           If None, clear all cache.
        """
        if not self.enabled:
            return
        
        current_time = time.time()
        
        if older_than_days is None:
            # Clear all
            for file in self.cache_dir.glob("*.pkl"):
                file.unlink()
            self.cache_index = {}
        else:
            # Clear old files
            cutoff_time = current_time - (older_than_days * 86400)
            keys_to_remove = []
            
            for cache_key, info in self.cache_index.items():
                if info['timestamp'] < cutoff_time:
                    cache_file = self.cache_dir / info['filename']
                    if cache_file.exists():
                        cache_file.unlink()
                    keys_to_remove.append(cache_key)
            
            for key in keys_to_remove:
                del self.cache_index[key]
        
        self._save_cache_index()
        print(f"Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False}
        
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl"))
        
        return {
            "enabled": True,
            "total_files": len(self.cache_index),
            "total_size_mb": total_size / (1024 * 1024),
            "cache_dir": str(self.cache_dir),
            "cache_duration_days": self.cache_duration / 86400
        }


# Create global cache instance
_global_cache = None

def init_cache(cache_dir: str = "ncbi_cache", 
               cache_duration_days: int = 30,
               enabled: bool = True) -> NCBICache:
    """Initialize the global cache instance."""
    global _global_cache
    _global_cache = NCBICache(cache_dir, cache_duration_days, enabled)
    return _global_cache

def get_cache() -> NCBICache:
    """Get the global cache instance, creating it if necessary."""
    global _global_cache
    if _global_cache is None:
        _global_cache = init_cache()
    return _global_cache


def detect_format(data: bytes, kwargs: dict) -> str:
    """
    Detect the format of the response data.
    
    Args:
        data: Response data as bytes
        kwargs: Request keyword arguments
        
    Returns:
        Format string: 'xml', 'fasta', 'text', etc.
    """
    # Check rettype/retmode in kwargs
    rettype = kwargs.get('rettype', '').lower()
    retmode = kwargs.get('retmode', '').lower()
    
    # Direct format detection from parameters
    if rettype == 'fasta':
        return 'fasta'
    elif retmode == 'xml':
        return 'xml'
    elif retmode == 'text':
        return 'text'
    
    # Try to detect from content
    try:
        # Decode first part of data for inspection
        sample = data[:1000] if isinstance(data, bytes) else data[:1000].encode()
        sample_str = sample.decode('utf-8', errors='ignore')
        
        # Check for FASTA format
        if sample_str.strip().startswith('>'):
            return 'fasta'
        
        # Check for XML
        if sample_str.strip().startswith('<?xml') or sample_str.strip().startswith('<'):
            return 'xml'
        
    except:
        pass
    
    # Default to XML for safety (binary mode)
    return 'xml'


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
        
        # Get the function name for cache key
        func_name = func.__name__
        
        # Try to get cached response
        cached_response = cache.get_cached_response(func_name, args, kwargs)
        if cached_response is not None:
            return cached_response
        
        # Make actual request
        response = func(*args, **kwargs)
        
        # Read the response and preserve it as bytes
        if hasattr(response, 'read'):
            response_data = response.read()
            # Ensure we have bytes for storage
            if isinstance(response_data, str):
                response_data = response_data.encode('utf-8')
        else:
            # If it's not a file-like object, convert to bytes
            response_data = str(response).encode('utf-8')
        
        # Detect format
        data_format = detect_format(response_data, kwargs)
        
        # Generate description for logging
        description = f"{func_name} request"
        if 'db' in kwargs:
            description = f"{func_name} from {kwargs['db']}"
        if 'term' in kwargs:
            term_preview = kwargs['term'][:100] + "..." if len(kwargs['term']) > 100 else kwargs['term']
            description += f": {term_preview}"
        elif 'id' in kwargs:
            id_str = str(kwargs['id'])
            if len(id_str) > 50:
                id_str = id_str[:47] + "..."
            description += f": {id_str}"
        
        # Save to cache with format information
        cache.save_response(func_name, args, kwargs, response_data, data_format, description)
        
        # Return appropriate IO object based on format
        if data_format == 'fasta' or data_format == 'text':
            # FASTA and text formats need StringIO
            return StringIO(response_data.decode('utf-8'))
        else:
            # XML and other formats need BytesIO
            return BytesIO(response_data)
    
    return wrapper


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
    """
    Restore original Entrez functions without caching.
    """
    from Bio import Entrez
    
    if hasattr(Entrez, '_original_esearch'):
        Entrez.esearch = Entrez._original_esearch
        Entrez.efetch = Entrez._original_efetch
        print("NCBI request caching disabled")
