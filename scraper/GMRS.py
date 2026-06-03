from apify_client import ApifyClient
from typing import List, Dict, Any

from model.Review import Review

class GoogleMapsReviewsScraper:
    ACTOR_ID = "MNr9yAaSQz6LKVlO3"

    def __init__(self, apify_token: str):
        self.client = ApifyClient(apify_token)

    def scrape(
        self,
        place_url: str,
        max_reviews: int = 100,
        sort_by: str = "lowestRanking",
    ) -> List[Dict[str, Any]]:
        """
        Estrae recensioni da Google Maps tramite l'Actor
        scrapesmith/Google-Maps-Reviews-Scraper.

        Args:
            place_url: URL del luogo Google Maps.
            max_reviews: Numero massimo di recensioni da estrarre.
            sort_by: newest | highest | lowest | relevant

        Returns:
            Lista di recensioni.
        """

        run_input = {
            "placeUrls": [place_url],
            "placeIds": [],
            "maxReviews": max_reviews,
            "sortBy": sort_by,
        }

        run = self.client.actor(self.ACTOR_ID).call(
            run_input=run_input
        )

        dataset_id = run.default_dataset_id

        return list(
            self.client.dataset(dataset_id).iterate_items()
        )

    def get_reviews(
        self,
        place_url: str,
        max_reviews: int = 100,
    ) -> List[Review]:

        raw_reviews = self.scrape(
            place_url=place_url,
            max_reviews=max_reviews,
        )

        return [Review.from_apify(item) for item in raw_reviews]