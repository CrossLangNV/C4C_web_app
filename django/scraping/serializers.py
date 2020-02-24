from rest_framework import serializers

from .models import ScrapingTaskItem, ScrapingTask


class ScrapingTaskItemSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=ScrapingTask.objects.all())

    class Meta:
        model = ScrapingTaskItem
        fields = ['id', 'task', 'data', 'date']


class ScrapingTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapingTask
        fields = ['id', 'spider', 'date']
