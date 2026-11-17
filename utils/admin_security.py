"""
IP allowlist for the Django admin site.

Settings (all read from the environment in config/settings.py):
  ADMIN_URL                    path of the admin site, default "admin/"
  ADMIN_ALLOWED_IPS            comma separated IPs or CIDR ranges that may reach it,
                               default "127.0.0.1,::1" (this machine only)
  ADMIN_TRUSTED_PROXY_COUNT    number of reverse proxies in front of Django
                               (0 = none, use the socket address)

Requests from anywhere else get a plain 404, so the admin does not even
advertise that it exists on that address.

Behind a proxy such as Nginx, Django's socket address is the proxy, not the
visitor. Set ADMIN_TRUSTED_PROXY_COUNT=1 and make the proxy OVERWRITE
X-Forwarded-For with the real client address (proxy_set_header
X-Forwarded-For $remote_addr;). Only then is the header trustworthy.
"""
import ipaddress
import logging

from django.conf import settings
from django.http import HttpResponseNotFound

logger = logging.getLogger(__name__)


def _parse_networks(values):
    networks = []
    for raw in values:
        raw = raw.strip()
        if not raw:
            continue
        try:
            networks.append(ipaddress.ip_network(raw, strict=False))
        except ValueError:
            logger.error('ADMIN_ALLOWED_IPS contains an invalid entry and it was ignored: %r', raw)
    return networks


def client_ip(request, trusted_proxy_count=0):
    """
    Address of the visitor. With N trusted proxies, the visitor is the Nth entry
    counted from the right of X-Forwarded-For (earlier entries are client-supplied
    and can be forged). Returns None when it cannot be determined.
    """
    if trusted_proxy_count > 0:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        hops = [h.strip() for h in forwarded.split(',') if h.strip()]
        if len(hops) < trusted_proxy_count:
            return None
        candidate = hops[-trusted_proxy_count]
    else:
        candidate = request.META.get('REMOTE_ADDR', '')
    try:
        ip = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip


class AdminIPAllowlistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = '/' + settings.ADMIN_URL.lstrip('/')
        self.networks = _parse_networks(settings.ADMIN_ALLOWED_IPS)
        self.proxy_count = int(getattr(settings, 'ADMIN_TRUSTED_PROXY_COUNT', 0))

    def __call__(self, request):
        if request.path.startswith(self.admin_prefix):
            ip = client_ip(request, self.proxy_count)
            allowed = ip is not None and any(ip in net for net in self.networks)
            if not allowed:
                logger.warning('Blocked admin access from %s', ip or 'unknown address')
                return HttpResponseNotFound('Not found')
        return self.get_response(request)
