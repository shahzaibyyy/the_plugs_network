"""
Pagination utilities for API responses.
"""
from typing import Any, Dict, List, Optional, TypeVar, Generic
from math import ceil
from pydantic import BaseModel

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters for API requests."""
    
    page: int = 1
    per_page: int = 20
    
    def __init__(self, page: int = 1, per_page: int = 20, **kwargs):
        # Validate and sanitize pagination parameters
        page = max(1, page)  # Ensure page is at least 1
        per_page = min(max(1, per_page), 100)  # Limit per_page between 1 and 100
        
        super().__init__(page=page, per_page=per_page, **kwargs)
    
    @property
    def offset(self) -> int:
        """Calculate the offset for database queries."""
        return (self.page - 1) * self.per_page
    
    @property
    def limit(self) -> int:
        """Get the limit for database queries."""
        return self.per_page


class PaginationMeta(BaseModel):
    """Pagination metadata for API responses."""
    
    page: int
    per_page: int
    total: int
    pages: int
    has_prev: bool
    has_next: bool
    prev_page: Optional[int] = None
    next_page: Optional[int] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    
    items: List[T]
    pagination: PaginationMeta
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        per_page: int
    ) -> "PaginatedResponse[T]":
        """
        Create a paginated response.
        
        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            per_page: Items per page
            
        Returns:
            PaginatedResponse with items and pagination metadata
        """
        pages = ceil(total / per_page) if per_page > 0 else 0
        has_prev = page > 1
        has_next = page < pages
        
        pagination = PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            pages=pages,
            has_prev=has_prev,
            has_next=has_next,
            prev_page=page - 1 if has_prev else None,
            next_page=page + 1 if has_next else None
        )
        
        return cls(items=items, pagination=pagination)


def paginate(
    items: List[T],
    page: int = 1,
    per_page: int = 20
) -> PaginatedResponse[T]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number
        per_page: Items per page
        
    Returns:
        PaginatedResponse with paginated items
    """
    total = len(items)
    offset = (page - 1) * per_page
    paginated_items = items[offset:offset + per_page]
    
    return PaginatedResponse.create(
        items=paginated_items,
        total=total,
        page=page,
        per_page=per_page
    )


def get_pagination_links(
    base_url: str,
    page: int,
    per_page: int,
    total: int,
    **query_params
) -> Dict[str, Optional[str]]:
    """
    Generate pagination links for API responses.
    
    Args:
        base_url: Base URL for the API endpoint
        page: Current page number
        per_page: Items per page
        total: Total number of items
        **query_params: Additional query parameters
        
    Returns:
        Dict with pagination links (first, prev, next, last)
    """
    pages = ceil(total / per_page) if per_page > 0 else 0
    
    def build_url(page_num: int) -> str:
        params = {"page": page_num, "per_page": per_page, **query_params}
        query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        return f"{base_url}?{query_string}"
    
    links = {
        "first": build_url(1) if pages > 0 else None,
        "prev": build_url(page - 1) if page > 1 else None,
        "next": build_url(page + 1) if page < pages else None,
        "last": build_url(pages) if pages > 0 else None,
    }
    
    return links
