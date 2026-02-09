from django.db import models


class Listing(models.Model):
    """A single real estate listing scraped from any source."""

    # ── Source Info ──
    source = models.CharField(max_length=50, help_text="e.g. tayara, mubawab")
    source_url = models.URLField(unique=True, help_text="Original listing URL")
    source_id = models.CharField(max_length=100, blank=True, null=True)

    # ── Property Details ──
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default="")
    property_type = models.CharField(
        max_length=30,
        choices=[
            ("apartment", "Appartement"),
            ("house", "Maison"),
            ("villa", "Villa"),
            ("studio", "Studio"),
            ("land", "Terrain"),
            ("commercial", "Commercial"),
            ("other", "Autre"),
        ],
        default="other",
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=[
            ("sale", "Vente"),
            ("rent", "Location"),
        ],
        default="sale",
    )

    # ── Price ──
    price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=5, default="TND")

    # ── Size & Rooms ──
    area_m2 = models.FloatField(blank=True, null=True, help_text="Surface in m²")
    rooms = models.IntegerField(blank=True, null=True)
    bedrooms = models.IntegerField(blank=True, null=True)
    bathrooms = models.IntegerField(blank=True, null=True)
    floor = models.IntegerField(blank=True, null=True)

    # ── Location ──
    governorate = models.CharField(max_length=50, blank=True, default="")
    delegation = models.CharField(max_length=100, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    address = models.CharField(max_length=300, blank=True, default="")
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    # ── Features ──
    features = models.JSONField(default=list, blank=True, help_text="e.g. ['climatisé', 'parking']")
    images = models.JSONField(default=list, blank=True, help_text="List of image URLs")

    # ── Pipeline Status ──
    STATUS_CHOICES = [
        ("bronze", "Bronze — Raw scraped"),
        ("silver", "Silver — Extracted & validated"),
        ("gold", "Gold — Enriched & geocoded"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="bronze")

    # ── Timestamps ──
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)

    # ── Raw Data ──
    raw_html_key = models.CharField(
        max_length=200, blank=True, default="",
        help_text="MinIO object key for raw HTML",
    )
    raw_extracted = models.JSONField(
        default=dict, blank=True,
        help_text="Raw LLM extraction output",
    )

    class Meta:
        ordering = ["-scraped_at"]
        indexes = [
            models.Index(fields=["source"]),
            models.Index(fields=["status"]),
            models.Index(fields=["governorate"]),
            models.Index(fields=["property_type"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["price"]),
        ]

    def __str__(self):
        return f"[{self.source}] {self.title[:60]} — {self.price} {self.currency}"