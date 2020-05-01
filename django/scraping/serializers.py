from rest_framework import serializers

from .models import ScrapingTask


class ScrapingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingTask
        fields = ['id', 'scheduler_id', 'spider',
                  'spider_type', 'status', 'date']
