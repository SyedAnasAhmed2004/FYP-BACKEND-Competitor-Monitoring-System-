"""
Custom exception classes for the application.
"""


class ScrapingError(Exception):
    """Exception raised for scraping-related errors."""
    pass


class EmbeddingError(Exception):
    """Exception raised for embedding generation errors."""
    pass


class MilvusConnectionError(Exception):
    """Exception raised for Milvus connection errors."""
    pass


class DataProcessingError(Exception):
    """Exception raised for data processing errors."""
    pass


class AnalyticsError(Exception):
    """Exception raised for analytics calculation errors."""
    pass


# ---------------------------------------------------------------------------
# DRF exception handler
# ---------------------------------------------------------------------------
import logging
import uuid

from django.db import DatabaseError, InterfaceError, OperationalError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

_logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Keep DRF's normal responses for errors it already understands
    (validation, auth, permission, 404, throttling) so the API shape the
    frontend relies on does not change.

    Everything else is an unexpected failure. It is logged in full on the
    server and the client gets a generic message plus an error id that can be
    matched against the log. Exception text never reaches the client.
    """
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    error_id = uuid.uuid4().hex[:8]
    view = context.get('view')
    view_name = view.__class__.__name__ if view else 'unknown'

    if isinstance(exc, (OperationalError, InterfaceError)):
        _logger.error('[%s] Database unavailable in %s: %s', error_id, view_name, exc)
        return Response(
            {'error': 'The service is temporarily unavailable. Please try again shortly.',
             'error_id': error_id},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if isinstance(exc, DatabaseError):
        _logger.exception('[%s] Database error in %s', error_id, view_name)
    else:
        _logger.exception('[%s] Unhandled error in %s', error_id, view_name)

    return Response(
        {'error': 'An unexpected error occurred.', 'error_id': error_id},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


_CONNECTION_HINTS = ('could not connect', 'connection refused', 'connection error', 'timed out', 'max retries')


def is_service_unavailable(exc):
    """True when the failure looks like a backing service (Chroma, Redis, API) being down."""
    import requests
    if isinstance(exc, (ConnectionError, TimeoutError, OperationalError, InterfaceError,
                        requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    text = str(exc).lower()
    return any(hint in text for hint in _CONNECTION_HINTS)


def error_response_from_exception(exc, action, *, logger=None, extra=None):
    """
    Log `exc` with a traceback and build a safe API response for it.

    `action` is a short phrase such as "fetching statistics". The client sees a
    generic message and an error id, never the exception text.
    503 is used when a backing service is unreachable, 500 otherwise.
    """
    error_id = uuid.uuid4().hex[:8]
    log = logger or _logger
    log.error('[%s] Error %s: %s', error_id, action, exc, exc_info=True)

    if is_service_unavailable(exc):
        body = {'error': f'Error {action}: a required service is temporarily unavailable. '
                         'Please try again shortly.',
                'error_id': error_id}
        code = status.HTTP_503_SERVICE_UNAVAILABLE
    else:
        body = {'error': f'Error {action}. Please try again later.', 'error_id': error_id}
        code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if extra:
        body.update(extra)
    return Response(body, status=code)
