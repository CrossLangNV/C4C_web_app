from rest_framework import serializers

from searchapp.models import Attachment, Document


class AttachmentSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = Attachment
        fields = ['file', 'url', 'document']