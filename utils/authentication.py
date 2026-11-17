"""
Token authentication with an expiry.

DRF's stock tokens never expire, so a leaked token works forever. Tokens here
are valid for settings.TOKEN_TTL_DAYS days from creation; after that the
holder has to log in again.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token


def _ttl():
    return timedelta(days=getattr(settings, 'TOKEN_TTL_DAYS', 14))


def token_is_expired(token):
    return token.created + _ttl() < timezone.now()


class ExpiringTokenAuthentication(TokenAuthentication):
    """TokenAuthentication that rejects (and deletes) expired tokens."""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if token_is_expired(token):
            token.delete()
            raise exceptions.AuthenticationFailed('Token has expired. Please log in again.')
        return user, token


def get_fresh_token(user):
    """Return the user's token, replacing it if it has expired."""
    token, _ = Token.objects.get_or_create(user=user)
    if token_is_expired(token):
        token.delete()
        token = Token.objects.create(user=user)
    return token


def get_valid_token(key):
    """
    Look a token key up for code paths that bypass DRF authentication
    (e.g. the SSE streaming view). Returns the Token, or None if the key is
    unknown, expired or belongs to an inactive user.
    """
    try:
        token = Token.objects.select_related('user').get(key=key)
    except Token.DoesNotExist:
        return None
    if token_is_expired(token):
        token.delete()
        return None
    if not token.user.is_active:
        return None
    return token
