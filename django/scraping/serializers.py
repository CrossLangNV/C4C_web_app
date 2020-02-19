from django.utils import formats
from rest_framework import serializers

from .models import ScrapyItem


class ScrapyItemSerializer(serializers.ModelSerializer):
    date_django = serializers.SerializerMethodField()

    class Meta:
        model = ScrapyItem
        fields = ['unique_id', 'data', 'date', 'date_django']

    def get_date_django(self, obj):
        return formats.date_format(obj.date, 'DATETIME_FORMAT')
