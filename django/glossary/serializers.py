from rest_framework import serializers

from glossary.models import Concept


class ConceptSerializer(serializers.ModelSerializer):
    documents = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Concept
        fields = '__all__'
