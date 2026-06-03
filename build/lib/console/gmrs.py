from dotenv import load_dotenv
load_dotenv()
import os

from scraper.GMRS import GoogleMapsReviewsScraper

def main():
    scraper = GoogleMapsReviewsScraper(os.getenv("APIFY_TOKEN"))

    reviews = scraper.get_reviews("https://www.google.com/maps/place/Clinica+Computer/@45.0829281,7.6565815,17z/data=!3m1!4b1!4m6!3m5!1s0x47886dc1c11851a3:0x16e95cb364d42178!8m2!3d45.0829281!4d7.6591564!16s%2Fg%2F11y4tfsb9z")

    print(reviews)

if __name__ == '__main__':
    main()