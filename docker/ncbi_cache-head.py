import os
import ncbi_cache

cache_days = int(os.getenv("ENTREZ_CACHE_EXPIRY_DAYS", "3"))

ncbi_cache.init_cache(
    cache_dir="ncbi_cache",
    cache_duration_days=cache_days,
    enabled=True
).clear_cache(older_than_days=cache_days)

# This applies caching to ALL Entrez calls (esearch and efetch)
ncbi_cache.apply_cache_to_entrez()
