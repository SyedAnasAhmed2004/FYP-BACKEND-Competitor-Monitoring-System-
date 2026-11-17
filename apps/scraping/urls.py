from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScrapingConfigViewSet, ScrapingLogViewSet

router = DefaultRouter()
router.register(r'configs', ScrapingConfigViewSet, basename='scrapingconfig')
router.register(r'logs', ScrapingLogViewSet, basename='scrapinglog')

urlpatterns = [
    path('', include(router.urls)),
]
