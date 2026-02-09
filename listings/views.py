from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from .models import Listing
from .serializers import ListingSerializer, ListingSummarySerializer


class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all().order_by('-scraped_at')
    filterset_fields = ['source', 'status', 'governorate', 'rooms']
    search_fields = ['title', 'address', 'description']
    ordering_fields = ['price', 'area_m2', 'scraped_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ListingSummarySerializer
        return ListingSerializer