from django.utils import formats
from rest_framework import serializers

from .models import ScrapingTaskItem, ScrapingTask


class ScrapingTaskSerializer(serializers.ModelSerializer):
    items = serializers.RelatedField(many=True, read_only=True)

    class Meta:
        model = ScrapingTask
        fields = ['id', 'spider', 'date']


class ScrapingTaskItemSerializer(serializers.ModelSerializer):
    date_django = serializers.SerializerMethodField()
    task = serializers.PrimaryKeyRelatedField(queryset=ScrapingTask.objects.all())

    class Meta:
        model = ScrapingTaskItem
        fields = ['id', 'task', 'data', 'date', 'date_django']

    def get_date_django(self, obj):
        return formats.date_format(obj.date, 'DATETIME_FORMAT')
