import os
import sys
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'estate_mind.settings')

import django
django.setup()

from listings.models import Listing
from agents.crawler import CrawlerAgent
from agents.bronze_storage import BronzeStorage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def save_to_bronze_and_db(results: list) -> dict:
    """
    Save crawled data following the architecture:
    1. Raw HTML → MinIO (Bronze layer) — immutable audit trail
    2. Listing metadata → PostgreSQL (Django ORM) — Silver layer
    """
    bronze = BronzeStorage()
    stats = {"bronze_saved": 0, "db_created": 0, "db_skipped": 0}

    for r in results:
        url = r["url"]

        # === BRONZE: Store raw HTML in MinIO ===
        minio_key = r.get("raw_html_key", "")
        raw_html = r.get("raw_html", "")

        if minio_key and raw_html:
            if not bronze.exists(minio_key):
                bronze.store_raw_html(minio_key, raw_html)
                stats["bronze_saved"] += 1

        # === SILVER: Save listing to Django DB ===
        if Listing.objects.filter(source_url=url).exists():
            stats["db_skipped"] += 1
            continue

        title = url.split("/")[-2].replace("-", " ").title()[:200]

        Listing(
            title=title,
            source=r["source"],
            source_url=url,
            raw_html_key=minio_key,
            description=r.get("markdown", "")[:5000],
            status="raw",
        ).save()
        stats["db_created"] += 1

    return stats


def main():
    print("\n" + "=" * 65)
    print("  🕷️  ESTATE MIND — CRAWLER AGENT")
    print("  Crawl4AI + Qwen3 8B | Bronze → MinIO | Silver → PostgreSQL")
    print("=" * 65 + "\n")

    agent = CrawlerAgent()

    results = agent.run(
        search_url="https://www.tayara.tn/ads/c/Immobilier",
        max_pages=500,
        max_listings=5000,
    )

    print(f"\n🕷️  Crawled: {len(results)} listings")

    # Save to MinIO (Bronze) + PostgreSQL (Silver)
    stats = save_to_bronze_and_db(results)

    print(f"\n📦 Bronze (MinIO):  {stats['bronze_saved']} raw HTML files stored")
    print(f"💾 Silver (DB):     {stats['db_created']} new | {stats['db_skipped']} skipped")
    print(f"📊 Total in DB:     {Listing.objects.count()}")

    print(f"\n👉 Django Admin:  http://localhost:8000/admin/listings/listing/")
    print(f"👉 REST API:      http://localhost:8000/api/listings/")
    print(f"👉 MinIO Console: http://localhost:9001 (minioadmin/minioadmin)")


if __name__ == "__main__":
    main()