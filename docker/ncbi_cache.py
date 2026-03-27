import diskcache
import io
import json
import logging
from functools import wraps
from Bio import Entrez
import os
from xml.etree import ElementTree as ET

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Cache setup
CACHE_DIR = "tmp/ncbi_cache"
CACHE_SIZE_MB = int(os.getenv("ENTREZ_CACHE_SIZE_MB", "500"))
USE_CACHE = os.getenv("ENTREZ_USE_CACHE", "1").lower() in ("1", "true", "yes")

cache = diskcache.Cache(CACHE_DIR, size_limit=CACHE_SIZE_MB * 1024 * 1024)


def generate_cache_key(func_name, args, kwargs):
    """Generate a unique cache key from function name and arguments."""
    key_parts = [func_name]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return "|".join(key_parts)


def detect_format(response_content, kwargs):
    """Detect the response format based on content and parameters."""
    if not response_content:
        return None

    # Check if FASTA format was requested
    if kwargs.get("rettype") == "fasta" or kwargs.get("retmode") == "text":
        return "fasta"

    # Check for JSON
    try:
        json.loads(
            response_content.decode("utf-8")
            if isinstance(response_content, bytes)
            else response_content
        )
        return "json"
    except (ValueError, TypeError):
        pass

    # Default to XML
    return "xml"


def is_error_response(response_content):
    """Check if response contains an error message from NCBI."""
    if not response_content:
        return True

    # Convert to string for pattern matching
    if isinstance(response_content, bytes):
        text_content = response_content.decode("utf-8", errors="ignore")
    else:
        text_content = response_content

    error_patterns = [
        "Search Backend failed",
        "Error fetching",
        "Service temporarily unavailable",
        "Rate limit exceeded",
        "Invalid parameter",
        "Internal Server Error",
    ]

    # Test lowercase version of text content for case-insensitive matching.
    return any(pattern.lower() in text_content.lower() for pattern in error_patterns)

def is_empty_response(response_content, response_format, func_name, kwargs):
    """Check if response is empty based on format and function."""
    if not response_content:
        logger.debug(f"Empty response content for {func_name}")
        return True

    if response_format == "json":
        try:
            data = json.loads(
                response_content.decode("utf-8")
                if isinstance(response_content, bytes)
                else response_content
            )
            logger.debug(
                f"JSON response for {func_name}: {json.dumps(data, indent=2)[:500]}"
            )

            if func_name == "esummary":
                uids = data.get("result", {}).get("uids", [])
                logger.debug(f"esummary JSON response uids: {uids[:10]} (total {len(uids)})")
                return len(uids) == 0

            elif func_name == "esearch":
                idlist = data.get("esearchresult", {}).get("idlist", [])
                logger.debug(f"esearch JSON response idlist: {idlist[:10]} (total {len(idlist)})")
                return len(idlist) == 0

            elif func_name == "efetch":
                # For gene info JSON, check if there's any meaningful data
                if not data or (isinstance(data, dict) and not data):
                    logger.debug("Empty efetch JSON response")
                    return True
                # Check for specific empty indicators in gene info JSON
                if isinstance(data, dict):
                    if "error" in data or "ERROR" in data:
                        return True
                    # Check if the response contains any actual gene data
                    if not any(
                        key in data for key in ["Entrezgene", "gene", "document"]
                    ):
                        logger.debug("efetch JSON response contains no gene data")
                        return True

        except (ValueError, TypeError) as e:
            logger.debug(f"JSON parsing error for {func_name}: {str(e)}")
            pass

    elif response_format == "xml":
        # Convert to string for XML checking
        text_content = (
            response_content.decode("utf-8")
            if isinstance(response_content, bytes)
            else response_content
        )
        logger.debug(
            f"XML response for {func_name} (first 500 chars): {text_content[:500]}"
        )

        try:
            root = ET.fromstring(text_content)

            if func_name == "esummary":
                doc_sums = root.findall(".//DocSum")
                ids = [
                    doc.find("Id").text
                    for doc in doc_sums
                    if doc.find("Id") is not None
                ]
                logger.debug(f"esummary XML response IDs: {ids[:10]} (total {len(ids)})")
                return len(ids) == 0

            elif func_name == "esearch":
                id_list = root.find(".//IdList")
                if id_list is not None:
                    ids = [id_elem.text for id_elem in id_list.findall("Id")]
                    logger.debug(f"esearch XML response IDs: {ids[:10]} (total {len(ids)})")
                    return len(ids) == 0
                return True

            elif func_name == "efetch":
                # Check for empty efetch XML responses (gene info)
                if root.tag.endswith("ERROR"):
                    logger.debug("efetch XML response is an error")
                    return True

                # Check for Entrezgene-Set structure
                if root.tag.endswith("Entrezgene-Set"):
                    gene_elements = root.findall(".//Entrezgene")
                    if not gene_elements:
                        logger.debug(
                            "efetch XML response contains no Entrezgene elements"
                        )
                        return True

                    # Check if the gene elements contain actual data
                    for gene in gene_elements:
                        # Check for basic gene info elements
                        gene_id = gene.find(".//Gene-track_geneid")
                        status = gene.find(".//Gene-track_status")

                        if gene_id is None or status is None:
                            continue

                        # If we found a gene with ID and status, it's not empty
                        if gene_id.text and status.text:
                            logger.debug(
                                f"Found valid gene data for ID: {gene_id.text}"
                            )
                            return False

                    logger.debug("efetch XML response contains only empty gene records")
                    return True

                # Fallback for other XML structures
                if not list(root):
                    logger.debug("efetch XML response contains no child elements")
                    return True

        except ET.ParseError as e:
            logger.debug(f"XML parsing error for {func_name}: {str(e)}")
            return True

    elif response_format == "fasta":
        # FASTA is empty if it's just whitespace
        text_content = (
            response_content.decode("utf-8")
            if isinstance(response_content, bytes)
            else response_content
        )
        logger.debug(f"FASTA response content (first 200 chars): {text_content[:200]}")
        if not text_content.strip():
            logger.debug("Empty FASTA response detected")
            return True

    return False


def cache_ncbi_request(func):
    """Decorator to cache NCBI Entrez requests."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if not USE_CACHE:
            return func(*args, **kwargs)

        cache_key = generate_cache_key(func.__name__, args, kwargs)
        logger.debug(f"Cache key for {func.__name__}: {cache_key}")

        if cache_key in cache:
            logger.info(f"Cache hit for {func.__name__}")
            cached_data = cache[cache_key]
            response_format = detect_format(cached_data, kwargs)
            logger.debug(f"Returning cached {response_format} response")

            # Return appropriate file-like object based on format
            if response_format == "fasta":
                text_data = (
                    cached_data.decode("utf-8")
                    if isinstance(cached_data, bytes)
                    else cached_data
                )
                return io.StringIO(text_data)
            else:
                byte_data = (
                    cached_data
                    if isinstance(cached_data, bytes)
                    else cached_data.encode("utf-8")
                )
                return io.BytesIO(byte_data)

        try:
            logger.debug(
                f"Making new {func.__name__} request with args: {args}, kwargs: {kwargs}"
            )
            response = func(*args, **kwargs)
            response_content = response.read()
            response_format = detect_format(response_content, kwargs)
            logger.debug(f"Received {response_format} response")

            # Ensure consistent byte storage in cache
            if isinstance(response_content, str):
                cache_data = response_content.encode("utf-8")
            else:
                cache_data = response_content

            if is_error_response(cache_data):
                logger.warning(
                    f"Error response detected for {func.__name__}, not caching"
                )
                if response_format == "fasta":
                    return io.StringIO(
                        response_content
                        if isinstance(response_content, str)
                        else response_content.decode("utf-8")
                    )
                else:
                    return io.BytesIO(
                        response_content
                        if isinstance(response_content, bytes)
                        else response_content.encode("utf-8")
                    )

            if is_empty_response(cache_data, response_format, func.__name__, kwargs):
                logger.warning(
                    f"Empty response detected for {func.__name__}, not caching"
                )
                if response_format == "fasta":
                    return io.StringIO(
                        response_content
                        if isinstance(response_content, str)
                        else response_content.decode("utf-8")
                    )
                else:
                    return io.BytesIO(
                        response_content
                        if isinstance(response_content, bytes)
                        else response_content.encode("utf-8")
                    )

            # Cache successful response
            cache.set(cache_key, cache_data)
            logger.info(
                f"Cached response for {func.__name__} (format: {response_format})"
            )

            # Return appropriate file-like object
            if response_format == "fasta":
                return io.StringIO(
                    response_content
                    if isinstance(response_content, str)
                    else response_content.decode("utf-8")
                )
            else:
                return io.BytesIO(
                    response_content
                    if isinstance(response_content, bytes)
                    else response_content.encode("utf-8")
                )

        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise

    return wrapper


# Monkey patch Entrez functions
if USE_CACHE:
    Entrez.esearch = cache_ncbi_request(Entrez.esearch)
    Entrez.efetch = cache_ncbi_request(Entrez.efetch)
    Entrez.esummary = cache_ncbi_request(Entrez.esummary)
    logger.info("NCBI Entrez caching enabled")
else:
    logger.info("NCBI Entrez caching disabled")
