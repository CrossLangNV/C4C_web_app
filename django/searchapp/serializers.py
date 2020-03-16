from rest_framework import serializers

from searchapp.models import Attachment, Document, Website


class WebsiteSerializer(serializers.ModelSerializer):
    documents = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Website
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    website = serializers.PrimaryKeyRelatedField(queryset=Website.objects.all())
    attachments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Document
        fields = '__all__'

class AttachmentSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = Attachment
        fields = '__all__'
