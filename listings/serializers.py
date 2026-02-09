from rest_framework import serializers
from .models import Listing


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__'


class ListingSummarySerializer(serializers.ModelSerializer):
    """Lighter serializer for list views"""
    class Meta:
        model = Listing
        fields = [
            'id', 'title', 'source', 'source_url',
            'price', 'rooms', 'area_m2',
            'governorate', 'status', 'scraped_at',
        ]