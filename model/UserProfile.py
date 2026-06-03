from model.Review import Review

from typing import Optional, List
from dataclasses import dataclass, field

@dataclass
class UserProfile:
    author_id: str
    author_name: Optional[str] = None
    author_url: Optional[str] = None

    reviews: List[Review] = field(default_factory=list)

    def add_review(self, review: Review):
        self.reviews.append(review)

    def avg_rating(self):
        ratings = [r.rating for r in self.reviews if r.rating]
        return sum(ratings) / len(ratings) if ratings else None