from rest_framework import serializers

from searchapp.models import Attachment, Document, Website


class WebsiteSerializer(serializers.ModelSerializer):
    documents = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Website
        fields = ['id', 'name', 'url', 'content', 'documents']


class DocumentSerializer(serializers.ModelSerializer):
    website = serializers.PrimaryKeyRelatedField(queryset=Website.objects.all())
    attachments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'title', 'date', 'acceptance_state', 'url', 'summary', 'content', 'website', 'attachments']


class AttachmentSerializer(serializers.ModelSerializer):
    document = serializers.PrimaryKeyRelatedField(queryset=Document.objects.all())

    class Meta:
        model = Attachment
        fields = ['id', 'file', 'url', 'document']