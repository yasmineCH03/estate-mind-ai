from django.contrib import admin
from .models import Listing


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = [
        "short_title",
        "source",
        "property_type",
        "transaction_type",
        "price",
        "governorate",
        "city",
        "status",
        "scraped_at",
    ]
    list_filter = [
        "source",
        "property_type",
        "transaction_type",
        "status",
        "governorate",
    ]
    search_fields = ["title", "description", "city", "address"]
    list_per_page = 25
    readonly_fields = ["scraped_at", "updated_at", "raw_extracted"]

    def short_title(self, obj):
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title
    short_title.short_description = "Title"