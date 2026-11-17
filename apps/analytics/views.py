from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import CompetitorMetrics, TrendAnalysis
from .serializers import CompetitorMetricsSerializer, TrendAnalysisSerializer


class CompetitorMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing competitor metrics."""
    serializer_class = CompetitorMetricsSerializer
    filterset_fields = ['competitor', 'metric_type', 'date']

    def get_queryset(self):
        return CompetitorMetrics.objects.filter(
            competitor__user=self.request.user, competitor__is_deleted=False
        ).select_related('competitor')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get metrics summary for all competitors."""
        # TODO: Implement metrics aggregation
        return Response({'message': 'Metrics summary to be implemented'})


class TrendAnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing trend analysis."""
    serializer_class = TrendAnalysisSerializer
    filterset_fields = ['competitor', 'trend_type', 'trend_direction']

    def get_queryset(self):
        return TrendAnalysis.objects.filter(
            competitor__user=self.request.user, competitor__is_deleted=False
        ).select_related('competitor')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest trends for all competitors."""
        # TODO: Implement latest trends retrieval
        return Response({'message': 'Latest trends to be implemented'})
