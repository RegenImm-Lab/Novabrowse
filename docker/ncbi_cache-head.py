import os
import ncbi_cache

use_cache = os.getenv("ENTREZ_USE_CACHE", "true").lower() != "false"
cache_expiry_days = int(os.getenv("ENTREZ_CACHE_EXPIRY_DAYS", "3"))

if use_cache:
    ncbi_cache.init_cache(
        cache_dir="ncbi_cache",
        cache_duration_days=cache_expiry_days,
        enabled=True
    ).clear_cache(older_than_days=cache_expiry_days)

    # This applies caching to ALL Entrez calls (esearch and efetch)
    ncbi_cache.apply_cache_to_entrez()
