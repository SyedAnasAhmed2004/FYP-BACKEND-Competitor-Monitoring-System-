from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompetitorMetricsViewSet, TrendAnalysisViewSet

router = DefaultRouter()
router.register(r'metrics', CompetitorMetricsViewSet, basename='competitormetrics')
router.register(r'trends', TrendAnalysisViewSet, basename='trendanalysis')

urlpatterns = [
    path('', include(router.urls)),
]
