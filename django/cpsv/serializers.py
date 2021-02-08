from rest_framework import serializers

from cpsv.models import PublicService


class PublicServiceObligationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PublicService
        fields = '__all__'