from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ScrapingConfig, ScrapingLog
from .serializers import ScrapingConfigSerializer, ScrapingLogSerializer


class ScrapingConfigViewSet(viewsets.ModelViewSet):
    """ViewSet for scraping configurations (scoped to the current user's competitors)."""
    serializer_class = ScrapingConfigSerializer
    filterset_fields = ['competitor', 'is_active']

    def get_queryset(self):
        return ScrapingConfig.objects.filter(
            competitor__user=self.request.user,
            competitor__is_deleted=False,
        ).select_related('competitor')

    @action(detail=True, methods=['post'])
    def trigger_scraping(self, request, pk=None):
        """Manually trigger scraping for this config."""
        config = self.get_object()
        # Trigger scraping task (will be implemented with Celery)
        return Response({'status': 'Scraping triggered', 'config_id': config.id})


class ScrapingLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing scraping logs (scoped to the current user's competitors)."""
    serializer_class = ScrapingLogSerializer
    filterset_fields = ['config', 'status']

    def get_queryset(self):
        return ScrapingLog.objects.filter(
            config__competitor__user=self.request.user,
            config__competitor__is_deleted=False,
        ).select_related('config__competitor')
