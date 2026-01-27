import ncbi_cache

ncbi_cache.init_cache(
    cache_dir="ncbi_cache", cache_duration_days=7, enabled=True
).clear_cache(older_than_days=7)

# This applies caching to ALL Entrez calls (esearch and efetch)
ncbi_cache.apply_cache_to_entrez()
