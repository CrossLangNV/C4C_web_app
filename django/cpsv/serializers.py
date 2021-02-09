from rest_framework import serializers

from cpsv.models import PublicService, ContactPoint


class PublicServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = PublicService
        fields = '__all__'


class ContactPointSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContactPoint
        fields = '__all__'
