"""JSON handlers for 404/500 raised outside DRF views (bad URL, middleware crash)."""
import logging
import uuid

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def not_found(request, exception=None):
    return JsonResponse({'error': 'The requested resource was not found.'}, status=404)


def server_error(request):
    error_id = uuid.uuid4().hex[:8]
    logger.error('[%s] Unhandled server error for %s %s', error_id, request.method, request.path)
    return JsonResponse(
        {'error': 'An unexpected error occurred.', 'error_id': error_id}, status=500
    )
