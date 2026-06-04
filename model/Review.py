from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

@dataclass
class Review:
    place_id: Optional[str] = None
    place_name: Optional[str] = None

    review_id: Optional[str] = None

    author_name: Optional[str] = None
    author_id: Optional[str] = None
    author_url: Optional[str] = None
    author_photo: Optional[str] = None
    author_badge: Optional[str] = None

    author_review_count: Optional[int] = None
    author_photo_count: Optional[int] = None

    rating: Optional[int] = None
    text: Optional[str] = None

    published_at: Optional[str] = None
    published_at_iso: Optional[str] = None
    updated_at_iso: Optional[str] = None

    likes_count: Optional[int] = None
    
    owner_reply: Optional[str] = None

    photos: List[Any] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.review_id)

    def __eq__(self, other):
        return (
            isinstance(other, Review)
            and self.review_id == other.review_id
        )

    @classmethod
    def from_apify(cls, item: Dict[str, Any]) -> "Review":
        return cls(
            place_id=item.get("placeId"),
            place_name=item.get("placeName"),

            review_id=item.get("reviewId"),

            author_name=item.get("authorName"),
            author_id=item.get("authorId"),
            author_url=item.get("authorUrl"),
            author_photo=item.get("authorPhoto"),
            author_badge=item.get("authorBadge"),

            author_review_count=item.get("authorReviewCount"),
            author_photo_count=item.get("authorPhotoCount"),

            rating=item.get("rating"),
            text=item.get("text"),

            published_at=item.get("publishedAt"),
            published_at_iso=item.get("publishedAtIso"),
            updated_at_iso=item.get("updatedAtIso"),

            likes_count=item.get("likesCount"),

            owner_reply=item.get("ownerReply"),

            photos=item.get("photos") or [],
            attributes=item.get("attributes") or {},
        )