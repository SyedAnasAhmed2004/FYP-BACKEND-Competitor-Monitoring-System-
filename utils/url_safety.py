"""
SSRF protection helpers.

Competitor URLs are supplied by users and then fetched by this server (an HTTP
HEAD check and a headless Playwright browser). Without checks, a user could
point those fetches at localhost, the internal network or a cloud metadata
service and read the response back through the scraped HTML.

Rules enforced here:
  * only http and https
  * no credentials embedded in the URL
  * every address the hostname resolves to must be a public (global) address
  * redirects are followed manually and every hop is checked again
"""
import ipaddress
import logging
import socket
from urllib.parse import urljoin, urlparse

import requests

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = ('http', 'https')
# Browser-internal schemes that never touch the network.
_LOCAL_BROWSER_SCHEMES = ('data', 'blob', 'about')
MAX_REDIRECTS = 5


class UnsafeURLError(ValueError):
    """The URL is not allowed to be fetched by the server."""


class UnresolvableHostError(UnsafeURLError):
    """The hostname does not resolve in DNS."""


def _is_public_ip(ip_text):
    ip = ipaddress.ip_address(ip_text)
    # An IPv4 address wrapped in IPv6 (::ffff:127.0.0.1) must be judged as IPv4.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    return ip.is_global and not ip.is_multicast


def assert_public_url(url):
    """
    Raise UnsafeURLError unless `url` is an http(s) URL whose host resolves
    only to public IP addresses. Raises UnresolvableHostError when DNS fails.
    """
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise UnsafeURLError('Malformed URL') from exc

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsafeURLError('Only http and https URLs are allowed')
    if parsed.username or parsed.password:
        raise UnsafeURLError('URLs with embedded credentials are not allowed')

    host = parsed.hostname
    if not host:
        raise UnsafeURLError('URL has no host')

    try:
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnresolvableHostError(f'Domain does not exist: {host}') from exc
    except ValueError as exc:
        raise UnsafeURLError('Invalid port in URL') from exc

    if not infos:
        raise UnresolvableHostError(f'Domain does not exist: {host}')

    for info in infos:
        ip_text = info[4][0].split('%')[0]  # drop IPv6 zone id
        if not _is_public_ip(ip_text):
            raise UnsafeURLError('URL points to a private or reserved address')


def is_public_url(url):
    """Boolean form of assert_public_url."""
    try:
        assert_public_url(url)
        return True
    except UnsafeURLError:
        return False


def safe_head(url, headers=None, timeout=10, max_redirects=MAX_REDIRECTS):
    """
    requests.head() that validates the URL and every redirect target.
    Raises UnsafeURLError for disallowed targets and
    requests.exceptions.TooManyRedirects for redirect loops.
    """
    current = url
    for _ in range(max_redirects + 1):
        assert_public_url(current)
        response = requests.head(
            current, headers=headers, timeout=timeout, allow_redirects=False
        )
        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get('Location')
            if not location:
                return response
            current = urljoin(current, location)
            continue
        return response
    raise requests.exceptions.TooManyRedirects(f'Exceeded {max_redirects} redirects')


def install_playwright_guard(context):
    """
    Make a Playwright browser context refuse any request (page, redirect or
    sub-resource) that targets a non-public address.
    """
    verdicts = {}  # host -> bool, avoids a DNS lookup for every sub-resource

    def handler(route):
        request_url = route.request.url
        scheme = urlparse(request_url).scheme
        if scheme in _LOCAL_BROWSER_SCHEMES:
            route.continue_()
            return

        host = urlparse(request_url).hostname or ''
        allowed = verdicts.get(host)
        if allowed is None:
            allowed = is_public_url(request_url)
            verdicts[host] = allowed

        if allowed:
            route.continue_()
        else:
            logger.warning('Blocked non-public browser request to %s', host)
            route.abort('blockedbyclient')

    context.route('**/*', handler)
