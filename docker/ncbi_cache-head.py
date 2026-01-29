import os
import ncbi_cache

use_cache = os.getenv("ENTREZ_USE_CACHE", "true").lower() != "false"

if use_cache:
    # Size limit is in megabytes, default to 500 MB.
    size_limit_mb = int(os.getenv("ENTREZ_CACHE_SIZE_MB", "500"))

    ncbi_cache.init_cache(
        cache_dir="ncbi_cache", size_limit_mb=size_limit_mb, enabled=True
    )

    # This applies caching to ALL Entrez calls (esearch and efetch)
    ncbi_cache.apply_cache_to_entrez()
