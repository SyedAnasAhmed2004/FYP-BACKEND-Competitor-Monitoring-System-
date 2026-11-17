from rest_framework import serializers

from utils.url_safety import UnsafeURLError, assert_public_url
from .models import ScrapingConfig, ScrapingLog


class ScrapingConfigSerializer(serializers.ModelSerializer):
    competitor_name = serializers.CharField(source='competitor.name', read_only=True)

    class Meta:
        model = ScrapingConfig
        fields = '__all__'

    def validate_competitor(self, competitor):
        """A user may only attach configs to their own, non-deleted competitors."""
        request = self.context.get('request')
        if (
            request is None
            or competitor.user_id != request.user.id
            or competitor.is_deleted
        ):
            raise serializers.ValidationError('Competitor not found.')
        return competitor

    def validate_target_url(self, value):
        """Block URLs that would make the server fetch internal addresses."""
        try:
            assert_public_url(value)
        except UnsafeURLError as exc:
            # DNS failures are tolerated here; only reject disallowed targets.
            if exc.__class__.__name__ != 'UnresolvableHostError':
                raise serializers.ValidationError(
                    'target_url must be a public http(s) address.'
                )
        return value


class ScrapingLogSerializer(serializers.ModelSerializer):
    competitor_name = serializers.CharField(source='config.competitor.name', read_only=True)

    class Meta:
        model = ScrapingLog
        fields = '__all__'
