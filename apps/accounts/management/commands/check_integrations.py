"""
Check that the third-party API keys in .env are present and actually accepted.

    python manage.py check_integrations
    python manage.py check_integrations --offline   (only checks that values are set)
    python manage.py check_integrations --strict     (exit code 1 if a required key is not OK)

Live checks use free, read-only endpoints and never spend credits. Key values
are never printed.
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand

PLACEHOLDER_HINTS = ('your-', 'your_', 'api key', 'change-this', 'xxxx', '<')


def _is_set(value):
    value = (value or '').strip()
    return bool(value) and not any(hint in value.lower() for hint in PLACEHOLDER_HINTS)


def _bearer_check(url, key, ok_when=None):
    """GET `url` with a bearer token. Returns (status, detail)."""
    try:
        response = requests.get(url, headers={'Authorization': f'Bearer {key}'}, timeout=15)
    except requests.exceptions.RequestException as exc:
        return 'UNREACHABLE', exc.__class__.__name__
    if response.status_code in (401, 403):
        return 'INVALID', f'HTTP {response.status_code}, key was rejected'
    if response.status_code != 200:
        return 'UNKNOWN', f'HTTP {response.status_code}'
    if ok_when:
        try:
            problem = ok_when(response.json())
        except ValueError:
            problem = 'unexpected response'
        if problem:
            return 'LIMITED', problem
    return 'OK', ''


def _sendgrid_scopes(body):
    scopes = body.get('scopes', [])
    return None if 'mail.send' in scopes else 'key is valid but lacks the "Mail Send" permission'


# name, setting/env name, required?, what it powers, live check (or None)
INTEGRATIONS = [
    ('Firecrawl', 'FIRECRAWL_API_KEY', True, 'website link discovery', None),
    ('Apify', 'APIFY_API_TOKEN', True, 'LinkedIn, Facebook and Instagram scrapers',
     lambda k: _bearer_check('https://api.apify.com/v2/users/me', k)),
    ('OpenRouter', 'OPENROUTER_API_KEY', True, 'AI summaries, reports and agents',
     lambda k: _bearer_check('https://openrouter.ai/api/v1/auth/key', k)),
    ('OpenAI', 'OPENAI_API_KEY', False, 'embeddings and fallback LLM',
     lambda k: _bearer_check('https://api.openai.com/v1/models', k)),
    ('SendGrid', 'SENDGRID_API_KEY', True, 'email alerts',
     lambda k: _bearer_check('https://api.sendgrid.com/v3/scopes', k, _sendgrid_scopes)),
    ('Financial Modeling Prep', 'FMP_API_KEY', False, 'financial dashboard', None),
]


class Command(BaseCommand):
    help = 'Verify third-party API keys are set and accepted (no credits are spent).'

    def add_arguments(self, parser):
        parser.add_argument('--offline', action='store_true', help='Only check that values are set.')
        parser.add_argument('--strict', action='store_true', help='Exit with code 1 if a required key is not OK.')

    def handle(self, *args, **options):
        import os
        failures = 0
        self.stdout.write(f'{"service":<26}{"status":<12}{"needed":<10}powers / detail')
        for name, env_name, required, purpose, live in INTEGRATIONS:
            value = getattr(settings, env_name, None) or os.getenv(env_name, '')
            if not _is_set(value):
                status, detail = 'MISSING', purpose
            elif options['offline'] or live is None:
                status, detail = ('SET', purpose + ' (not live-tested)')
            else:
                status, detail = live(value.strip())
                detail = purpose + (f' ({detail})' if detail else '')

            good = status in ('OK', 'SET')
            if required and not good:
                failures += 1
            line = f'{name:<26}{status:<12}{"required" if required else "optional":<10}{detail}'
            style = self.style.SUCCESS if good else (self.style.ERROR if required else self.style.WARNING)
            self.stdout.write(style(line))

        sender = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
        self.stdout.write(f'\nEmail sender in use: {sender}')
        self.stdout.write('It must be a verified sender or domain in SendGrid, otherwise emails are rejected.')

        if failures:
            self.stdout.write(self.style.ERROR(f'\n{failures} required integration(s) not ready.'))
            if options['strict']:
                raise SystemExit(1)
        else:
            self.stdout.write(self.style.SUCCESS('\nAll required integrations are ready.'))
