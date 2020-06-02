from rest_framework import serializers

from .models import ScrapingTask, ScrapingTaskItem


class ScrapingTaskItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingTaskItem
        fields = ['id', 'scheduler_id', 'status', 'date']


class ScrapingTaskSerializer(serializers.ModelSerializer):
    items = ScrapingTaskItemSerializer(many=True, read_only=True)

    class Meta:
        model = ScrapingTask
        fields = ['id', 'spider', 'spider_date_start', 'spider_date_end',
                  'spider_type', 'date', 'items']
