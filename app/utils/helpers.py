"""
General utility functions and helpers for the application.
"""
import hashlib
import hmac
import secrets
import string
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic
from datetime import datetime, timezone, timedelta
import json
import re
from functools import wraps
import time
import asyncio
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Pagination(Generic[T]):
    """Generic pagination helper."""
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        per_page: int,
        has_prev: bool = False,
        has_next: bool = False
    ):
        self.items = items
        self.total = total
        self.page = page
        self.per_page = per_page
        self.has_prev = has_prev
        self.has_next = has_next
        self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pagination to dictionary."""
        return {
            "items": self.items,
            "pagination": {
                "page": self.page,
                "per_page": self.per_page,
                "total": self.total,
                "pages": self.pages,
                "has_prev": self.has_prev,
                "has_next": self.has_next,
                "prev_page": self.page - 1 if self.has_prev else None,
                "next_page": self.page + 1 if self.has_next else None,
            }
        }


def generate_random_string(length: int = 32, include_symbols: bool = False) -> str:
    """
    Generate a cryptographically secure random string.
    
    Args:
        length: Length of the string to generate
        include_symbols: Whether to include symbols in the string
        
    Returns:
        str: Random string
    """
    characters = string.ascii_letters + string.digits
    if include_symbols:
        characters += "!@#$%^&*()-_=+[]{}|;:,.<>?"
    
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_api_key(prefix: str = "pk", length: int = 32) -> str:
    """
    Generate API key with prefix.
    
    Args:
        prefix: Prefix for the API key
        length: Length of the random part
        
    Returns:
        str: Generated API key
    """
    random_part = generate_random_string(length)
    return f"{prefix}_{random_part}"


def hash_string(value: str, salt: Optional[str] = None) -> str:
    """
    Hash a string using SHA-256.
    
    Args:
        value: String to hash
        salt: Optional salt to add
        
    Returns:
        str: Hexadecimal hash
    """
    if salt:
        value = f"{value}{salt}"
    return hashlib.sha256(value.encode()).hexdigest()


def create_hmac_signature(data: str, secret: str) -> str:
    """
    Create HMAC signature for data.
    
    Args:
        data: Data to sign
        secret: Secret key for signing
        
    Returns:
        str: HMAC signature
    """
    return hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_hmac_signature(data: str, signature: str, secret: str) -> bool:
    """
    Verify HMAC signature.
    
    Args:
        data: Original data
        signature: Signature to verify
        secret: Secret key used for signing
        
    Returns:
        bool: True if signature is valid, False otherwise
    """
    expected_signature = create_hmac_signature(data, secret)
    return hmac.compare_digest(signature, expected_signature)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove/replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = f"{name[:max_name_length]}.{ext}" if ext else name[:255]
    
    # Ensure filename is not empty
    if not filename:
        filename = f"file_{generate_random_string(8)}"
    
    return filename


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024 and i < len(size_names) - 1:
        size /= 1024
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        str: Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)
        
    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
    """
    Flatten nested dictionary.
    
    Args:
        data: Dictionary to flatten
        separator: Separator for nested keys
        
    Returns:
        Dict[str, Any]: Flattened dictionary
    """
    def _flatten(obj: Any, parent_key: str = '') -> Dict[str, Any]:
        items = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                items.extend(_flatten(value, new_key).items())
        else:
            items.append((parent_key, obj))
        
        return dict(items)
    
    return _flatten(data)


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with default fallback.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Any: Parsed data or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(data: Any, default: Any = None) -> str:
    """
    Safely serialize data to JSON string.
    
    Args:
        data: Data to serialize
        default: Default serializer function
        
    Returns:
        str: JSON string
    """
    try:
        return json.dumps(data, default=default or str)
    except (TypeError, ValueError):
        return "{}"


def chunk_list(data: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split list into chunks of specified size.
    
    Args:
        data: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List[List[T]]: List of chunks
    """
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def remove_duplicates(data: List[T], key_func: Optional[callable] = None) -> List[T]:
    """
    Remove duplicates from list while preserving order.
    
    Args:
        data: List with potential duplicates
        key_func: Optional function to extract comparison key
        
    Returns:
        List[T]: List without duplicates
    """
    seen = set()
    result = []
    
    for item in data:
        key = key_func(item) if key_func else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def calculate_age(birth_date: datetime, reference_date: Optional[datetime] = None) -> int:
    """
    Calculate age from birth date.
    
    Args:
        birth_date: Date of birth
        reference_date: Reference date (defaults to now)
        
    Returns:
        int: Age in years
    """
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)
    
    age = reference_date.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age


def format_currency(amount: float, currency: str = "USD", locale: str = "en_US") -> str:
    """
    Format amount as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code
        locale: Locale for formatting
        
    Returns:
        str: Formatted currency string
    """
    try:
        import locale as loc
        loc.setlocale(loc.LC_ALL, locale)
        return loc.currency(amount, grouping=True)
    except Exception:
        # Fallback formatting
        if currency == "USD":
            return f"${amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_factor: float = 2.0
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_factor: Factor for exponential backoff
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    delay = min(base_delay * (exponential_factor ** attempt), max_delay)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


async def retry_async_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_factor: float = 2.0
):
    """
    Decorator for retrying async functions with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_factor: Factor for exponential backoff
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Async function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    
                    delay = min(base_delay * (exponential_factor ** attempt), max_delay)
                    logger.warning(f"Async function {func.__name__} failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


def timing_decorator(func):
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"Function {func.__name__} executed in {execution_time:.4f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.4f}s: {e}")
            raise
    
    return wrapper


@asynccontextmanager
async def async_timing_context(operation_name: str):
    """Async context manager for timing operations."""
    start_time = time.time()
    logger.debug(f"Starting {operation_name}")
    
    try:
        yield
    finally:
        execution_time = time.time() - start_time
        logger.debug(f"Completed {operation_name} in {execution_time:.4f}s")


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number for consistent storage.
    
    Args:
        phone: Phone number to normalize
        
    Returns:
        str: Normalized phone number
    """
    # Remove all non-digit characters except +
    normalized = re.sub(r'[^\d+]', '', phone)
    
    # Add + if not present and number looks international
    if not normalized.startswith('+') and len(normalized) > 10:
        normalized = f"+{normalized}"
    
    return normalized


def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate URL-friendly slug from text.
    
    Args:
        text: Text to convert to slug
        max_length: Maximum length of slug
        
    Returns:
        str: URL-friendly slug
    """
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Truncate if too long
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    # Ensure slug is not empty
    if not slug:
        slug = generate_random_string(8).lower()
    
    return slug


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging/display.
    
    Args:
        data: Sensitive data to mask
        mask_char: Character to use for masking
        visible_chars: Number of characters to keep visible at the end
        
    Returns:
        str: Masked data
    """
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]


def get_client_ip(request_headers: Dict[str, str]) -> str:
    """
    Extract client IP address from request headers.
    
    Args:
        request_headers: HTTP request headers
        
    Returns:
        str: Client IP address
    """
    # Check for common proxy headers
    forwarded_for = request_headers.get('x-forwarded-for', '').split(',')[0].strip()
    if forwarded_for:
        return forwarded_for
    
    real_ip = request_headers.get('x-real-ip', '').strip()
    if real_ip:
        return real_ip
    
    # Fallback headers
    forwarded = request_headers.get('forwarded', '')
    if forwarded:
        # Parse Forwarded header (RFC 7239)
        match = re.search(r'for=([^;,\s]+)', forwarded)
        if match:
            return match.group(1).strip('"[]')
    
    return request_headers.get('remote-addr', 'unknown')
